---
name: ldraw-lego-cad
description: >-
  Use whenever generating, editing, or rendering LEGO Technic LDraw (.ldr) CAD
  models or build instructions in this project. Enforces zero brick collisions,
  verified LDraw part orientations, physical mechanical validity, max 4 pieces
  per step, and visual render inspection before sharing.
---

# LEGO / LDraw CAD Quality & Collision Rules

Follow these rules whenever creating or modifying LDraw (`.ldr`) models or LEGO build instructions:

## 1. Zero Brick Collisions or Intersections
- **Never place two bricks in the same 3D volume** (e.g., two perpendicular bricks crossing at the same `y` layer, or duplicate bricks stacked at the same `(x, y, z)`).
- Always butt-joint perpendicular rails cleanly using shorter bricks (e.g., `1×6` `3894.dat` fitting strictly between two `1×16` rails) or offset them onto different vertical layers.
- Never leave bricks floating in mid-air—every brick must rest solidly on studs, plates, or pinned Technic supports below it.

## 2. Physical & Mechanical Validity
- **Reels & film paths:** Film reels must always lie in-plane with the film travel direction (exact tangent unwinding, zero sideways twist).
- **Pinch rollers:** Rubber pinch rollers must roll *along* the flat faces of the film (flat horizontal tires on vertical axles for a flatbed layout).
- **Gears:** Worm gear (`4716`) and 24-tooth gear (`3648`) must sit on perpendicular axles at exact meshing distance without phantom intermediate gears.
- **Visual stand-ins:** Any non-LEGO proxy (e.g., translucent amber film strip, motor body, PCB) must be explicitly labeled as a visual stand-in so the builder never tries to snap it onto studs.

## 3. Verified LDraw Local Axes (Check Before Rotating!)
- **Baseplate (`3811.dat` 32×32):** `Y = 0` is top surface; negative `Y` goes UP (`1 stud = 20 LDU`, `1 plate = 8 LDU`, `1 brick = 24 LDU`).
- **Technic Axles (`3737`, `3706`, `3705`):** Default axis is **X** (horizontal). Use `ROT_Z90` for vertical (`Y`) axles; `ROT_ID` for horizontal (`X`) axles.
- **Gears, Pulleys & Wheels (`3648`, `3649`, `4185`, `6014`, `61254`):** Default axle hole is **Z**. Use `ROT_X90` to lie flat on a vertical (`Y`) axle.
- **Worm Gear (`4716`):** Default axis is **Y**. Use `ROT_Z90` for horizontal (`X`).
- **Technic Liftarms (`32524`):** Default pin holes run along **X**. Use `ROT_Z90` for vertical (`Y`) pin holes.

## 4. Instruction Booklet Standards
- **Maximum 4 pieces per step** (`MAX_PIECES_PER_STEP = 4`, enforced programmatically in `src/generate_ldraw.py`).
- **Always visually inspect rendered LeoCAD PNGs** with `read_file` after any edit to confirm zero collisions, correct rotations, and clean step highlights before presenting to the user.
