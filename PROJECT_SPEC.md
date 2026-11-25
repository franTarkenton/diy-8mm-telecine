# Project: DIY Technic-Built Standard 8mm Telecine Film Scanner

## Project Goal
Build a high-quality, solderless, frame-by-frame Standard 8mm (Regular 8) film scanner using compatible LEGO Technic bricks, a Raspberry Pi, and a high-resolution macro camera setup to digitize a large archive of home movie reels.

## Architecture & Optical Design
- **Direct-to-Sensor Capture:** No projection screen. A backlit film frame is photographed directly by a macro lens through a light-tight black brick tunnel.
- **Film Transport (Sprocketless):** Smooth flat LEGO tiles guide the film edges; two soft rubber rollers driven by a worm-gear stepper motor advance the film gently without metal claws. A slip-clutch rubber band drives the take-up reel.
- **Light Path:** High-CRI LED backlight -> 3mm milky-white acrylic diffuser -> black brick aperture mask (illuminating only 1 frame + adjacent sprocket hole) -> film gate -> light-tight black brick lens tunnel -> macro lens -> camera sensor.

## Approved Hardware Bill of Materials (BOM)
- **Camera:** Raspberry Pi High Quality (HQ) Camera (C/CS-mount, 12.3 MP Sony IMX477, electronic shutter).
- **Optics:** Fixed 35mm C-mount industrial/CCTV lens (with locking focus & iris thumbscrews) + C-mount macro extension tube ring set (5mm/10mm/20mm).
- **Compute & Storage:** Raspberry Pi 4 (4GB) or Raspberry Pi 5 (4GB) + external USB 3.0 SSD for storing 12-bit RAW/DNG frames.
- **Motion Control (Solderless):** 28BYJ-48 5V stepper motor + ULN2003 driver board + Female-to-Female DuPont jumper wires to Raspberry Pi GPIO.
- **Illumination:** CRI 95+ bi-color mini LED video light (USB-C powered, set to 5600K) + 3mm milky-white translucent cast acrylic diffuser.
- **Mechanical Frame:** Compatible Technic baseplate (32x32 or 48x48), Technic liftarms for A-frame reel towers, axles with bushings (sized for 8mm / 5/16" Standard 8mm reel holes), worm gear + 24-tooth gear, rubber rollers, black bricks, and smooth studless tiles.

## Software Requirements & Next Artifacts Needed
1. **GPIO Wiring Guide (`docs/wiring.md`):** Pin-out diagram connecting the ULN2003 driver board to the Raspberry Pi GPIO header.
2. **Capture & Alignment Script (`src/scanner.py`):** Python script using `picamera2` and `OpenCV` that:
   - Advances the 28BYJ-48 stepper motor incrementally.
   - Monitors the live preview to detect when the sprocket hole centers in the frame.
   - Pauses briefly for vibration damping, captures a full-res 12-bit DNG/RAW frame to the external SSD, and loops automatically.
3. **Post-Processing Script (`src/compile_video.sh`):** FFmpeg workflow to assemble captured frames into an archival video file at 16 fps or 18 fps.
4. **Build Checklist (`task.md`):** Step-by-step assembly, calibration, and focus-locking procedure.
