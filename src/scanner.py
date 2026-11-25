#!/usr/bin/env python3
"""Standard 8mm Telecine Film Scanner Controller.

Drives a 28BYJ-48 stepper motor (via ULN2003 on Raspberry Pi GPIO) and captures
12-bit RAW/DNG frames from a Raspberry Pi HQ Camera (IMX477) using picamera2
and OpenCV sprocket-hole alignment.

Run with --dry-run to test the alignment state machine without Raspberry Pi
hardware, or --calibrate to tune the sprocket ROI and focus live.
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol

try:
    import cv2
    import numpy as np
except ImportError:  # pragma: no cover - handled gracefully at runtime
    cv2 = None  # type: ignore[assignment]
    np = None  # type: ignore[assignment]

try:
    from gpiozero import OutputDevice
except ImportError:  # pragma: no cover - not present off-Pi
    OutputDevice = None  # type: ignore[assignment]

try:
    from picamera2 import Picamera2
except ImportError:  # pragma: no cover - not present off-Pi
    Picamera2 = None  # type: ignore[assignment]


LOGGER = logging.getLogger("telecine.scanner")

# 8-phase half-step sequence for 28BYJ-48 (~4096 half-steps per revolution)
HALF_STEP_SEQUENCE: tuple[tuple[int, int, int, int], ...] = (
    (1, 0, 0, 0),
    (1, 1, 0, 0),
    (0, 1, 0, 0),
    (0, 1, 1, 0),
    (0, 0, 1, 0),
    (0, 0, 1, 1),
    (0, 0, 0, 1),
    (1, 0, 0, 1),
)


@dataclass
class ScannerConfig:
    """Configuration for the 8mm telecine capture session."""

    output_dir: Path = Path("./captures")
    gpio_pins: tuple[int, int, int, int] = (17, 27, 22, 23)
    step_delay_s: float = 0.002
    reverse_direction: bool = False
    release_coils_on_capture: bool = True
    settle_delay_s: float = 0.35

    # Preview stream & sprocket-hole ROI (x, y, width, height) in preview pixels
    preview_size: tuple[int, int] = (640, 480)
    roi: tuple[int, int, int, int] = (40, 80, 140, 320)
    target_y: float = 160.0  # Desired sprocket centroid Y inside the ROI
    tolerance_px: float = 3.0

    # OpenCV bright-region detection parameters for the backlit sprocket hole
    threshold: int = 220
    min_area: float = 300.0
    max_area: float = 18000.0
    min_aspect: float = 0.35
    max_aspect: float = 2.8

    # Motion state-machine parameters (in half-steps)
    coarse_steps: int = 8
    fine_steps: int = 1
    fine_zone_px: float = 20.0
    advance_past_steps: int = 45
    max_steps_per_frame: int = 1200
    max_frames: int = 0  # 0 = run until end-of-reel or Ctrl+C

    # Locked manual camera settings (5600K high-CRI LED backlight)
    exposure_us: int = 12000
    analogue_gain: float = 1.0
    wb_gains: tuple[float, float] = (1.8, 1.5)
    save_preview_jpg: bool = False

    # Modes
    calibrate_only: bool = False
    show_debug_window: bool = False
    dry_run: bool = False


class StepperDriver(Protocol):
    """Minimal stepper motor interface."""

    def step(self, steps: int) -> None: ...
    def release(self) -> None: ...
    def close(self) -> None: ...


class ULN2003Stepper:
    """Half-step 28BYJ-48 driver using gpiozero (Pi 4 & Pi 5 compatible)."""

    def __init__(
        self,
        pins: tuple[int, int, int, int],
        step_delay_s: float = 0.002,
        reverse: bool = False,
    ) -> None:
        if OutputDevice is None:
            raise RuntimeError(
                "gpiozero is not installed. Install python3-gpiozero (and python3-lgpio on Pi 5) "
                "or run with --dry-run."
            )
        self._pins = [OutputDevice(pin, initial_value=False) for pin in pins]
        self._step_delay_s = step_delay_s
        self._reverse = reverse
        self._phase_index = 0
        self.total_steps = 0

    def step(self, steps: int) -> None:
        if steps == 0:
            return
        direction = 1 if steps > 0 else -1
        if self._reverse:
            direction = -direction

        for _ in range(abs(steps)):
            self._phase_index = (self._phase_index + direction) % len(HALF_STEP_SEQUENCE)
            pattern = HALF_STEP_SEQUENCE[self._phase_index]
            for device, value in zip(self._pins, pattern):
                device.value = value
            self.total_steps += 1 if steps > 0 else -1
            time.sleep(self._step_delay_s)

    def release(self) -> None:
        """De-energize all coils to prevent heating and holding-torque vibration."""
        for device in self._pins:
            device.off()

    def close(self) -> None:
        self.release()
        for device in self._pins:
            device.close()


class MockStepper:
    """Simulated stepper driver for --dry-run testing."""

    def __init__(self) -> None:
        self.position_steps = 0

    def step(self, steps: int) -> None:
        self.position_steps += steps

    def release(self) -> None:
        pass

    def close(self) -> None:
        pass


@dataclass
class SprocketDetection:
    """Result of sprocket-hole detection inside the configured ROI."""

    found: bool
    cx: float = 0.0
    cy: float = 0.0
    area: float = 0.0
    bbox: tuple[int, int, int, int] = (0, 0, 0, 0)
    error_y: float = 0.0


class SprocketDetector:
    """Detects a backlit Standard 8mm sprocket hole in a preview frame ROI."""

    def __init__(self, config: ScannerConfig) -> None:
        if cv2 is None or np is None:
            raise RuntimeError(
                "OpenCV (cv2) and numpy are required. Install python3-opencv."
            )
        self.config = config
        self._morph_kernel = np.ones((3, 3), dtype=np.uint8)

    def detect(self, frame_rgb: "np.ndarray") -> SprocketDetection:
        x, y, w, h = self.config.roi
        roi_img = frame_rgb[y : y + h, x : x + w]
        if roi_img.size == 0:
            return SprocketDetection(found=False)

        if roi_img.ndim == 3:
            gray = cv2.cvtColor(roi_img, cv2.COLOR_RGB2GRAY)
        else:
            gray = roi_img

        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, binary = cv2.threshold(
            blurred, self.config.threshold, 255, cv2.THRESH_BINARY
        )
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, self._morph_kernel)

        contours, _ = cv2.findContours(
            cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        best: Optional[SprocketDetection] = None
        best_dist = float("inf")

        for contour in contours:
            area = float(cv2.contourArea(contour))
            if not (self.config.min_area <= area <= self.config.max_area):
                continue

            bx, by, bw, bh = cv2.boundingRect(contour)
            if bh == 0:
                continue
            aspect = bw / float(bh)
            if not (self.config.min_aspect <= aspect <= self.config.max_aspect):
                continue

            moments = cv2.moments(contour)
            if moments["m00"] <= 0:
                continue

            cx = moments["m10"] / moments["m00"]
            cy = moments["m01"] / moments["m00"]
            error_y = cy - self.config.target_y
            dist = abs(error_y)

            if dist < best_dist:
                best_dist = dist
                best = SprocketDetection(
                    found=True,
                    cx=cx,
                    cy=cy,
                    area=area,
                    bbox=(bx, by, bw, bh),
                    error_y=error_y,
                )

        return best if best is not None else SprocketDetection(found=False)

    def draw_overlay(
        self, frame_rgb: "np.ndarray", detection: SprocketDetection
    ) -> "np.ndarray":
        """Render ROI, target alignment line, and sprocket detection overlay."""
        vis = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        rx, ry, rw, rh = self.config.roi

        # ROI boundary
        cv2.rectangle(vis, (rx, ry), (rx + rw, ry + rh), (255, 200, 0), 2)

        # Target Y line and tolerance band
        ty = int(round(ry + self.config.target_y))
        tol = int(round(self.config.tolerance_px))
        cv2.line(vis, (rx, ty), (rx + rw, ty), (0, 255, 0), 1)
        cv2.line(vis, (rx, ty - tol), (rx + rw, ty - tol), (0, 180, 0), 1)
        cv2.line(vis, (rx, ty + tol), (rx + rw, ty + tol), (0, 180, 0), 1)

        if detection.found:
            bx, by, bw, bh = detection.bbox
            cv2.rectangle(
                vis,
                (rx + bx, ry + by),
                (rx + bx + bw, ry + by + bh),
                (0, 0, 255),
                2,
            )
            cx_abs = int(round(rx + detection.cx))
            cy_abs = int(round(ry + detection.cy))
            cv2.circle(vis, (cx_abs, cy_abs), 4, (0, 255, 255), -1)
            label = f"LOCK err={detection.error_y:+.1f}px area={detection.area:.0f}"
        else:
            label = "SEARCHING..."

        cv2.putText(
            vis,
            label,
            (10, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0) if detection.found else (0, 165, 255),
            2,
        )
        return vis


class CameraDriver(Protocol):
    """Minimal camera interface for live preview and DNG capture."""

    def start(self) -> None: ...
    def stop(self) -> None: ...
    def get_preview_frame(self) -> "np.ndarray": ...
    def capture_dng(self, dng_path: Path, jpg_path: Optional[Path] = None) -> None: ...


class TelecineCamera:
    """Raspberry Pi HQ Camera (IMX477) controller using picamera2."""

    def __init__(self, config: ScannerConfig) -> None:
        if Picamera2 is None:
            raise RuntimeError(
                "picamera2 is not installed. Install python3-picamera2 on Raspberry Pi OS "
                "or run with --dry-run."
            )
        self.config = config
        self._picam2 = Picamera2()

    def start(self) -> None:
        # Configure full-resolution 12-bit RAW + fast RGB preview stream
        still_config = self._picam2.create_still_configuration(
            main={"size": (4056, 3040), "format": "RGB888"},
            lores={"size": self.config.preview_size, "format": "RGB888"},
            raw={"size": (4056, 3040), "format": "SRGGB12"},
            buffer_count=2,
        )
        self._picam2.configure(still_config)
        self._picam2.start()

        # Lock manual exposure, analogue gain, and white balance to prevent flicker
        self._picam2.set_controls(
            {
                "AeEnable": False,
                "AwbEnable": False,
                "ExposureTime": self.config.exposure_us,
                "AnalogueGain": self.config.analogue_gain,
                "ColourGains": self.config.wb_gains,
            }
        )
        # Allow sensor controls to settle for a few frames
        time.sleep(0.5)
        LOGGER.info(
            "HQ Camera started (exposure=%dus, gain=%.2f, wb=%s)",
            self.config.exposure_us,
            self.config.analogue_gain,
            self.config.wb_gains,
        )

    def get_preview_frame(self) -> "np.ndarray":
        return self._picam2.capture_array("lores")

    def capture_dng(self, dng_path: Path, jpg_path: Optional[Path] = None) -> None:
        request = self._picam2.capture_request()
        try:
            request.save_dng(str(dng_path))
            if jpg_path is not None:
                request.save("main", str(jpg_path))
        finally:
            request.release()

    def stop(self) -> None:
        self._picam2.stop()
        self._picam2.close()


class MockCamera:
    """Synthetic camera for --dry-run testing without Raspberry Pi hardware."""

    def __init__(self, config: ScannerConfig, stepper: MockStepper) -> None:
        if np is None or cv2 is None:
            raise RuntimeError("OpenCV (cv2) and numpy are required even in --dry-run mode.")
        self.config = config
        self._stepper = stepper
        # Simulate one Standard 8mm frame pitch every 160 half-steps
        self._steps_per_frame = 160

    def start(self) -> None:
        LOGGER.info("MockCamera started (dry-run mode, pitch=%d steps/frame)", self._steps_per_frame)

    def get_preview_frame(self) -> "np.ndarray":
        w, h = self.config.preview_size
        frame = np.full((h, w, 3), 25, dtype=np.uint8)

        rx, ry, rw, rh = self.config.roi
        # Map stepper position to a repeating sprocket hole moving downward through the ROI
        phase = (self._stepper.position_steps % self._steps_per_frame) / float(self._steps_per_frame)
        hole_cy = int(ry + phase * rh)
        hole_cx = rx + rw // 2
        hole_w, hole_h = 34, 26

        x1 = max(0, hole_cx - hole_w // 2)
        y1 = max(0, hole_cy - hole_h // 2)
        x2 = min(w - 1, hole_cx + hole_w // 2)
        y2 = min(h - 1, hole_cy + hole_h // 2)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), -1)
        return frame

    def capture_dng(self, dng_path: Path, jpg_path: Optional[Path] = None) -> None:
        dng_path.write_text(
            f"MOCK_DNG step={self._stepper.position_steps}\n", encoding="utf-8"
        )
        if jpg_path is not None:
            frame = self.get_preview_frame()
            cv2.imwrite(str(jpg_path), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

    def stop(self) -> None:
        LOGGER.info("MockCamera stopped.")


class TelecineScanner:
    """Orchestrates film advance, sprocket alignment, damping, and DNG capture."""

    def __init__(
        self,
        config: ScannerConfig,
        stepper: StepperDriver,
        camera: CameraDriver,
        detector: SprocketDetector,
    ) -> None:
        self.config = config
        self.stepper = stepper
        self.camera = camera
        self.detector = detector
        self._stop_requested = False

    def request_stop(self) -> None:
        self._stop_requested = True

    def run_calibration(self) -> None:
        """Live preview loop for positioning ROI, focus, and exposure."""
        LOGGER.info("Calibration mode active. Press 'q' in preview window or Ctrl+C to exit.")
        self.camera.start()
        try:
            while not self._stop_requested:
                frame = self.camera.get_preview_frame()
                det = self.detector.detect(frame)
                if self.config.show_debug_window:
                    vis = self.detector.draw_overlay(frame, det)
                    cv2.imshow("8mm Telecine Calibration", vis)
                    if (cv2.waitKey(30) & 0xFF) == ord("q"):
                        break
                else:
                    LOGGER.info(
                        "found=%s cy=%.1f error_y=%+.1f area=%.0f",
                        det.found,
                        det.cy,
                        det.error_y,
                        det.area,
                    )
                    time.sleep(0.25)
        finally:
            if self.config.show_debug_window:
                cv2.destroyAllWindows()
            self.camera.stop()
            self.stepper.close()

    def _align_next_frame(self) -> bool:
        """Advance film until a sprocket hole centers within tolerance_px of target_y."""
        steps_taken = 0

        while not self._stop_requested:
            frame = self.camera.get_preview_frame()
            det = self.detector.detect(frame)

            if self.config.show_debug_window:
                vis = self.detector.draw_overlay(frame, det)
                cv2.imshow("8mm Telecine Live", vis)
                if (cv2.waitKey(1) & 0xFF) == ord("q"):
                    self.request_stop()
                    return False

            if det.found and abs(det.error_y) <= self.config.tolerance_px:
                LOGGER.debug(
                    "Sprocket aligned after %d steps (error_y=%+.2fpx, area=%.0f)",
                    steps_taken,
                    det.error_y,
                    det.area,
                )
                return True

            if steps_taken >= self.config.max_steps_per_frame:
                LOGGER.warning(
                    "Exceeded max_steps_per_frame (%d) without sprocket lock; assuming end of reel.",
                    self.config.max_steps_per_frame,
                )
                return False

            # Choose step size: fine stepping when close to target_y, coarse otherwise.
            # If the hole has already passed target_y slightly, step backward by 1 fine step.
            if det.found and abs(det.error_y) <= self.config.fine_zone_px:
                step_delta = (
                    self.config.fine_steps
                    if det.error_y < 0
                    else -self.config.fine_steps
                )
            else:
                step_delta = self.config.coarse_steps

            self.stepper.step(step_delta)
            steps_taken += abs(step_delta)

        return False

    def run_scan(self) -> int:
        """Execute automated frame-by-frame scanning loop. Returns frames captured."""
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        captured = 0

        self.camera.start()
        try:
            while not self._stop_requested:
                if self.config.max_frames > 0 and captured >= self.config.max_frames:
                    LOGGER.info("Reached max_frames=%d. Stopping scan.", self.config.max_frames)
                    break

                if not self._align_next_frame():
                    break

                if self.config.release_coils_on_capture:
                    self.stepper.release()

                if self.config.settle_delay_s > 0:
                    time.sleep(self.config.settle_delay_s)

                captured += 1
                stem = f"frame_{captured:06d}"
                dng_path = self.config.output_dir / f"{stem}.dng"
                jpg_path = (
                    self.config.output_dir / f"{stem}.jpg"
                    if self.config.save_preview_jpg
                    else None
                )

                self.camera.capture_dng(dng_path, jpg_path=jpg_path)
                LOGGER.info("Captured frame %06d -> %s", captured, dng_path)

                # Advance past the current sprocket hole so we don't re-trigger on it
                self.stepper.step(self.config.advance_past_steps)
        finally:
            if self.config.show_debug_window:
                cv2.destroyAllWindows()
            self.stepper.close()
            self.camera.stop()

        LOGGER.info("Scan finished. Total frames captured: %d", captured)
        return captured


def _parse_int_tuple(raw: str, expected_len: int, name: str) -> tuple[int, ...]:
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != expected_len:
        raise argparse.ArgumentTypeError(
            f"{name} must have {expected_len} comma-separated integers (got {raw!r})"
        )
    try:
        return tuple(int(p) for p in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid integer in {name}: {raw!r}") from exc


def _parse_float_tuple(raw: str, expected_len: int, name: str) -> tuple[float, ...]:
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != expected_len:
        raise argparse.ArgumentTypeError(
            f"{name} must have {expected_len} comma-separated numbers (got {raw!r})"
        )
    try:
        return tuple(float(p) for p in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid float in {name}: {raw!r}") from exc


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="DIY Standard 8mm Telecine Scanner (picamera2 + OpenCV + ULN2003)"
    )
    parser.add_argument(
        "-o", "--output-dir", type=Path, default=Path("./captures"),
        help="Destination directory for 12-bit DNG frames (e.g., external USB 3.0 SSD mount).",
    )
    parser.add_argument(
        "--pins", default="17,27,22,23",
        help="ULN2003 IN1..IN4 BCM GPIO pins (default: 17,27,22,23).",
    )
    parser.add_argument(
        "--reverse", action="store_true",
        help="Reverse stepper motor direction.",
    )
    parser.add_argument(
        "--step-delay", type=float, default=0.002,
        help="Delay in seconds between half-steps (default: 0.002).",
    )
    parser.add_argument(
        "--settle-delay", type=float, default=0.35,
        help="Vibration damping pause in seconds before capture (default: 0.35).",
    )
    parser.add_argument(
        "--roi", default="40,80,140,320",
        help="Sprocket detection ROI in preview pixels as x,y,w,h (default: 40,80,140,320).",
    )
    parser.add_argument(
        "--target-y", type=float, default=160.0,
        help="Target sprocket centroid Y inside ROI (default: 160.0).",
    )
    parser.add_argument(
        "--tolerance", type=float, default=3.0,
        help="Allowed alignment error in pixels (default: 3.0).",
    )
    parser.add_argument(
        "--threshold", type=int, default=220,
        help="Grayscale brightness threshold (0-255) for backlit sprocket hole (default: 220).",
    )
    parser.add_argument(
        "--min-area", type=float, default=300.0,
        help="Minimum sprocket contour area in px^2 (default: 300).",
    )
    parser.add_argument(
        "--max-area", type=float, default=18000.0,
        help="Maximum sprocket contour area in px^2 (default: 18000).",
    )
    parser.add_argument(
        "--advance-past-steps", type=int, default=45,
        help="Half-steps to advance after capture to clear current sprocket hole (default: 45).",
    )
    parser.add_argument(
        "--max-frames", type=int, default=0,
        help="Stop after N frames (0 = scan until end of reel).",
    )
    parser.add_argument(
        "--exposure-us", type=int, default=12000,
        help="Locked manual shutter exposure in microseconds (default: 12000).",
    )
    parser.add_argument(
        "--gain", type=float, default=1.0,
        help="Locked manual analogue gain (default: 1.0).",
    )
    parser.add_argument(
        "--wb-gains", default="1.8,1.5",
        help="Locked manual ColourGains as R,B for 5600K LED (default: 1.8,1.5).",
    )
    parser.add_argument(
        "--save-jpg", action="store_true",
        help="Also save a JPEG preview alongside each DNG frame.",
    )
    parser.add_argument(
        "--calibrate", action="store_true",
        help="Run live calibration mode (no stepping or saving).",
    )
    parser.add_argument(
        "--show-debug", action="store_true",
        help="Display OpenCV debug overlay window (requires desktop display).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simulate camera and stepper without Raspberry Pi hardware.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable debug logging.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    pins = _parse_int_tuple(args.pins, 4, "--pins")
    roi = _parse_int_tuple(args.roi, 4, "--roi")
    wb_gains = _parse_float_tuple(args.wb_gains, 2, "--wb-gains")

    config = ScannerConfig(
        output_dir=args.output_dir,
        gpio_pins=(pins[0], pins[1], pins[2], pins[3]),
        step_delay_s=args.step_delay,
        reverse_direction=args.reverse,
        settle_delay_s=args.settle_delay,
        roi=(roi[0], roi[1], roi[2], roi[3]),
        target_y=args.target_y,
        tolerance_px=args.tolerance,
        threshold=args.threshold,
        min_area=args.min_area,
        max_area=args.max_area,
        advance_past_steps=args.advance_past_steps,
        max_frames=args.max_frames,
        exposure_us=args.exposure_us,
        analogue_gain=args.gain,
        wb_gains=(wb_gains[0], wb_gains[1]),
        save_preview_jpg=args.save_jpg,
        calibrate_only=args.calibrate,
        show_debug_window=args.show_debug,
        dry_run=args.dry_run,
    )

    if config.dry_run:
        stepper: StepperDriver = MockStepper()
        camera: CameraDriver = MockCamera(config, stepper)
    else:
        stepper = ULN2003Stepper(
            pins=config.gpio_pins,
            step_delay_s=config.step_delay_s,
            reverse=config.reverse_direction,
        )
        camera = TelecineCamera(config)

    detector = SprocketDetector(config)
    scanner = TelecineScanner(config, stepper, camera, detector)

    def _handle_signal(signum: int, _frame: object) -> None:
        LOGGER.info("Received signal %d; shutting down cleanly...", signum)
        scanner.request_stop()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    if config.calibrate_only:
        scanner.run_calibration()
    else:
        scanner.run_scan()

    return 0


if __name__ == "__main__":
    sys.exit(main())
