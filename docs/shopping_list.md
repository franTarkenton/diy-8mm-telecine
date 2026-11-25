# Shopping List — DIY Technic Standard 8mm Telecine Film Scanner

This shopping list covers every component in [PROJECT_SPEC.md](../PROJECT_SPEC.md), plus the small beginner essentials (power supplies, cables, SD card, and motor-to-Technic coupler) so you don't get stuck mid-build.

Vendors are ordered by preference: **Canadian Distributors first → AliExpress → Amazon.ca / Other**.

> **Estimated Total Budget (CAD, before shipping & tax):** **~\$385 – \$585 CAD** *(or **~\$300 – \$455 CAD** if you already own an external USB 3.0 SSD)*.

---

## 1. Raspberry Pi Compute & Camera (Canadian Distributor)

Buy these together from **PiShop.ca** (official Canadian Raspberry Pi distributor, ships from Ottawa, ON) to save on shipping:

| Item | Notes for Beginners | Where to Buy | Est. CAD |
| :--- | :--- | :--- | :--- |
| **Raspberry Pi 4 (4GB)** *(recommended for simplicity)* **or Pi 5 (4GB)** | Pi 4 uses the standard ribbon cable included with the HQ Camera. Pi 5 is faster, but requires the separate Pi 5 camera cable below. | [PiShop.ca — Pi 4 4GB](https://www.pishop.ca/search.php?search_query=Raspberry+Pi+4+4GB) / [PiShop.ca — Pi 5 4GB](https://www.pishop.ca/search.php?search_query=Raspberry+Pi+5+4GB) | \$75 – \$85 |
| **Official Raspberry Pi USB-C Power Supply** | Get the **15W (5V 3A)** for Pi 4, or **27W** for Pi 5. Avoid phone chargers—they cause undervoltage warnings with an SSD attached. | [PiShop.ca — Power Supplies](https://www.pishop.ca/search.php?search_query=Official+Power+Supply+USB-C) | \$12 – \$18 |
| **32GB+ microSD Card (Class 10 / A1)** | Holds Raspberry Pi OS and `src/scanner.py`. (Or grab a Pi Starter Kit if you also need a micro-HDMI cable.) | [PiShop.ca — microSD](https://www.pishop.ca/search.php?search_query=microSD+32GB) | \$12 – \$15 |
| **Raspberry Pi High Quality (HQ) Camera (C/CS-mount, IMX477)** | Make sure you get the **C/CS-mount** version (NOT the M12 version). Includes the C-to-CS adapter ring and a 15-pin ribbon cable. | [PiShop.ca — HQ Camera](https://www.pishop.ca/search.php?search_query=High+Quality+Camera) | \$70 – \$75 |
| *(Pi 5 Only)* **Camera Cable for Raspberry Pi 5 (22-pin to 15-pin, 300mm)** | Only needed if you chose Raspberry Pi 5. | [PiShop.ca — Pi 5 Camera Cable](https://www.pishop.ca/search.php?search_query=Camera+Cable+for+Raspberry+Pi+5) | \$0 – \$5 |
| **Section 1 Subtotal** | *(Low = Pi 4; High = Pi 5 + cable)* | | **\$169 – \$198** |

---

## 2. Macro Optics (C-Mount Lens & Extension Tubes)

Standard 8mm frames are tiny (4.5 mm × 3.3 mm). A fixed 35mm C-mount CCTV lens + macro extension tubes lets you fill ~80–85% of the HQ Camera sensor sharply.

| Item | What to Look For | Where to Buy | Est. CAD |
| :--- | :--- | :--- | :--- |
| **35mm f/1.6 or f/1.7 C-Mount Manual CCTV Lens** | Look for manual focus + manual iris with **locking thumbscrews** (e.g., Fujinon, Computar, or generic 35mm C-mount industrial/machine-vision lens). | **AliExpress:** [35mm C-mount lens](https://www.aliexpress.com/wholesale?SearchText=35mm+c+mount+lens+cctv+locking)<br>**Amazon.ca:** [35mm C-mount CCTV lens](https://www.amazon.ca/s?k=35mm+C-mount+CCTV+lens+f1.7) | \$25 – \$55 |
| **C-Mount Macro Extension Tube Ring Set (5mm / 10mm / 20mm)** | Aluminum C-mount (1"-32 TPI) spacer rings. You will typically stack ~15mm–25mm between the lens and the HQ Camera to focus close enough for 8mm film. | **AliExpress:** [C-mount macro extension rings](https://www.aliexpress.com/wholesale?SearchText=c+mount+macro+extension+tube+ring+set)<br>**Amazon.ca:** [C-mount extension tube](https://www.amazon.ca/s?k=C+mount+macro+extension+tube+5mm+10mm+20mm) | \$10 – \$20 |
| **Section 2 Subtotal** | | | **\$35 – \$75** |

---

## 3. Motion Control & Solderless Wiring

| Item | Notes for Beginners | Where to Buy | Est. CAD |
| :--- | :--- | :--- | :--- |
| **28BYJ-48 5V Stepper Motor + ULN2003 Driver Board** | Buy the **5V** version bundled with the green/blue **ULN2003** breakout board. Buying a 2-pack or 5-pack is cheap and gives you a spare. | **Canadian:** [BC Robotics (motor SKU `ROB-004`)](https://bc-robotics.com/?s=stepper+motor+5v) · [X2 Robotics](https://www.x2robotics.ca/)<br>**AliExpress:** [28BYJ-48 + ULN2003](https://www.aliexpress.com/wholesale?SearchText=28BYJ-48+ULN2003+5V+stepper+motor)<br>**Amazon.ca:** [28BYJ-48 + ULN2003 kit](https://www.amazon.ca/s?k=28BYJ-48+ULN2003+stepper+motor+driver) | \$5 – \$15 |
| **Female-to-Female DuPont Jumper Wires (20cm, 40-pin ribbon)** | You need 6 wires for the ULN2003 (`IN1–IN4`, `5V`, `GND`). Peel off what you need from a 40-pin ribbon. | **Canadian:** [BC Robotics](https://bc-robotics.com/?s=dupont+jumper+wires) · [Elmwood Electronics](https://elmwoodelectronics.ca/search?q=female+to+female+jumper+wires) · [Universal-Solder](https://universal-solder.ca/?s=dupont+jumper+wires)<br>**AliExpress:** [Female-to-Female DuPont](https://www.aliexpress.com/wholesale?SearchText=female+to+female+dupont+jumper+wires+20cm) | \$4 – \$8 |
| **Dedicated 5V Motor Power Adapter (Recommended)** | Keeps motor noise off the Pi's 5V rail while writing to the USB 3.0 SSD. Easiest solderless setup: a **5V 2A barrel power supply** + **DC barrel-to-screw-terminal adapter** + **Male-to-Female DuPont wires** (or a 5V MB102 breadboard power module). | **Canadian:** [BC Robotics](https://bc-robotics.com/?s=5v+power+supply) · [Elmwood Electronics](https://elmwoodelectronics.ca/search?q=breadboard+power+supply)<br>**Amazon.ca:** [MB102 5V breadboard power module](https://www.amazon.ca/s?k=MB102+breadboard+power+supply+5V) | \$8 – \$15 |
| **28BYJ-48 (5mm Double-D) to LEGO Technic Axle Coupler** | *Important catch:* The 28BYJ-48 has a 5mm metal shaft with two flat sides, while LEGO Technic uses a cross-axle. Grab a 5mm-to-Technic coupler (or 3D-print one) so it connects cleanly to your worm gear! | **AliExpress:** [5mm to Technic axle coupler](https://www.aliexpress.com/wholesale?SearchText=28BYJ-48+lego+technic+coupler)<br>**Alternative:** Local library 3D printer (free/cheap STL on Printables/Thingiverse: *"28BYJ-48 LEGO Technic adapter"*) | \$2 – \$8 |
| **Section 3 Subtotal** | | | **\$19 – \$46** |

---

## 4. Illumination & Diffuser

| Item | What to Look For | Where to Buy | Est. CAD |
| :--- | :--- | :--- | :--- |
| **CRI 95+ Bi-Color Mini LED Video Light (USB-C)** | Look for **CRI 95+**, USB-C powered (so it can run continuously plugged into a wall charger without draining the battery), adjustable to **5600K**. Popular choice: **Ulanzi VL49 (Bi-Color or RGB)** or **VIJIM VL81**. | **Amazon.ca:** [Ulanzi VL49 LED Video Light](https://www.amazon.ca/s?k=Ulanzi+VL49)<br>**AliExpress:** [Ulanzi VL49 Bi-Color](https://www.aliexpress.com/wholesale?SearchText=Ulanzi+VL49+bi-color+CRI+95) | \$25 – \$40 |
| **3mm (1/8") Milky-White Translucent Cast Acrylic Sheet** | Ask for **#2447 White Translucent Cell-Cast Acrylic** (signage/light-box diffuser grade). You only need a small piece (~4"×4" or 6"×6"). | **Canadian (cut-to-size):** [Plastic World (Toronto, ships Canada-wide)](https://plasticworld.ca/) · [Canada Plastics](https://www.canada-plastics.com/) · [Plasticuts](https://plasticuts.ca/)<br>**Amazon.ca:** [3mm milky white translucent cast acrylic](https://www.amazon.ca/s?k=milky+white+translucent+cast+acrylic+3mm) | \$10 – \$20 |
| **Section 4 Subtotal** | | | **\$35 – \$60** |

---

## 5. External Storage (12-Bit RAW/DNG Archive)

Each 12.3 MP 12-bit DNG frame is ~18–24 MB (~70–90 GB per 50-foot / 3,600-frame Standard 8mm reel). A fast USB 3.0 SSD is strongly recommended over writing to the microSD card.

| Item | Notes | Where to Buy | Est. CAD |
| :--- | :--- | :--- | :--- |
| **External USB 3.0 SSD (500GB – 1TB)** | Reliable options: **Crucial X6 / X9**, **Samsung T7**, or **SanDisk Extreme**. | **Canadian:** [Canada Computers](https://www.canadacomputers.com/en/search?s=external+ssd+1tb) · [Memory Express](https://www.memoryexpress.com/Search/Products?Search=external+ssd+1tb)<br>**Amazon.ca:** [1TB External USB 3.0 SSD](https://www.amazon.ca/s?k=external+USB+3.0+SSD+1TB) | \$85 – \$130 |
| **Section 5 Subtotal** | | | **\$85 – \$130** |

---

## 6. Mechanical Frame (Compatible LEGO Technic Parts)

You have two great ways to source the Technic structure:
- **Option A — Lowest cost (AliExpress):** Order a bulk Technic liftarm/gear/pin kit + a few specific part packs (2–3 weeks shipping to Canada).
- **Option B — Exact parts, fast Canadian shipping (BrickLink):** Create a wanted list on [BrickLink.com](https://www.bricklink.com/) and filter stores by **Seller Country: Canada**.

| Component | Specific Parts / Specs | Where to Buy | Est. CAD |
| :--- | :--- | :--- | :--- |
| **Baseplate (32×32 or 48×48)** | Rigid flat foundation to keep camera, gate, and reel towers aligned. | **AliExpress:** [48×48 Baseplate](https://www.aliexpress.com/wholesale?SearchText=48x48+baseplate+building+blocks)<br>**Amazon.ca:** [32×32 / 48×48 Baseplate](https://www.amazon.ca/s?k=48x48+baseplate+compatible) | \$8 – \$15 |
| **Technic Liftarms, Beams, Axles, Pins & Bushings Kit** | Used for A-frame reel towers, camera cradle, and roller frame. Note: Standard LEGO axles are 4.8 mm; wrap a thin layer of tape or use Technic bushings/spacers to snugly center **8mm (5/16") Standard 8mm reel hubs**. | **AliExpress:** [Technic Liftarms/Axles/Pins Bulk Kit](https://www.aliexpress.com/wholesale?SearchText=technic+liftarm+beam+axle+bushing+bulk+kit) | \$15 – \$25 |
| **Worm Gear + 24-Tooth Gear Pack** | Gives a self-locking 24:1 reduction from the 28BYJ-48 stepper to the film drive roller. | **AliExpress:** [Technic Worm Gear + 24T Gear](https://www.aliexpress.com/wholesale?SearchText=technic+worm+gear+24+tooth+gear+pack)<br>**BrickLink (CA):** Search part `4716` (Worm Gear) & `3648` (24T Gear) | \$4 – \$8 |
| **Soft Rubber Rollers / Technic Tires (2×) + Silicone Rubber Bands** | Two small smooth-tread Technic tires (e.g., ~14mm–24mm diameter) act as gentle pinch rollers; a thin rubber band acts as the slip-clutch drive to the take-up reel. | **AliExpress:** [Technic Small Smooth Tires + Wheels](https://www.aliexpress.com/wholesale?SearchText=technic+small+rubber+tire+wheel+pack) | \$5 – \$10 |
| **Black Bricks & Smooth Studless Tiles (1×4, 1×6, 2×4)** | Black bricks build the light-tight lens tunnel and aperture mask; **smooth studless tiles** form the scratch-free film gate channel. | **AliExpress:** [Black Bricks & Smooth Tiles Bulk](https://www.aliexpress.com/wholesale?SearchText=black+smooth+tiles+bricks+compatible+bulk)<br>**BrickLink (CA):** Filter by Color: Black, Category: Tile & Brick | \$10 – \$18 |
| **Section 6 Subtotal** | | | **\$42 – \$76** |

---

## Cost Summary (CAD, before shipping & tax)

| Category | Est. Low (CAD) | Est. High (CAD) |
| :--- | ---: | ---: |
| 1. Raspberry Pi Compute & HQ Camera | \$169 | \$198 |
| 2. Macro Optics (35mm C-Mount + Tubes) | \$35 | \$75 |
| 3. Motion Control & Solderless Wiring | \$19 | \$46 |
| 4. Illumination & Diffuser | \$35 | \$60 |
| 5. External USB 3.0 SSD (500GB – 1TB) | \$85 | \$130 |
| 6. Mechanical Frame (Technic Parts) | \$42 | \$76 |
| **Grand Total** | **\$385** | **\$585** |
| *Grand Total (if you already own an SSD)* | *\$300* | *\$455* |

---

## Suggested Order Strategy for a First-Time Builder

1. **Order AliExpress items first** (Technic parts, 35mm C-mount lens, macro extension rings, and 5mm-to-Technic coupler) since they take 2–3 weeks to arrive in Canada.
2. **Order your Canadian electronics bundle** from **PiShop.ca** (Raspberry Pi 4/5, HQ Camera, power supply, microSD) + **BC Robotics / Elmwood Electronics** (28BYJ-48 + ULN2003, DuPont wires).
3. **Grab the LED light, 3mm translucent acrylic, and USB 3.0 SSD** from **Amazon.ca / Plastic World / Canada Computers** once you're ready to assemble.
