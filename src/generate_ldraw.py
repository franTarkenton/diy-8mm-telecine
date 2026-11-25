#!/usr/bin/env python3
"""Generate a stud-accurate 3D LDraw (.ldr) model of the Flatbed 8mm Telecine Scanner.

Produces `cad/telecine_flatbed.ldr` on a compact 32x32 baseplate (3811.dat)
with 12 progressive `0 STEP` build stages ready for headless 3D isometric
rendering via LeoCAD or interactive 3D viewing in LeoCAD / BrickLink Studio.

Verified LDraw Part Axis Conventions (from visual LeoCAD inspection):
  - 1 stud = 20 LDU, 1 plate = 8 LDU, 1 brick = 24 LDU
  - Y points DOWN (y=0 is top of baseplate; negative Y goes UP)
  - 32x32 Baseplate (3811.dat): X in [-320, +320], Z in [-320, +320]
    Stud centers: col 0..31 -> -310 + col*20
  - Technic Axles (3737, 3706, 3705): default axis is X (horizontal).
    Use ROT_Z90 for vertical (Y) axles; ROT_ID for horizontal (X) axles.
  - Technic Gears/Pulleys/Wheels (3648, 3649, 4185, 6014, 61254):
    default axle hole is Z. Use ROT_X90 to lie flat on a vertical (Y) axle.
  - Technic Worm Gear (4716): default axis is Y; use ROT_Z90 for horizontal (X).
"""

from __future__ import annotations

from pathlib import Path

# LDraw standard color codes
BLACK = 0
BLUE = 1
GREEN = 2
RED = 4
YELLOW = 14
WHITE = 15
TRANS_ORANGE = 57
LIGHT_BLUISH_GRAY = 71
DARK_BLUISH_GRAY = 72

# 3x3 rotation matrices (row-major)
ROT_ID = (1, 0, 0, 0, 1, 0, 0, 0, 1)
ROT_Y90 = (0, 0, 1, 0, 1, 0, -1, 0, 0)
ROT_X90 = (1, 0, 0, 0, 0, -1, 0, 1, 0)
ROT_Z90 = (0, -1, 0, 1, 0, 0, 0, 0, 1)
ROT_Y90_Z90 = (0, 1, 0, 0, 0, 1, 1, 0, 0)  # tile lengthwise along Z (N-S), standing on 8mm edge (Y)


def stud_x(col: float) -> float:
    """Convert 0..31 stud column (West->East) to LDraw X coordinate on 32x32 baseplate."""
    return -310.0 + col * 20.0


def stud_z(row: float) -> float:
    """Convert 0..31 stud row (North->South) to LDraw Z coordinate on 32x32 baseplate."""
    return -310.0 + row * 20.0


class LDrawBuilder:
    """Helper for emitting clean, step-separated LDraw `.ldr` files."""

    def __init__(self, title: str) -> None:
        self.lines: list[str] = [
            f"0 {title}",
            "0 Name: telecine_flatbed.ldr",
            "0 Author: DIY 8mm Telecine Project",
            "0 !LDRAW_ORG Unofficial_Model",
            "",
        ]
        self.step_count = 0

    def comment(self, text: str) -> None:
        self.lines.append(f"0 // {text}")

    def part(
        self,
        color: int,
        x: float,
        y: float,
        z: float,
        part_file: str,
        rot: tuple[float, ...] = ROT_ID,
    ) -> None:
        r = " ".join(f"{v:g}" for v in rot)
        self.lines.append(f"1 {color} {x:g} {y:g} {z:g} {r} {part_file}")

    def step(self, label: str = "") -> None:
        if self.step_count > 0:
            self.lines.append("0 STEP")
            self.lines.append("")
        self.step_count += 1
        if label:
            self.comment(f"STEP {self.step_count}: {label}")

    def build(self) -> str:
        return "\n".join(self.lines) + "\n"


def build_telecine_ldr() -> str:
    """Construct the 12-step Flatbed Standard 8mm Telecine Scanner on a 32x32 baseplate."""
    b = LDrawBuilder("DIY Flatbed Standard 8mm Telecine Scanner")

    # Compact 32x32 layout (fills frame cleanly in isometric renders):
    # - Optical Light Axis (West -> East): row = 15.5
    # - 8mm Film Line (North -> South):    col = 13.5
    # - Supply Reel Center (North):        (col=11, row=4)   -> East rim tangent at col=13.5
    # - Take-Up Reel Center (South):       (col=11, row=27)  -> East rim tangent at col=13.5
    # - Driven Pinch Roller Center:        (col=15, row=21)  -> West rim touches col=13.5
    # - Idler Pinch Roller Center:         (col=12, row=21)  -> East rim touches col=13.5

    # ------------------------------------------------------------------
    # STEP 1: 32x32 Baseplate & Cross Anchor Rails
    # ------------------------------------------------------------------
    b.step("Baseplate 32x32 and Cross Anchor Rails")
    b.part(LIGHT_BLUISH_GRAY, 0, 0, 0, "3811.dat")
    # 2x West-East 1x16 Technic anchor bricks framing optical axis
    b.part(DARK_BLUISH_GRAY, stud_x(16.5), -24, stud_z(12), "3703.dat", ROT_ID)
    b.part(DARK_BLUISH_GRAY, stud_x(16.5), -24, stud_z(19), "3703.dat", ROT_ID)
    # 2x North-South 1x16 Technic anchor bricks framing film path
    b.part(DARK_BLUISH_GRAY, stud_x(10), -24, stud_z(15.5), "3703.dat", ROT_Y90)
    b.part(DARK_BLUISH_GRAY, stud_x(17), -24, stud_z(15.5), "3703.dat", ROT_Y90)

    # ------------------------------------------------------------------
    # STEP 2: North Supply Reel Bearing Pedestal (col=11, row=4)
    # ------------------------------------------------------------------
    b.step("North Supply Reel Bearing Pedestal")
    b.part(DARK_BLUISH_GRAY, stud_x(11), -24, stud_z(1), "3702.dat", ROT_ID)
    b.part(DARK_BLUISH_GRAY, stud_x(11), -24, stud_z(7), "3702.dat", ROT_ID)
    b.part(DARK_BLUISH_GRAY, stud_x(11), -34, stud_z(4), "64179.dat", ROT_Y90)
    for dc in (-3, 3):
        for dr in (-2, 2):
            b.part(LIGHT_BLUISH_GRAY, stud_x(11 + dc), -48, stud_z(4 + dr), "3004.dat", ROT_ID)
            b.part(LIGHT_BLUISH_GRAY, stud_x(11 + dc), -72, stud_z(4 + dr), "3004.dat", ROT_ID)
    b.part(DARK_BLUISH_GRAY, stud_x(11), -82, stud_z(4), "64179.dat", ROT_Y90)

    # ------------------------------------------------------------------
    # STEP 3: Vertical Supply Axle & Flat Supply Reel (North)
    # ------------------------------------------------------------------
    b.step("Vertical Supply Axle and Flat Supply Reel")
    # Vertical 10L axle (ROT_Z90 makes axle stand straight UP along Y!)
    b.part(BLACK, stud_x(11), -100, stud_z(4), "3737.dat", ROT_Z90)
    b.part(LIGHT_BLUISH_GRAY, stud_x(11), -94, stud_z(4), "3713.dat", ROT_Z90)
    # Flat Supply Reel (bottom flange + spool + top flange)
    b.part(BLUE, stud_x(11), -100, stud_z(4), "3649.dat", ROT_X90)
    b.part(DARK_BLUISH_GRAY, stud_x(11), -112, stud_z(4), "4185.dat", ROT_X90)
    b.part(BLUE, stud_x(11), -124, stud_z(4), "3649.dat", ROT_X90)

    # ------------------------------------------------------------------
    # STEP 4: South Take-Up Reel Pedestal, Bottom Pulley & Flat Reel
    # ------------------------------------------------------------------
    b.step("South Take-Up Reel Pedestal and Flat Take-Up Reel")
    b.part(DARK_BLUISH_GRAY, stud_x(11), -24, stud_z(24), "3702.dat", ROT_ID)
    b.part(DARK_BLUISH_GRAY, stud_x(11), -24, stud_z(30), "3702.dat", ROT_ID)
    b.part(DARK_BLUISH_GRAY, stud_x(11), -34, stud_z(27), "64179.dat", ROT_Y90)
    for dc in (-3, 3):
        for dr in (-2, 2):
            b.part(LIGHT_BLUISH_GRAY, stud_x(11 + dc), -48, stud_z(27 + dr), "3004.dat", ROT_ID)
            b.part(LIGHT_BLUISH_GRAY, stud_x(11 + dc), -72, stud_z(27 + dr), "3004.dat", ROT_ID)
    b.part(DARK_BLUISH_GRAY, stud_x(11), -82, stud_z(27), "64179.dat", ROT_Y90)
    # Vertical 10L Take-Up axle
    b.part(BLACK, stud_x(11), -100, stud_z(27), "3737.dat", ROT_Z90)
    # Bottom Wedge Belt Pulley for underneath slip-clutch band
    b.part(YELLOW, stud_x(11), -16, stud_z(27), "4185.dat", ROT_X90)
    b.part(LIGHT_BLUISH_GRAY, stud_x(11), -94, stud_z(27), "3713.dat", ROT_Z90)
    # Flat Take-Up Reel
    b.part(GREEN, stud_x(11), -100, stud_z(27), "3649.dat", ROT_X90)
    b.part(DARK_BLUISH_GRAY, stud_x(11), -112, stud_z(27), "4185.dat", ROT_X90)
    b.part(GREEN, stud_x(11), -124, stud_z(27), "3649.dat", ROT_X90)

    # ------------------------------------------------------------------
    # STEP 5: Gearbox Pedestal, Driven Pinch Roller & 24T Gear Shaft
    # ------------------------------------------------------------------
    b.step("Driven Pinch Roller and 24-Tooth Gear Shaft")
    b.part(DARK_BLUISH_GRAY, stud_x(16), -24, stud_z(19), "3701.dat", ROT_ID)
    b.part(DARK_BLUISH_GRAY, stud_x(16), -24, stud_z(23), "3701.dat", ROT_ID)
    b.part(DARK_BLUISH_GRAY, stud_x(16), -34, stud_z(21), "64179.dat", ROT_Y90)
    for dc in (-3, 3):
        for dr in (-2, 2):
            b.part(LIGHT_BLUISH_GRAY, stud_x(16 + dc), -48, stud_z(21 + dr), "3004.dat", ROT_ID)
            b.part(LIGHT_BLUISH_GRAY, stud_x(16 + dc), -72, stud_z(21 + dr), "3004.dat", ROT_ID)
    b.part(DARK_BLUISH_GRAY, stud_x(16), -82, stud_z(21), "64179.dat", ROT_Y90)
    # Vertical 10L Driven Shaft (ROT_Z90 -> vertical!)
    b.part(BLACK, stud_x(15), -100, stud_z(21), "3737.dat", ROT_Z90)
    # Bottom Wedge Belt Pulley
    b.part(YELLOW, stud_x(15), -16, stud_z(21), "4185.dat", ROT_X90)
    # Middle 24-Tooth Gear (flat, driven by worm gear)
    b.part(DARK_BLUISH_GRAY, stud_x(15), -58, stud_z(21), "3648.dat", ROT_X90)
    # Top Driven Smooth Rubber Tire + Wheel lying FLAT on vertical Y axle (Z-axis -> Y via ROT_X90!)
    b.part(LIGHT_BLUISH_GRAY, stud_x(15), -112, stud_z(21), "6014.dat", ROT_X90)
    b.part(BLACK, stud_x(15), -112, stud_z(21), "61254.dat", ROT_X90)

    # ------------------------------------------------------------------
    # STEP 6: Horizontal Worm Gear & 28BYJ-48 Stepper Motor Cradle
    # ------------------------------------------------------------------
    b.step("Self-Locking Worm Gear and 28BYJ-48 Stepper Cradle")
    # Horizontal 6L axle (ROT_ID -> runs East-West along X!)
    b.part(BLACK, stud_x(19), -58, stud_z(21), "3706.dat", ROT_ID)
    # 2L Worm Gear (ROT_Z90 -> horizontal along X, meshing with 24T gear!)
    b.part(DARK_BLUISH_GRAY, stud_x(17.5), -58, stud_z(21), "4716.dat", ROT_Z90)
    b.part(LIGHT_BLUISH_GRAY, stud_x(20), -58, stud_z(21), "3713.dat", ROT_ID)
    # 28BYJ-48 Stepper Motor Cradle + Motor housing proxy
    b.part(DARK_BLUISH_GRAY, stud_x(23), -24, stud_z(21), "3001.dat", ROT_ID)
    b.part(DARK_BLUISH_GRAY, stud_x(23), -48, stud_z(21), "3701.dat", ROT_ID)
    b.part(LIGHT_BLUISH_GRAY, stud_x(23), -58, stud_z(21), "3001.dat", ROT_ID)
    b.part(BLUE, stud_x(23), -66, stud_z(21), "3020.dat", ROT_ID)

    # ------------------------------------------------------------------
    # STEP 7: Spring-Loaded Idler Pinch Roller Arm (Yellow 1x7 Liftarm)
    # ------------------------------------------------------------------
    b.step("Spring-Loaded Idler Pinch Roller Arm")
    # Pivoting 1x7 Yellow Liftarm lying FLAT (vertical pin holes via ROT_Z90)
    b.part(YELLOW, stud_x(12), -92, stud_z(22.5), "32524.dat", ROT_Z90)
    # Vertical 4L axle (ROT_Z90 -> vertical!) holding Idler Rubber Tire FLAT (ROT_X90!)
    b.part(BLACK, stud_x(12), -106, stud_z(21), "3705.dat", ROT_Z90)
    b.part(LIGHT_BLUISH_GRAY, stud_x(12), -112, stud_z(21), "6014.dat", ROT_X90)
    b.part(BLACK, stud_x(12), -112, stud_z(21), "61254.dat", ROT_X90)
    b.part(LIGHT_BLUISH_GRAY, stud_x(12), -88, stud_z(24.5), "3673.dat", ROT_X90)

    # ------------------------------------------------------------------
    # STEP 8: Underneath Slip-Clutch Take-Up Band Route
    # ------------------------------------------------------------------
    b.step("Underneath Slip-Clutch Band Route")
    b.part(YELLOW, stud_x(13), -8, stud_z(24), "2431.dat", ROT_Y90)

    # ------------------------------------------------------------------
    # STEP 9: Smooth-Tile Film Gate at Center (+) Intersection (13.5, 15.5)
    # ------------------------------------------------------------------
    b.step("Smooth-Tile Film Gate and Aperture Mask")
    # Solid 4-stud-wide black pedestal (cols 12..15, rows 13..18) up to film bottom
    for y_lvl in (-24, -48, -72, -96):
        b.part(BLACK, stud_x(12.5), y_lvl, stud_z(15.5), "3001.dat", ROT_Y90)
        b.part(BLACK, stud_x(14.5), y_lvl, stud_z(15.5), "3001.dat", ROT_Y90)
    # Smooth 1x6 black glide tile directly beneath film bottom edge
    b.part(BLACK, stud_x(13.5), -104, stud_z(15.5), "6636.dat", ROT_Y90)
    # Solid West (col=12) and East (col=15) gate walls resting cleanly on pedestal
    for col in (12, 15):
        for row in (13.5, 17.5):
            b.part(BLACK, stud_x(col), -120, stud_z(row), "3004.dat", ROT_Y90)
            b.part(BLACK, stud_x(col), -144, stud_z(row), "3004.dat", ROT_Y90)
    # Top cap closing the aperture window above the 8mm film
    b.part(BLACK, stud_x(12.5), -152, stud_z(15.5), "3020.dat", ROT_Y90)
    b.part(BLACK, stud_x(14.5), -152, stud_z(15.5), "3020.dat", ROT_Y90)

    # ------------------------------------------------------------------
    # STEP 10: 3mm Acrylic Diffuser Slot & Black Brick Light Tunnel
    # ------------------------------------------------------------------
    b.step("3mm Acrylic Diffuser Slot and Black Light Tunnel")
    # Milky-white 3mm acrylic diffuser just West of gate (col=9)
    for y_lvl in (-24, -48, -72, -96):
        b.part(BLACK, stud_x(9), y_lvl, stud_z(15.5), "3010.dat", ROT_Y90)
    for y_lvl in (-120, -144):
        b.part(WHITE, stud_x(9), y_lvl, stud_z(15.5), "3010.dat", ROT_Y90)

    # Hollow Black Brick Light Tunnel extending East (cols 17..24, centered row=15.5)
    for col in (18, 22):
        for y_lvl in (-24, -48, -72, -96):
            b.part(BLACK, stud_x(col), y_lvl, stud_z(15.5), "3001.dat", ROT_ID)
        for wall_row in (13.5, 17.5):
            b.part(BLACK, stud_x(col), -120, stud_z(wall_row), "3010.dat", ROT_ID)
            b.part(BLACK, stud_x(col), -144, stud_z(wall_row), "3010.dat", ROT_ID)
        b.part(BLACK, stud_x(col), -152, stud_z(15.5), "3020.dat", ROT_ID)

    # ------------------------------------------------------------------
    # STEP 11: 5600K LED Cradle (Far West) & HQ Camera Cradle (Far East)
    # ------------------------------------------------------------------
    b.step("5600K LED Cradle and Raspberry Pi HQ Camera Cradle")
    # Far West LED Pedestal (col=3, row=15.5) with 2-3 cm air gap before diffuser
    for y_lvl in (-24, -48, -72, -96):
        b.part(BLACK, stud_x(3), y_lvl, stud_z(15.5), "3001.dat", ROT_Y90)
    b.part(BLACK, stud_x(2.5), -120, stud_z(15.5), "3010.dat", ROT_Y90)
    b.part(BLACK, stud_x(2.5), -144, stud_z(15.5), "3010.dat", ROT_Y90)
    b.part(WHITE, stud_x(3.5), -120, stud_z(15.5), "3010.dat", ROT_Y90)
    b.part(WHITE, stud_x(3.5), -144, stud_z(15.5), "3010.dat", ROT_Y90)

    # Far East HQ Camera Pedestal (col=28, row=15.5) shimmed with 2x4 plates
    for y_lvl in (-24, -48, -72, -96):
        b.part(BLACK, stud_x(28), y_lvl, stud_z(15.5), "3001.dat", ROT_ID)
    b.part(BLACK, stud_x(28), -104, stud_z(15.5), "3020.dat", ROT_ID)
    # 35mm C-mount lens + macro tubes (pointing West into tunnel)
    b.part(DARK_BLUISH_GRAY, stud_x(26), -120, stud_z(15.5), "3001.dat", ROT_ID)
    # Green Raspberry Pi HQ Camera PCB at col=29.5
    b.part(GREEN, stud_x(29.5), -120, stud_z(15.5), "3010.dat", ROT_Y90)
    b.part(GREEN, stud_x(29.5), -144, stud_z(15.5), "3010.dat", ROT_Y90)

    # ------------------------------------------------------------------
    # STEP 12: Thread Straight 8mm Film Strip (Standing on Edge, N -> S)
    # ------------------------------------------------------------------
    b.step("Thread 8mm Film Strip Tangent from Supply to Take-Up")
    # Translucent amber 1x6 tiles standing VERTICALLY on edge along col=13.5!
    for row in (7, 13, 19, 24.5):
        b.part(TRANS_ORANGE, stud_x(13.5), -114, stud_z(row), "6636.dat", ROT_Y90_Z90)

    return b.build()


def main() -> None:
    out_path = Path(__file__).resolve().parent.parent / "cad" / "telecine_flatbed.ldr"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_telecine_ldr(), encoding="utf-8")
    print(f"Wrote 12-step LDraw model -> {out_path}")


if __name__ == "__main__":
    main()
