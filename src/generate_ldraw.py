#!/usr/bin/env python3
"""Generate a stud-accurate 3D LDraw (.ldr) model of the Flatbed 8mm Telecine Scanner
with a strict MAXIMUM OF 4 PIECES PER STEP (like an official LEGO booklet).

Outputs:
  - `cad/telecine_flatbed.ldr`  (multi-step LDraw CAD model)
  - `cad/steps_manifest.json`   (per-step parts, instructions, and bag metadata for the HTML booklet)
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
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
ROT_FILM_EDGE = (0, 1, 0, 0, 0, 1, 1, 0, 0)  # tile lengthwise along Z, standing on 8mm edge

PART_NAMES: dict[str, str] = {
    "3811.dat": "32×32 Baseplate",
    "3703.dat": "1×16 Technic Brick",
    "3894.dat": "1×6 Technic Brick",
    "3702.dat": "1×8 Technic Brick",
    "3701.dat": "1×4 Technic Brick",
    "3700.dat": "1×2 Technic Brick w/ Hole",
    "64179.dat": "5×7 Technic Frame (only 1!)",
    "3738.dat": "2×8 Technic Plate w/ Holes",
    "3003.dat": "2×2 Brick",
    "3001.dat": "2×4 Brick",
    "3004.dat": "1×2 Brick",
    "3010.dat": "1×4 Brick",
    "3020.dat": "2×4 Plate",
    "3737.dat": "10L Technic Axle",
    "3706.dat": "6L Technic Axle",
    "3705.dat": "4L Technic Axle",
    "3713.dat": "1L Technic Bush",
    "3649.dat": "8mm Reel Flange (40T Proxy)",
    "3648.dat": "24-Tooth Gear",
    "4185.dat": "Wedge Belt Pulley",
    "4716.dat": "2L Worm Gear",
    "6014.dat": "Wheel Rim",
    "61254.dat": "Smooth Rubber Tire",
    "32524.dat": "1×7 Technic Liftarm (Yellow)",
    "3673.dat": "Gray Frictionless Pin",
    "2431.dat": "1×4 Smooth Tile",
    "6636.dat": "1×6 Smooth Tile",
}

COLOR_NAMES: dict[int, str] = {
    BLACK: "Black",
    BLUE: "Blue",
    GREEN: "Green",
    RED: "Red",
    YELLOW: "Yellow",
    WHITE: "White",
    TRANS_ORANGE: "8mm Film Strip",
    LIGHT_BLUISH_GRAY: "Light Gray",
    DARK_BLUISH_GRAY: "Dark Gray",
}


def stud_x(col: float) -> float:
    return -310.0 + col * 20.0


def stud_z(row: float) -> float:
    return -310.0 + row * 20.0


@dataclass
class BuildStep:
    num: int
    bag: str
    title: str
    instructions: list[str]
    check: str
    parts_raw: list[tuple[int, float, float, float, str, tuple[float, ...]]] = field(default_factory=list)


class LDrawBookletBuilder:
    """Enforces <= 4 pieces per step and emits both .ldr and steps_manifest.json."""

    MAX_PIECES_PER_STEP = 4

    def __init__(self, title: str) -> None:
        self.title = title
        self.steps: list[BuildStep] = []
        self._current: BuildStep | None = None

    def step(self, bag: str, title: str, instructions: list[str], check: str) -> None:
        s = BuildStep(
            num=len(self.steps) + 1,
            bag=bag,
            title=title,
            instructions=instructions,
            check=check,
        )
        self.steps.append(s)
        self._current = s

    def part(
        self,
        color: int,
        x: float,
        y: float,
        z: float,
        part_file: str,
        rot: tuple[float, ...] = ROT_ID,
    ) -> None:
        assert self._current is not None, "Call step() before adding parts"
        self._current.parts_raw.append((color, x, y, z, part_file, rot))
        if len(self._current.parts_raw) > self.MAX_PIECES_PER_STEP:
            raise ValueError(
                f"Step {self._current.num} ({self._current.title!r}) has "
                f"{len(self._current.parts_raw)} pieces (max {self.MAX_PIECES_PER_STEP})!"
            )

    def build_ldr(self) -> str:
        lines = [
            f"0 {self.title}",
            "0 Name: telecine_flatbed.ldr",
            "0 Author: DIY 8mm Telecine Project",
            "0 !LDRAW_ORG Unofficial_Model",
            "0 !LPUB PAGE SIZE GLOBAL 11.0 8.5",
            "0 !LPUB PAGE ORIENTATION GLOBAL LANDSCAPE",
            "0 !LPUB PAGE BACKGROUND GLOBAL COLOR \"#E6F1FB\"",
            "0 !LPUB PLI BACKGROUND GLOBAL COLOR \"#FFFFFF\"",
            "0 !LPUB PLI BORDER GLOBAL ROUND #2563EB 0.035 10 MARGINS 0.08 0.08",
            "0 !LPUB ASSEM CAMERA_ANGLES GLOBAL 35 45",
            "0 !LPUB ASSEM MODEL_SCALE GLOBAL 0.72",
            "",
        ]
        for idx, s in enumerate(self.steps):
            if idx > 0:
                lines.append("0 STEP")
                lines.append("")
            lines.append(f"0 // STEP {s.num} ({s.bag}): {s.title} [{len(s.parts_raw)} pcs]")
            for color, x, y, z, pf, rot in s.parts_raw:
                r = " ".join(f"{v:g}" for v in rot)
                lines.append(f"1 {color} {x:g} {y:g} {z:g} {r} {pf}")
        return "\n".join(lines) + "\n"

    def build_manifest(self) -> list[dict[str, object]]:
        manifest: list[dict[str, object]] = []
        for s in self.steps:
            counts: Counter[tuple[str, int]] = Counter(
                (pf, color) for color, _x, _y, _z, pf, _r in s.parts_raw
            )
            parts_list = []
            for (pf, color), qty in counts.items():
                pid = pf.replace(".dat", "")
                name = PART_NAMES.get(pf, pid)
                icon_file = f"images/parts/{pid}_{color}.png"
                if color == TRANS_ORANGE:
                    name = "8mm Film Strip (Visual Guide)"
                    pid = "Film"
                else:
                    cname = COLOR_NAMES.get(color, "")
                    if cname and cname.lower() not in name.lower():
                        name = f"{cname} {name}"
                parts_list.append({"qty": f"{qty}×", "name": name, "id": pid, "icon": icon_file})

            manifest.append(
                {
                    "num": s.num,
                    "bag": s.bag,
                    "title": s.title,
                    "piece_count": len(s.parts_raw),
                    "parts": parts_list,
                    "instructions": s.instructions,
                    "check": s.check,
                }
            )
        return manifest


def build_telecine() -> LDrawBookletBuilder:
    b = LDrawBookletBuilder("DIY Flatbed Standard 8mm Telecine Scanner (Max 4 pcs/step)")

    # ==================================================================
    # BAG 1 — BASEPLATE & FLAT REEL TURNTABLES (Steps 1–10)
    # ==================================================================
    b.step(
        "Bag 1 · Foundation",
        "Place Baseplate & West–East Optical Rails",
        [
            "Lay the 32×32 baseplate (3811) flat on your table.",
            "Snap two 1×16 Technic bricks (3703) running West–East across the middle (rows 12 and 19) to frame the Light Path.",
        ],
        "Both 1×16 rails sit flat and parallel with a 6-stud gap between them.",
    )
    b.part(LIGHT_BLUISH_GRAY, 0, 0, 0, "3811.dat")
    b.part(DARK_BLUISH_GRAY, stud_x(16.5), -24, stud_z(12), "3703.dat", ROT_ID)
    b.part(DARK_BLUISH_GRAY, stud_x(16.5), -24, stud_z(19), "3703.dat", ROT_ID)

    b.step(
        "Bag 1 · Foundation",
        "Add North–South Film Path Side Rails (Zero Overlap)",
        [
            "Snap two 1×6 Technic bricks (3894) running North–South (cols 10 and 16) snugly BETWEEN the two 1×16 rails (rows 13–18) so zero bricks overlap.",
        ],
        "The two 1×6 rails butt cleanly against the inside edges of the 1×16 rails, framing the center Film Gate bay.",
    )
    b.part(DARK_BLUISH_GRAY, stud_x(10), -24, stud_z(15.5), "3894.dat", ROT_Y90)
    b.part(DARK_BLUISH_GRAY, stud_x(16), -24, stud_z(15.5), "3894.dat", ROT_Y90)

    b.step(
        "Bag 1 · Foundation",
        "Supply Reel Pedestal — Base & Lower Bearing Plate",
        [
            "At the North end (row 4), snap two 2×2 bricks (3003) at col 8 and col 14 (6 studs center-to-center).",
            "Snap one 2×8 Technic Plate with Holes (3738) flat across the top of both bricks.",
        ],
        "The center round hole of the 2×8 plate sits cleanly over (col 11, row 4).",
    )
    b.part(LIGHT_BLUISH_GRAY, stud_x(8), -24, stud_z(4), "3003.dat", ROT_ID)
    b.part(LIGHT_BLUISH_GRAY, stud_x(14), -24, stud_z(4), "3003.dat", ROT_ID)
    b.part(DARK_BLUISH_GRAY, stud_x(11), -32, stud_z(4), "3738.dat", ROT_ID)

    b.step(
        "Bag 1 · Foundation",
        "Supply Reel Pedestal — Riser Columns",
        [
            "Stack two 2×2 bricks (3003) on the West end and two 2×2 bricks on the East end of the lower 2×8 Technic plate.",
        ],
        "Both riser columns are 2 bricks tall above the lower plate.",
    )
    b.part(LIGHT_BLUISH_GRAY, stud_x(8), -56, stud_z(4), "3003.dat", ROT_ID)
    b.part(LIGHT_BLUISH_GRAY, stud_x(14), -56, stud_z(4), "3003.dat", ROT_ID)
    b.part(LIGHT_BLUISH_GRAY, stud_x(8), -80, stud_z(4), "3003.dat", ROT_ID)
    b.part(LIGHT_BLUISH_GRAY, stud_x(14), -80, stud_z(4), "3003.dat", ROT_ID)

    b.step(
        "Bag 1 · Foundation",
        "Supply Reel Pedestal — Top Bearing & Vertical Axle",
        [
            "Snap the second 2×8 Technic Plate with Holes (3738) flat across the top of the riser columns.",
            "Drop the vertical 10L axle (3737) down through both center holes and add a 1L bushing (3713) right above the top plate.",
        ],
        "The vertical 10L axle spins freely and stands dead plumb.",
    )
    b.part(DARK_BLUISH_GRAY, stud_x(11), -88, stud_z(4), "3738.dat", ROT_ID)
    b.part(BLACK, stud_x(11), -100, stud_z(4), "3737.dat", ROT_Z90)
    b.part(LIGHT_BLUISH_GRAY, stud_x(11), -94, stud_z(4), "3713.dat", ROT_Z90)

    b.step(
        "Bag 1 · Foundation",
        "Seat the Flat Supply Reel (North)",
        [
            "Wrap 2–3 neat turns of painter's tape around the upper axle tip so your 8mm Supply Reel fits snugly and sits FLAT like a vinyl record.",
            "(Shown here as a blue reel proxy resting at Film Plane Height, ~4.5 cm above the baseplate.)",
        ],
        "Spin the Supply Reel by hand—it stays level and its East rim aligns with col 13.5.",
    )
    b.part(BLUE, stud_x(11), -100, stud_z(4), "3649.dat", ROT_X90)
    b.part(DARK_BLUISH_GRAY, stud_x(11), -112, stud_z(4), "4185.dat", ROT_X90)
    b.part(BLUE, stud_x(11), -124, stud_z(4), "3649.dat", ROT_X90)

    b.step(
        "Bag 1 · Foundation",
        "Take-Up Reel Pedestal — Base & Lower Bearing Plate",
        [
            "At the South end (row 27), snap two 2×2 bricks (3003) at col 8 and col 14.",
            "Snap one 2×8 Technic Plate with Holes (3738) flat across the top.",
        ],
        "Matches the North Supply pedestal directly in line at col 11.",
    )
    b.part(LIGHT_BLUISH_GRAY, stud_x(8), -24, stud_z(27), "3003.dat", ROT_ID)
    b.part(LIGHT_BLUISH_GRAY, stud_x(14), -24, stud_z(27), "3003.dat", ROT_ID)
    b.part(DARK_BLUISH_GRAY, stud_x(11), -32, stud_z(27), "3738.dat", ROT_ID)

    b.step(
        "Bag 1 · Foundation",
        "Take-Up Reel Pedestal — Riser Columns",
        [
            "Stack two 2×2 riser bricks (3003) on each end of the South lower Technic plate.",
        ],
        "Same height as the North Supply pedestal.",
    )
    b.part(LIGHT_BLUISH_GRAY, stud_x(8), -56, stud_z(27), "3003.dat", ROT_ID)
    b.part(LIGHT_BLUISH_GRAY, stud_x(14), -56, stud_z(27), "3003.dat", ROT_ID)
    b.part(LIGHT_BLUISH_GRAY, stud_x(8), -80, stud_z(27), "3003.dat", ROT_ID)
    b.part(LIGHT_BLUISH_GRAY, stud_x(14), -80, stud_z(27), "3003.dat", ROT_ID)

    b.step(
        "Bag 1 · Foundation",
        "Take-Up Pedestal — Top Bearing, Axle & Bottom Pulley",
        [
            "Snap the upper 2×8 Technic Plate (3738) on top of the South risers.",
            "Drop the vertical 10L axle (3737) down, threading the yellow Wedge Belt Pulley (4185) at the bottom (~1 cm up) and a 1L bushing (3713) above the top plate.",
        ],
        "The bottom pulley spins smoothly with the axle underneath the lower plate.",
    )
    b.part(DARK_BLUISH_GRAY, stud_x(11), -88, stud_z(27), "3738.dat", ROT_ID)
    b.part(BLACK, stud_x(11), -100, stud_z(27), "3737.dat", ROT_Z90)
    b.part(YELLOW, stud_x(11), -16, stud_z(27), "4185.dat", ROT_X90)
    b.part(LIGHT_BLUISH_GRAY, stud_x(11), -94, stud_z(27), "3713.dat", ROT_Z90)

    b.step(
        "Bag 1 · Foundation",
        "Seat the Flat Take-Up Reel (South)",
        [
            "Seat your flat 8mm Take-Up Reel (green proxy) on the South vertical axle at the EXACT same height as the Supply Reel.",
        ],
        "A straight ruler along col 13.5 touches the East rims of both reels at the exact same height.",
    )
    b.part(GREEN, stud_x(11), -100, stud_z(27), "3649.dat", ROT_X90)
    b.part(DARK_BLUISH_GRAY, stud_x(11), -112, stud_z(27), "4185.dat", ROT_X90)
    b.part(GREEN, stud_x(11), -124, stud_z(27), "3649.dat", ROT_X90)

    # ==================================================================
    # BAG 2 — WORM-GEAR DRIVE & PINCH ROLLERS (Steps 11–18)
    # ==================================================================
    b.step(
        "Bag 2 · Film Drive",
        "Anchor Your Single 5×7 Technic Gearbox Frame",
        [
            "At row 23 (col 16), snap one 1×4 Technic brick (3701) onto the baseplate parallel to the existing row 19 rail.",
            "Mount your ONLY 5×7 Open-Center Technic Frame (64179) lying flat across the row 19 rail and the new row 23 brick.",
        ],
        "The 5×7 frame sits flat and rigid across both rails—this locks the worm gear and 24T gear in exact mesh.",
    )
    b.part(DARK_BLUISH_GRAY, stud_x(16), -24, stud_z(23), "3701.dat", ROT_ID)
    b.part(DARK_BLUISH_GRAY, stud_x(16), -34, stud_z(21), "64179.dat", ROT_Y90)

    b.step(
        "Bag 2 · Film Drive",
        "Add Gearbox Riser Columns (With Worm-Axle Bearing Hole)",
        [
            "Stack two 2×2 bricks (3003) on the West side (col 12) and one 2×2 brick + one 1×2 Technic Brick with Hole (3700) on the East side (col 18) so the horizontal worm-gear axle passes cleanly through a real Technic bearing hole.",
        ],
        "The round Technic hole on the East riser faces East–West right at 24T-gear height.",
    )
    b.part(LIGHT_BLUISH_GRAY, stud_x(12), -48, stud_z(21), "3003.dat", ROT_ID)
    b.part(LIGHT_BLUISH_GRAY, stud_x(18), -48, stud_z(21), "3003.dat", ROT_ID)
    b.part(LIGHT_BLUISH_GRAY, stud_x(12), -72, stud_z(21), "3003.dat", ROT_ID)
    b.part(LIGHT_BLUISH_GRAY, stud_x(18), -72, stud_z(21), "3700.dat", ROT_Y90)

    b.step(
        "Bag 2 · Film Drive",
        "Install Gearbox Top Bearing, Shaft, 24T Gear & Bottom Pulley",
        [
            "Snap one 2×8 Technic Plate with Holes (3738) across the top of the gearbox risers (centered at col 15).",
            "Drop the vertical 10L axle (3737) down through col 15, threading the yellow Pulley (4185) at the bottom and the 24-Tooth Gear (3648) inside the gearbox.",
        ],
        "Spin the vertical axle—the 24T gear and bottom pulley turn together smoothly.",
    )
    b.part(DARK_BLUISH_GRAY, stud_x(15), -80, stud_z(21), "3738.dat", ROT_ID)
    b.part(BLACK, stud_x(15), -100, stud_z(21), "3737.dat", ROT_Z90)
    b.part(YELLOW, stud_x(15), -16, stud_z(21), "4185.dat", ROT_X90)
    b.part(DARK_BLUISH_GRAY, stud_x(15), -58, stud_z(21), "3648.dat", ROT_X90)

    b.step(
        "Bag 2 · Film Drive",
        "Mount the Flat Driven Rubber Pinch Roller",
        [
            "Fit the smooth rubber tire (61254) onto the wheel rim (6014) and press it FLAT onto the top of the driven 10L axle at Film Plane Height.",
        ],
        "The West outer rubber tread of this flat roller lines up right along col 13.5.",
    )
    b.part(LIGHT_BLUISH_GRAY, stud_x(15), -112, stud_z(21), "6014.dat", ROT_X90)
    b.part(BLACK, stud_x(15), -112, stud_z(21), "61254.dat", ROT_X90)

    b.step(
        "Bag 2 · Film Drive",
        "Mesh the Horizontal Self-Locking Worm Gear",
        [
            "Slide the horizontal 6L axle (3706) through the East side of the gearbox at the exact height of the 24T gear.",
            "Thread the 2L Worm Gear (4716) so its spiral meshes snugly into the 24T gear, secured with a 1L bushing (3713).",
        ],
        "Turn the horizontal axle by hand—the rubber roller turns slowly. Try turning the rubber roller by hand—it MUST lock solid!",
    )
    b.part(BLACK, stud_x(19), -58, stud_z(21), "3706.dat", ROT_ID)
    b.part(DARK_BLUISH_GRAY, stud_x(17.5), -58, stud_z(21), "4716.dat", ROT_Z90)
    b.part(LIGHT_BLUISH_GRAY, stud_x(20), -58, stud_z(21), "3713.dat", ROT_ID)

    b.step(
        "Bag 2 · Film Drive",
        "Build the 28BYJ-48 Stepper Motor Cradle",
        [
            "At col 23, row 21, build the motor pedestal (2×4 brick + 1×4 Technic brick) to support the 28BYJ-48 stepper body.",
            "Connect the 28BYJ-48 shaft to the horizontal worm axle using the 5mm-to-Technic coupler and secure the motor with 2 zip-ties.",
        ],
        "The motor shaft aligns straight with the horizontal worm axle without binding.",
    )
    b.part(DARK_BLUISH_GRAY, stud_x(23), -24, stud_z(21), "3001.dat", ROT_ID)
    b.part(DARK_BLUISH_GRAY, stud_x(23), -48, stud_z(21), "3701.dat", ROT_ID)
    b.part(LIGHT_BLUISH_GRAY, stud_x(23), -58, stud_z(21), "3001.dat", ROT_ID)
    b.part(BLUE, stud_x(23), -66, stud_z(21), "3020.dat", ROT_ID)

    b.step(
        "Bag 2 · Film Drive",
        "Install the Yellow Pivoting Idler Arm & Axle",
        [
            "Lay the yellow 1×7 Technic liftarm (32524) FLAT on the West side (col 12), hinged at its South end with a gray frictionless pin (3673).",
            "Push the vertical 4L axle (3705) up through the North end hole of the yellow arm.",
        ],
        "The yellow arm swings freely like a flat horizontal hinge.",
    )
    b.part(YELLOW, stud_x(12), -92, stud_z(22.5), "32524.dat", ROT_Z90)
    b.part(LIGHT_BLUISH_GRAY, stud_x(12), -88, stud_z(24.5), "3673.dat", ROT_X90)
    b.part(BLACK, stud_x(12), -106, stud_z(21), "3705.dat", ROT_Z90)

    b.step(
        "Bag 2 · Film Drive",
        "Mount Idler Rubber Tire & Underneath Slip-Clutch Band",
        [
            "Press the second flat smooth rubber tire (61254 + 6014) onto the vertical 4L axle so it presses against the driven tire.",
            "Hook a small rubber band from the yellow arm to the gearbox frame for light pinch tension, and loop a thin slip-clutch rubber band underneath between the two yellow bottom pulleys (yellow route tile marks the diagonal path).",
        ],
        "Feed a test strip of 8mm film between the two flat rubber tires—turning the worm gear advances it smoothly South while gently winding the Take-Up Reel.",
    )
    b.part(LIGHT_BLUISH_GRAY, stud_x(12), -112, stud_z(21), "6014.dat", ROT_X90)
    b.part(BLACK, stud_x(12), -112, stud_z(21), "61254.dat", ROT_X90)
    b.part(YELLOW, stud_x(13), -8, stud_z(24), "2431.dat", ROT_Y90)

    # ==================================================================
    # BAG 3 — FILM GATE, DIFFUSER & LIGHT TUNNEL (Steps 19–27)
    # ==================================================================
    b.step(
        "Bag 3 · Optics Gate",
        "Film Gate Pedestal — Lower Two Layers",
        [
            "Right at the center + intersection (cols 12.5 and 14.5, row 15.5), stack two pairs of black 2×4 bricks (3001) to form a solid 4×4 pedestal base.",
        ],
        "Solid black 4×4 foundation centered directly on the optical axis.",
    )
    b.part(BLACK, stud_x(12.5), -24, stud_z(15.5), "3001.dat", ROT_Y90)
    b.part(BLACK, stud_x(14.5), -24, stud_z(15.5), "3001.dat", ROT_Y90)
    b.part(BLACK, stud_x(12.5), -48, stud_z(15.5), "3001.dat", ROT_Y90)
    b.part(BLACK, stud_x(14.5), -48, stud_z(15.5), "3001.dat", ROT_Y90)

    b.step(
        "Bag 3 · Optics Gate",
        "Film Gate Pedestal — Upper Two Layers",
        [
            "Add two more pairs of black 2×4 bricks (3001) bringing the pedestal right up to the bottom edge of the 8mm film.",
        ],
        "Top of the pedestal sits 4 bricks high (just under Film Plane Height).",
    )
    b.part(BLACK, stud_x(12.5), -72, stud_z(15.5), "3001.dat", ROT_Y90)
    b.part(BLACK, stud_x(14.5), -72, stud_z(15.5), "3001.dat", ROT_Y90)
    b.part(BLACK, stud_x(12.5), -96, stud_z(15.5), "3001.dat", ROT_Y90)
    b.part(BLACK, stud_x(14.5), -96, stud_z(15.5), "3001.dat", ROT_Y90)

    b.step(
        "Bag 3 · Optics Gate",
        "Smooth Glide Tile & West Gate Walls",
        [
            "Snap the smooth black 1×6 tile (6636) along the centerline (col 13.5) so the bottom edge of the film glides on glassy plastic.",
            "Add the lower West aperture wall bricks (1×2 black bricks, 3004) at rows 13.5 and 17.5, leaving a clean 1-frame window in the middle.",
        ],
        "Open light window sits dead-center on row 15.5.",
    )
    b.part(BLACK, stud_x(13.5), -104, stud_z(15.5), "6636.dat", ROT_Y90)
    b.part(BLACK, stud_x(12), -120, stud_z(13.5), "3004.dat", ROT_Y90)
    b.part(BLACK, stud_x(12), -120, stud_z(17.5), "3004.dat", ROT_Y90)

    b.step(
        "Bag 3 · Optics Gate",
        "Complete Aperture Window Walls (East & Upper)",
        [
            "Add the lower East gate wall bricks (3004) at col 15 and the upper West wall bricks to bring the window to full height.",
        ],
        "Clear vertical film channel runs cleanly North–South through the gate.",
    )
    b.part(BLACK, stud_x(15), -120, stud_z(13.5), "3004.dat", ROT_Y90)
    b.part(BLACK, stud_x(15), -120, stud_z(17.5), "3004.dat", ROT_Y90)
    b.part(BLACK, stud_x(12), -144, stud_z(13.5), "3004.dat", ROT_Y90)
    b.part(BLACK, stud_x(12), -144, stud_z(17.5), "3004.dat", ROT_Y90)

    b.step(
        "Bag 3 · Optics Gate",
        "Cap the Film Gate Roof",
        [
            "Add the final two upper East wall bricks (3004) and cap the Film Gate roof with two black 2×4 plates (3020).",
        ],
        "Pull a test strip of 8mm film (with a splice!) through the gate—it must glide with zero snagging.",
    )
    b.part(BLACK, stud_x(15), -144, stud_z(13.5), "3004.dat", ROT_Y90)
    b.part(BLACK, stud_x(15), -144, stud_z(17.5), "3004.dat", ROT_Y90)
    b.part(BLACK, stud_x(12.5), -152, stud_z(15.5), "3020.dat", ROT_Y90)
    b.part(BLACK, stud_x(14.5), -152, stud_z(15.5), "3020.dat", ROT_Y90)

    b.step(
        "Bag 3 · Optics Gate",
        "Build the 3mm Acrylic Diffuser Stand (West of Gate)",
        [
            "Just West of the Film Gate (col 9, row 15.5), stack four black 1×4 bricks (3010) to form the diffuser base.",
        ],
        "Sits squarely parallel to the Film Gate, ~2 cm to the West.",
    )
    b.part(BLACK, stud_x(9), -24, stud_z(15.5), "3010.dat", ROT_Y90)
    b.part(BLACK, stud_x(9), -48, stud_z(15.5), "3010.dat", ROT_Y90)
    b.part(BLACK, stud_x(9), -72, stud_z(15.5), "3010.dat", ROT_Y90)
    b.part(BLACK, stud_x(9), -96, stud_z(15.5), "3010.dat", ROT_Y90)

    b.step(
        "Bag 3 · Optics Gate",
        "Seat the Milky-White 3mm Cast Acrylic Diffuser",
        [
            "Seat your 3mm milky-white translucent cast acrylic sheet (#2447, shown as white bricks) straight and parallel right behind the Film Gate window.",
        ],
        "Covers the full aperture window evenly with zero tilt.",
    )
    b.part(WHITE, stud_x(9), -120, stud_z(15.5), "3010.dat", ROT_Y90)
    b.part(WHITE, stud_x(9), -144, stud_z(15.5), "3010.dat", ROT_Y90)

    b.step(
        "Bag 3 · Optics Gate",
        "Black Light Tunnel — Section 1 Base (Col 18)",
        [
            "Just East of the Film Gate (col 18, row 15.5), stack four black 2×4 bricks (3001) to form the first tunnel floor section.",
        ],
        "Flush against the East face of the Film Gate pedestal.",
    )
    b.part(BLACK, stud_x(18), -24, stud_z(15.5), "3001.dat", ROT_ID)
    b.part(BLACK, stud_x(18), -48, stud_z(15.5), "3001.dat", ROT_ID)
    b.part(BLACK, stud_x(18), -72, stud_z(15.5), "3001.dat", ROT_ID)
    b.part(BLACK, stud_x(18), -96, stud_z(15.5), "3001.dat", ROT_ID)

    b.step(
        "Bag 3 · Optics Gate",
        "Black Light Tunnel — Section 1 Walls",
        [
            "Add two layers of black 1×4 wall bricks (3010) along the North (row 13.5) and South (row 17.5) edges to form a hollow light-tight passage.",
        ],
        "Center channel at row 15.5 stays completely open for the optical beam.",
    )
    b.part(BLACK, stud_x(18), -120, stud_z(13.5), "3010.dat", ROT_ID)
    b.part(BLACK, stud_x(18), -120, stud_z(17.5), "3010.dat", ROT_ID)
    b.part(BLACK, stud_x(18), -144, stud_z(13.5), "3010.dat", ROT_ID)
    b.part(BLACK, stud_x(18), -144, stud_z(17.5), "3010.dat", ROT_ID)

    b.step(
        "Bag 3 · Optics Gate",
        "Black Light Tunnel — Section 2 Base (Col 22)",
        [
            "Continue East (col 22, row 15.5) with four more black 2×4 bricks (3001) for the second tunnel floor section.",
        ],
        "Forms a continuous straight tunnel floor toward the camera.",
    )
    b.part(BLACK, stud_x(22), -24, stud_z(15.5), "3001.dat", ROT_ID)
    b.part(BLACK, stud_x(22), -48, stud_z(15.5), "3001.dat", ROT_ID)
    b.part(BLACK, stud_x(22), -72, stud_z(15.5), "3001.dat", ROT_ID)
    b.part(BLACK, stud_x(22), -96, stud_z(15.5), "3001.dat", ROT_ID)

    b.step(
        "Bag 3 · Optics Gate",
        "Black Light Tunnel — Section 2 Walls",
        [
            "Add two layers of black 1×4 wall bricks (3010) along the North and South edges of Section 2.",
        ],
        "Peek through from the East—straight unobstructed view of the white diffuser.",
    )
    b.part(BLACK, stud_x(22), -120, stud_z(13.5), "3010.dat", ROT_ID)
    b.part(BLACK, stud_x(22), -120, stud_z(17.5), "3010.dat", ROT_ID)
    b.part(BLACK, stud_x(22), -144, stud_z(13.5), "3010.dat", ROT_ID)
    b.part(BLACK, stud_x(22), -144, stud_z(17.5), "3010.dat", ROT_ID)

    b.step(
        "Bag 3 · Optics Gate",
        "Cap the Black Light Tunnel Roof",
        [
            "Snap two black 2×4 plates (3020) across the top of Sections 1 and 2 to seal out room light from above.",
        ],
        "Shine a flashlight into the diffuser—only the backlit 1-frame window glows inside the dark tunnel.",
    )
    b.part(BLACK, stud_x(18), -152, stud_z(15.5), "3020.dat", ROT_ID)
    b.part(BLACK, stud_x(22), -152, stud_z(15.5), "3020.dat", ROT_ID)

    # ==================================================================
    # BAG 4 — LED, HQ CAMERA & FILM THREADING (Steps 31–35)
    # ==================================================================
    b.step(
        "Bag 4 · Camera & LED",
        "Build the 5600K LED Pedestal (Far West)",
        [
            "At Far West (col 3, row 15.5—leaving a 2–3 cm air gap before the diffuser so LED diodes blend smoothly), stack four black 2×4 bricks (3001).",
        ],
        "Squarely centered on row 15.5 facing straight East.",
    )
    b.part(BLACK, stud_x(3), -24, stud_z(15.5), "3001.dat", ROT_Y90)
    b.part(BLACK, stud_x(3), -48, stud_z(15.5), "3001.dat", ROT_Y90)
    b.part(BLACK, stud_x(3), -72, stud_z(15.5), "3001.dat", ROT_Y90)
    b.part(BLACK, stud_x(3), -96, stud_z(15.5), "3001.dat", ROT_Y90)

    b.step(
        "Bag 4 · Camera & LED",
        "Mount the 5600K CRI 95+ LED Video Light",
        [
            "Place your Ulanzi VL49 LED light (shown as black housing + white emitter face) squarely on the Far West pedestal facing straight East, set to 5600K on USB-C power.",
        ],
        "Light shines straight through the acrylic diffuser and Film Gate window.",
    )
    b.part(BLACK, stud_x(2.5), -120, stud_z(15.5), "3010.dat", ROT_Y90)
    b.part(BLACK, stud_x(2.5), -144, stud_z(15.5), "3010.dat", ROT_Y90)
    b.part(WHITE, stud_x(3.5), -120, stud_z(15.5), "3010.dat", ROT_Y90)
    b.part(WHITE, stud_x(3.5), -144, stud_z(15.5), "3010.dat", ROT_Y90)

    b.step(
        "Bag 4 · Camera & LED",
        "Build the HQ Camera Pedestal (Far East)",
        [
            "At Far East (col 28, row 15.5), stack four black 2×4 bricks (3001) to bring the camera mount up to optical axis height.",
        ],
        "Aligned straight along row 15.5 facing West into the black light tunnel.",
    )
    b.part(BLACK, stud_x(28), -24, stud_z(15.5), "3001.dat", ROT_ID)
    b.part(BLACK, stud_x(28), -48, stud_z(15.5), "3001.dat", ROT_ID)
    b.part(BLACK, stud_x(28), -72, stud_z(15.5), "3001.dat", ROT_ID)
    b.part(BLACK, stud_x(28), -96, stud_z(15.5), "3001.dat", ROT_ID)

    b.step(
        "Bag 4 · Camera & LED",
        "Shim Height & Mount 35mm Lens + RPi HQ Camera",
        [
            "Add black 2×4 shim plates (3020, 3.2 mm each) until the 35mm C-mount lens aligns dead-center with the Film Gate window.",
            "Seat the 35mm lens + macro tubes (gray proxy) and green Raspberry Pi HQ Camera PCB, and lock the PCB firmly with 2 zip-ties.",
        ],
        "LED, Diffuser, Film Gate, Tunnel, and 35mm Lens form one dead-straight horizontal line.",
    )
    b.part(BLACK, stud_x(28), -104, stud_z(15.5), "3020.dat", ROT_ID)
    b.part(DARK_BLUISH_GRAY, stud_x(26), -120, stud_z(15.5), "3001.dat", ROT_ID)
    b.part(GREEN, stud_x(29.5), -120, stud_z(15.5), "3010.dat", ROT_Y90)
    b.part(GREEN, stud_x(29.5), -144, stud_z(15.5), "3010.dat", ROT_Y90)

    b.step(
        "Bag 4 · Camera & LED",
        "Thread 8mm Film, Wire ULN2003 & Lock Focus",
        [
            "NOTE: The translucent amber strip shown here is NOT a LEGO part—it represents your actual 8mm movie film standing on edge!",
            "Thread a sacrificial 8mm test strip tangent off the Supply Reel → straight through the Film Gate → between the two flat Pinch Rollers → tangent onto the Take-Up Reel.",
            "Wire ULN2003 per docs/wiring.md, run `uv run python src/scanner.py --calibrate --show-debug`, focus on film grain, and lock the lens thumbscrews!",
        ],
        "Sprocket hole centers cleanly on the green target line and film advances smoothly with zero jitter. Ready to scan!",
    )
    b.part(TRANS_ORANGE, stud_x(13.5), -114, stud_z(7), "6636.dat", ROT_FILM_EDGE)
    b.part(TRANS_ORANGE, stud_x(13.5), -114, stud_z(13), "6636.dat", ROT_FILM_EDGE)
    b.part(TRANS_ORANGE, stud_x(13.5), -114, stud_z(19), "6636.dat", ROT_FILM_EDGE)
    b.part(TRANS_ORANGE, stud_x(13.5), -114, stud_z(24.5), "6636.dat", ROT_FILM_EDGE)

    return b


def render_booklet_html(manifest: list[dict[str, object]]) -> str:
    """Build the self-contained 35-step LEGO instruction booklet HTML."""
    steps_json = json.dumps(manifest, indent=2)
    n = len(manifest)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>LEGO Technic Build Booklet — Flatbed 8mm Telecine ({n} Steps, Max 4 pcs/step)</title>
  <style>
    :root {{
      --page-bg: #e6f1fb; --card-bg: #ffffff; --border: #cbd5e1;
      --parts-bg: #eff6ff; --parts-border: #2563eb;
      --fg: #0f172a; --muted: #475569; --primary: #2563eb; --primary-fg: #ffffff;
      --success: #16a34a; --success-bg: #f0fdf4;
    }}
    body.dark {{
      --page-bg: #0f172a; --card-bg: #1e293b; --border: #334155;
      --parts-bg: #172554; --parts-border: #60a5fa;
      --fg: #f1f5f9; --muted: #94a3b8; --primary: #3b82f6; --primary-fg: #ffffff;
      --success: #4ade80; --success-bg: #052e16;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; padding: 18px 16px 32px; background: var(--page-bg); color: var(--fg); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 14px; line-height: 1.45; }}
    .booklet {{ max-width: 1120px; margin: 0 auto; }}
    .topbar {{ display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 12px; }}
    .topbar h1 {{ margin: 0; font-size: 20px; font-weight: 800; }}
    .topbar .sub {{ font-size: 12px; color: var(--muted); }}
    .controls {{ display: flex; align-items: center; gap: 8px; }}
    button {{ cursor: pointer; font-family: inherit; font-size: 13px; font-weight: 600; padding: 6px 13px; border-radius: 7px; border: 1px solid var(--border); background: var(--card-bg); color: var(--fg); }}
    button:hover:not(:disabled) {{ border-color: var(--primary); color: var(--primary); }}
    button:disabled {{ opacity: 0.4; cursor: not-allowed; }}
    button.primary {{ background: var(--primary); color: var(--primary-fg); border-color: var(--primary); }}
    button.primary:hover:not(:disabled) {{ filter: brightness(1.08); color: var(--primary-fg); }}
    .scrubber {{ display: flex; flex-wrap: wrap; align-items: center; gap: 6px; background: var(--card-bg); border: 1px solid var(--border); border-radius: 10px; padding: 8px 10px; margin-bottom: 12px; }}
    .bag-group {{ display: flex; flex-wrap: wrap; align-items: center; gap: 3px; padding-right: 8px; border-right: 1px solid var(--border); }}
    .bag-group:last-child {{ border-right: none; padding-right: 0; }}
    .bag-label {{ font-size: 11px; font-weight: 800; color: var(--muted); text-transform: uppercase; margin-right: 3px; }}
    .step-pill {{ width: 26px; height: 26px; padding: 0; display: inline-flex; align-items: center; justify-content: center; border-radius: 5px; font-size: 11px; font-weight: 700; }}
    .step-pill.active {{ background: var(--primary); color: #fff; border-color: var(--primary); }}
    .step-pill.done {{ background: var(--success-bg); color: var(--success); border-color: var(--success); }}
    .page {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 18px; box-shadow: 0 4px 16px rgba(15,23,42,0.06); }}
    .page-header {{ display: flex; flex-wrap: wrap; align-items: flex-start; justify-content: space-between; gap: 14px; padding-bottom: 14px; margin-bottom: 16px; border-bottom: 1px solid var(--border); }}
    .step-badge-wrap {{ display: flex; align-items: center; gap: 14px; }}
    .step-num {{ font-size: 40px; font-weight: 900; line-height: 1; min-width: 52px; }}
    .bag-tag {{ display: inline-block; font-size: 11px; font-weight: 800; text-transform: uppercase; padding: 2px 8px; border-radius: 99px; background: var(--parts-bg); color: var(--primary); border: 1px solid var(--parts-border); margin-bottom: 4px; margin-right: 6px; }}
    .pcs-tag {{ display: inline-block; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 99px; background: var(--success-bg); color: var(--success); border: 1px solid var(--success); margin-bottom: 4px; }}
    .step-title {{ margin: 0; font-size: 18px; font-weight: 700; }}
    .parts-box {{ background: var(--parts-bg); border: 2px solid var(--parts-border); border-radius: 10px; padding: 8px 12px; min-width: 260px; max-width: 540px; }}
    .parts-box-title {{ font-size: 11px; font-weight: 800; text-transform: uppercase; color: var(--primary); margin-bottom: 6px; }}
    .parts-grid {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .part-chip {{ display: inline-flex; flex-direction: column; align-items: center; gap: 3px; background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 6px 8px; font-size: 11px; min-width: 84px; text-align: center; }}
    .part-icon {{ width: 52px; height: 52px; object-fit: contain; display: block; background: #ffffff; border-radius: 5px; padding: 2px; }}
    .part-meta {{ display: flex; align-items: center; gap: 4px; font-weight: 700; }}
    .part-qty {{ font-weight: 900; color: var(--primary); font-size: 13px; }}
    .part-id {{ font-family: ui-monospace, monospace; font-size: 10px; color: var(--muted); }}
    .visuals {{ display: grid; grid-template-columns: minmax(340px, 1.45fr) minmax(260px, 1fr); gap: 16px; align-items: start; }}
    @media (max-width: 860px) {{ .visuals {{ grid-template-columns: 1fr; }} }}
    .canvas-card {{ border: 1px solid var(--border); border-radius: 10px; padding: 10px; background: var(--page-bg); }}
    .canvas-label {{ display: flex; justify-content: space-between; align-items: center; font-size: 11px; font-weight: 700; color: var(--muted); text-transform: uppercase; margin-bottom: 6px; }}
    .img-wrap {{ background: #ffffff; border-radius: 6px; overflow: hidden; border: 1px solid var(--border); }}
    .img-wrap img {{ width: 100%; height: auto; display: block; }}
    .legend {{ display: flex; flex-wrap: wrap; gap: 12px; font-size: 11px; color: var(--muted); margin-top: 8px; }}
    .legend-item {{ display: inline-flex; align-items: center; gap: 5px; }}
    .swatch {{ width: 12px; height: 12px; border-radius: 3px; display: inline-block; }}
    .instr-col {{ display: flex; flex-direction: column; gap: 12px; }}
    .instr-list {{ margin: 0; padding-left: 20px; display: flex; flex-direction: column; gap: 8px; font-size: 14px; }}
    .fit-check {{ background: var(--success-bg); border: 1px solid var(--success); border-radius: 8px; padding: 10px 12px; font-size: 13px; }}
    .fit-check strong {{ color: var(--success); }}
    .step-progress {{ font-size: 12px; color: var(--muted); font-family: ui-monospace, monospace; }}
  </style>
</head>
<body>
  <div class="booklet">
    <div class="topbar">
      <div>
        <h1>LEGO Technic Build Booklet — Flatbed 8mm Telecine</h1>
        <div class="sub">{n} micro-steps · Strict max 4 pieces/step · Only 1× 5×7 frame · Use ← / → arrow keys to flip pages</div>
      </div>
      <div class="controls">
        <span id="step-progress" class="step-progress">1 / {n}</span>
        <button id="btn-theme">Dark Mode</button>
        <button id="btn-prev">← Prev</button>
        <button id="btn-next" class="primary">Next Step →</button>
      </div>
    </div>

    <div id="scrubber" class="scrubber"></div>

    <div class="page">
      <div class="page-header">
        <div class="step-badge-wrap">
          <div id="step-num" class="step-num">1</div>
          <div>
            <div>
              <span id="bag-tag" class="bag-tag">BAG 1</span>
              <span id="pcs-tag" class="pcs-tag">3 pieces</span>
            </div>
            <h2 id="step-title" class="step-title"></h2>
          </div>
        </div>
        <div class="parts-box">
          <div class="parts-box-title">Parts Needed for This Step (Max 4 pcs)</div>
          <div id="parts-grid" class="parts-grid"></div>
        </div>
      </div>

      <div class="visuals">
        <div class="canvas-card">
          <div class="canvas-label">
            <span id="view-title">3D Isometric LEGO CAD — Step 1</span>
            <div style="display:flex;gap:6px;">
              <button id="btn-mode-3d" class="primary" style="padding:2px 8px;font-size:11px;">Step 3D</button>
              <button id="btn-mode-full" style="padding:2px 8px;font-size:11px;">Full Color 3D</button>
            </div>
          </div>
          <div class="img-wrap">
            <img id="step-img" src="images/steps/step01.png" alt="3D LEGO Step Render" />
          </div>
          <div class="legend">
            <span class="legend-item"><span class="swatch" style="background:#e11d48;border:1px solid #991b1b"></span> New pieces in THIS step</span>
            <span class="legend-item"><span class="swatch" style="background:#94a3b8"></span> Already built (faded)</span>
            <span class="legend-item">Orbit in 3D: <code>leocad -l /usr/share/ldraw cad/telecine_flatbed.ldr</code></span>
          </div>
        </div>

        <div class="instr-col">
          <ol id="instr-list" class="instr-list"></ol>
          <div id="fit-check" class="fit-check"></div>
        </div>
      </div>
    </div>
  </div>

  <script>
    const STEPS = {steps_json};

    let currentStep = 0;
    let viewMode = "3d";

    const scrubberEl = document.getElementById("scrubber");
    const stepNumEl = document.getElementById("step-num");
    const bagTagEl = document.getElementById("bag-tag");
    const pcsTagEl = document.getElementById("pcs-tag");
    const stepTitleEl = document.getElementById("step-title");
    const partsGridEl = document.getElementById("parts-grid");
    const instrListEl = document.getElementById("instr-list");
    const fitCheckEl = document.getElementById("fit-check");
    const stepImg = document.getElementById("step-img");
    const viewTitle = document.getElementById("view-title");
    const stepProgress = document.getElementById("step-progress");
    const btnPrev = document.getElementById("btn-prev");
    const btnNext = document.getElementById("btn-next");
    const btnTheme = document.getElementById("btn-theme");
    const btnMode3d = document.getElementById("btn-mode-3d");
    const btnModeFull = document.getElementById("btn-mode-full");

    function render() {{
      const s = STEPS[currentStep];
      stepNumEl.textContent = s.num;
      bagTagEl.textContent = s.bag;
      pcsTagEl.textContent = s.piece_count + (s.piece_count === 1 ? " piece" : " pieces");
      stepTitleEl.textContent = s.title;
      stepProgress.textContent = s.num + " / " + STEPS.length;

      partsGridEl.innerHTML = s.parts.map(p =>
        '<div class="part-chip">' +
          '<img class="part-icon" src="' + p.icon + '" alt="' + p.name + '" />' +
          '<div class="part-meta"><span class="part-qty">' + p.qty + '</span><span class="part-id">' + p.id + '</span></div>' +
          '<div style="line-height:1.2;max-width:96px;">' + p.name + '</div>' +
        '</div>'
      ).join("");

      instrListEl.innerHTML = s.instructions.map(t => "<li>" + t + "</li>").join("");
      fitCheckEl.innerHTML = "<strong>Fit Check:</strong> " + s.check;

      btnPrev.disabled = currentStep === 0;
      btnNext.disabled = currentStep === STEPS.length - 1;
      btnNext.textContent = currentStep === STEPS.length - 1 ? "Done!" : "Next Step →";

      const pad = String(s.num).padStart(2, "0");
      if (viewMode === "3d") {{
        stepImg.src = "images/steps/step" + pad + ".png";
        viewTitle.textContent = "3D Isometric LEGO CAD — Step " + s.num + " (" + s.piece_count + " pcs highlighted)";
      }} else {{
        stepImg.src = "images/steps/complete_3d.png";
        viewTitle.textContent = "3D Isometric LEGO CAD — Finished Full-Color Model";
      }}
      btnMode3d.classList.toggle("primary", viewMode === "3d");
      btnModeFull.classList.toggle("primary", viewMode === "full");

      const bagOrder = [];
      const bagMap = {{}};
      STEPS.forEach((st, idx) => {{
        const shortBag = st.bag.split("·")[0].trim();
        if (!bagMap[shortBag]) {{ bagMap[shortBag] = []; bagOrder.push(shortBag); }}
        bagMap[shortBag].push(idx);
      }});
      scrubberEl.innerHTML = bagOrder.map(b =>
        '<div class="bag-group"><span class="bag-label">' + b + '</span>' +
        bagMap[b].map(idx => {{
          const cls = idx === currentStep ? "step-pill active" : (idx < currentStep ? "step-pill done" : "step-pill");
          return '<button class="' + cls + '" data-idx="' + idx + '">' + (idx + 1) + '</button>';
        }}).join("") + '</div>'
      ).join("");

      scrubberEl.querySelectorAll(".step-pill").forEach(btn => {{
        btn.addEventListener("click", () => {{
          currentStep = Number(btn.getAttribute("data-idx"));
          render();
        }});
      }});
    }}

    btnPrev.addEventListener("click", () => {{ if (currentStep > 0) {{ currentStep--; render(); }} }});
    btnNext.addEventListener("click", () => {{ if (currentStep < STEPS.length - 1) {{ currentStep++; render(); }} }});
    btnMode3d.addEventListener("click", () => {{ viewMode = "3d"; render(); }});
    btnModeFull.addEventListener("click", () => {{ viewMode = "full"; render(); }});
    btnTheme.addEventListener("click", () => {{
      document.body.classList.toggle("dark");
      btnTheme.textContent = document.body.classList.contains("dark") ? "Light Mode" : "Dark Mode";
    }});
    document.addEventListener("keydown", (e) => {{
      if (e.key === "ArrowRight" && currentStep < STEPS.length - 1) {{ currentStep++; render(); }}
      if (e.key === "ArrowLeft" && currentStep > 0) {{ currentStep--; render(); }}
    }});

    render();
  </script>
</body>
</html>
"""


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    builder = build_telecine()

    ldr_path = root / "cad" / "telecine_flatbed.ldr"
    ldr_path.parent.mkdir(parents=True, exist_ok=True)
    ldr_path.write_text(builder.build_ldr(), encoding="utf-8")

    manifest = builder.build_manifest()
    manifest_path = root / "cad" / "steps_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    html_path = root / "docs" / "lego_instructions.html"
    html_path.write_text(render_booklet_html(manifest), encoding="utf-8")

    max_pcs = max(s["piece_count"] for s in manifest)
    print(f"Wrote {len(manifest)}-step LDraw model (max {max_pcs} pcs/step) -> {ldr_path}")
    print(f"Wrote step manifest -> {manifest_path}")
    print(f"Wrote interactive booklet -> {html_path}")


if __name__ == "__main__":
    main()
