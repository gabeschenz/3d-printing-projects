"""Parametric model of a relic-style "holy shotgun" display prop.

A non-functional costume/display piece inspired by the crucifix shotgun in
the film Constantine (2005).  Nothing here can chamber or fire anything: the
barrel is a solid rod sleeve, the drum is a free-spinning ornament, and the
shells are solid dummies.

Coordinate system for the assembled prop (millimetres):
    X  runs along the barrel, muzzle at +X, rear face of the receiver at X=0
    Y  is left/right, +Y is the holder's left
    Z  is up; the barrel axis is Z=0

Every part function returns a solid in assembled position.  `build_parts()`
collects them with their print orientation, colour and quantity.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from build123d import (
    Box,
    Circle,
    Cone,
    Cylinder,
    Ellipse,
    FontStyle,
    Location,
    Part,
    Plane,
    Polygon,
    Pos,
    Rectangle,
    RectangleRounded,
    Rot,
    Text,
    chamfer,
    extrude,
    fillet,
    loft,
)

# --------------------------------------------------------------------------
# Parameters
# --------------------------------------------------------------------------

# Printer envelope the parts are sized for.
BED_X, BED_Y, BED_Z = 220.0, 220.0, 250.0
BED_MARGIN = 7.5  # keep parts this far inside the bed edge on each side

# Fits (radial clearances).
FIT = 0.15    # parts that are glued or pressed together
SLIDE = 0.25  # parts that should turn or slide freely

# Hardware.
ROD_R = 4.0          # 8 mm rod: barrel spine and drum axle
SCREW_CLEAR_R = 1.7  # M3 clearance hole
SCREW_TAP_R = 1.4    # M3 self-tapping pilot (2.8 mm)
SCREW_HEAD_R = 3.2   # M3 socket-head counterbore
SCREW_HEAD_DEPTH = 3.2

# Receiver ("frame").  Printed as left/right halves split on Y=0.
FRAME_HALF_W = 20.0
FRAME_TOP_Z = 27.0
FRAME_BOT_Z = -60.0
STRAP_BOT_Z = 15.0
REAR_BLOCK_X1 = 88.0   # rear block spans X 0..88
BAY_X1 = 157.0         # drum bay spans X 88..157
FRAME_X1 = 197.0       # front block spans X 157..197
BOSS_LEN = 6.0         # shroud locating boss on the front face

# Drum (12 dummy shells, Striker style: the top chamber lines up with the barrel).
N_CHAMBERS = 12
DRUM_PITCH_R = 47.5
AXLE_Z = -DRUM_PITCH_R
DRUM_R = 61.5
SHIELD_X0, SHIELD_X1 = 88.0, 92.0
DRUM_X0, DRUM_X1 = 92.5, 156.5
SHELL_R = 10.0
SHELL_RIM_R = 11.25
SHELL_RIM_T = 1.8
CHAMBER_R = SHELL_R + 0.3
DRUM_FRONT_WALL = 4.0

# Barrel, spine rod and shroud.
BARREL_R = 11.0
BARREL_X0 = 179.0
BARREL_SPLIT_X = 370.0
MUZZLE_X = 560.0
SPINE_X0, SPINE_X1 = 165.0, 546.0
SHROUD_R_OUT, SHROUD_R_IN = 20.0, 17.5
SHROUD_X0 = FRAME_X1
SHROUD_SPLIT_X = 348.0
SHROUD_X1 = 500.0
SPIGOT_R = SHROUD_R_IN - 0.2
SPIGOT_LEN = 8.0
BAND_R = 22.0
RIB_HALF_W = 7.0
RIB_TOP_Z = 26.0

# Accessories.
TORCH_Z = 33.0
TORCH_X0, TORCH_X1 = 248.0, 340.0
DRAGON_Z = -36.0
DRAGON_R = 11.0
DRAGON_X0, DRAGON_X1 = 300.0, 500.0
FOREGRIP_X0, FOREGRIP_X1 = 215.0, 245.0

# Trigger.
TRIGGER_PIVOT = (61.0, -49.0)  # (X, Z)
TRIGGER_HALF_W = 4.0

# Inscriptions (engraved on the receiver sides).  These are stand-ins chosen
# for the theme, not a transcription of the film prop.
TEXT_LEFT = "VADE RETRO SATANA"
TEXT_RIGHT = "LUX IN TENEBRIS"
TEXT_FONT = "DejaVu Serif"
TEXT_SIZE = 6.5
TEXT_DEPTH = 0.8

# Frame clamp screws (X, Z).  M3 x 30, heads on the right-hand side.
FRAME_SCREWS = [(12, 14), (76, -24), (163, -26), (189, -26), (168, 21)]
GRIP_TONGUE_SCREWS = [(10, -46), (23, -52)]
GRIP_BODY_SCREWS = [(7.3, -100), (-4.8, -145)]  # M3 x 20

# Colours used for previews and as a filament suggestion.
BRASS = (0.78, 0.62, 0.25)
STEEL = (0.25, 0.26, 0.29)
WOOD = (0.36, 0.22, 0.12)
GOLD = (0.90, 0.74, 0.25)
HARDWARE = (0.70, 0.72, 0.75)

# --------------------------------------------------------------------------
# Small geometry helpers
# --------------------------------------------------------------------------

P_XZ = Plane(origin=(0, 0, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))  # local (x, y) -> (X, Z)
P_YZ = Plane(origin=(0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))   # local (x, y) -> (Y, Z)


def xcyl(r, x0, x1, y=0.0, z=0.0):
    """Cylinder along X from x0 to x1."""
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(r, x1 - x0)


def ycyl(r, y0, y1, x=0.0, z=0.0):
    """Cylinder along Y from y0 to y1."""
    return Pos(x, (y0 + y1) / 2, z) * Rot(90, 0, 0) * Cylinder(r, y1 - y0)


def xcone(r0, r1, x0, x1, y=0.0, z=0.0):
    """Cone along X with radius r0 at x0 and r1 at x1."""
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cone(max(r0, 1e-3), max(r1, 1e-3), x1 - x0)


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def prism_xz(sketch, y0, y1):
    """Extrude a sketch drawn as (X, Z) from y0 to y1."""
    plane = Plane(origin=(0, y1, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    return extrude(plane * sketch, amount=y1 - y0, dir=(0, -1, 0))


def prism_yz(sketch, x0, x1):
    """Extrude a sketch drawn as (Y, Z) from x0 to x1."""
    plane = Plane(origin=(x0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    return extrude(plane * sketch, amount=x1 - x0, dir=(1, 0, 0))


def poly(*pts):
    """Polygon through the given points, always wound counter-clockwise."""
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))
    if area < 0:
        pts = pts[::-1]
    return Polygon(*pts, align=None)


def rect(x0, x1, y0, y1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2) * Rectangle(x1 - x0, y1 - y0)


def cross_sketch(length, width, bar, arm_pos=0.3, gusset=0.0):
    """Latin cross.  Long axis on local x with the head at +x, centred on its
    bounding box.  `gusset` adds a small diamond at the crossing so the arms
    print without an unsupported ceiling when the long axis is vertical."""
    cx = length / 2 - arm_pos * length
    sk = Rectangle(length, bar) + Pos(cx, 0) * Rectangle(bar, width)
    if gusset > 0:
        side = (bar / 2 + gusset) * math.sqrt(2)
        sk += Pos(cx, 0) * Rot(0, 0, 45) * Rectangle(side, side)
    return sk


def about_axle(angle_deg):
    """Location that rotates about the drum axle by angle_deg."""
    return Pos(0, 0, AXLE_Z) * Rot(angle_deg, 0, 0) * Pos(0, 0, -AXLE_Z)


# --------------------------------------------------------------------------
# Receiver
# --------------------------------------------------------------------------


def trigger_sketch():
    px, pz = TRIGGER_PIVOT
    blade = poly(
        (px + 2.0, pz - 3.0),
        (px + 2.0, pz - 13.0),
        (px + 1.2, pz - 20.0),
        (px + 1.6, pz - 27.0),
        (px + 3.4, pz - 34.0),
        (px + 5.6, pz - 39.0),
        (px + 1.0, pz - 39.5),
        (px - 2.6, pz - 33.0),
        (px - 4.6, pz - 25.0),
        (px - 5.0, pz - 12.0),
        (px - 5.0, pz - 3.0),
    )
    return blade + Pos(px, pz) * Circle(5.5)


def frame_full():
    """The whole receiver before it is split into halves."""
    w = FRAME_HALF_W
    outline = poly(
        (0, FRAME_BOT_Z),
        (REAR_BLOCK_X1, FRAME_BOT_Z),
        (REAR_BLOCK_X1, STRAP_BOT_Z),
        (BAY_X1, STRAP_BOT_Z),
        (BAY_X1, FRAME_BOT_Z),
        (176, FRAME_BOT_Z),
        (FRAME_X1, -36),
        (FRAME_X1, FRAME_TOP_Z),
        (0, FRAME_TOP_Z),
    )
    rear_top = outline.vertices().sort_by_distance((0, FRAME_TOP_Z, 0))[0]
    outline = fillet(rear_top, 12)
    front_top = outline.vertices().sort_by_distance((FRAME_X1, FRAME_TOP_Z, 0))[0]
    outline = fillet(front_top, 4)
    body = prism_xz(outline, -w, w)
    # Soften the block: bevel every edge of the two outer faces.
    body = chamfer(body.edges().filter_by(lambda e: abs(abs(e.center().Y) - w) < 1e-6), 2.0)

    # Trigger guard: a loop under the rear block, 12 mm wide.
    guard = Pos(61, -74) * RectangleRounded(50, 48, 12) - Pos(61, -71.5) * RectangleRounded(40, 43, 8)
    guard &= rect(30, 90, -100, FRAME_BOT_Z + 0.5)
    body += prism_xz(guard, -6, 6)

    # Rear sight: a V-notched block on top of the receiver.
    sight = rect(-7, 7, FRAME_TOP_Z - 1, FRAME_TOP_Z + 4) - poly((-3.2, FRAME_TOP_Z + 4.2), (0, FRAME_TOP_Z + 1), (3.2, FRAME_TOP_Z + 4.2))
    body += prism_yz(sight, 6, 16)

    # Square boss that keys the recoil shield and carries the drum axle.
    body += box(SHIELD_X0 - 1, SHIELD_X1, -6, 6, AXLE_Z - 6, AXLE_Z + 6)

    # Shroud locating boss and anti-rotation key on the front face.
    body += xcyl(SPIGOT_R, FRAME_X1 - 1, FRAME_X1 + BOSS_LEN)
    body += box(FRAME_X1 - 1, FRAME_X1 + 4, -2.8, 2.8, -(SHROUD_R_OUT - 0.2), -(SHROUD_R_IN - 1.0))

    # Raised medallion on each side of the rear block.
    medallion = (
        Circle(26) - Circle(23) + Rot(0, 0, 90) * cross_sketch(36, 24, 6.5)
    )
    medallion = Pos(38, -12) * medallion
    body += prism_xz(medallion, w - 0.5, w + 1.2)
    body += prism_xz(medallion, -w - 1.2, -w + 0.5)

    # --- pockets -----------------------------------------------------------
    cuts = []
    cuts.append(xcyl(BARREL_R + FIT, BARREL_X0, FRAME_X1 + BOSS_LEN + 1))        # barrel socket
    cuts.append(xcyl(ROD_R + FIT, SPINE_X0, BARREL_X0 + 1))                      # spine rod pocket
    cuts.append(xcyl(ROD_R + FIT, REAR_BLOCK_X1 - 10, SHIELD_X1 + 1, z=AXLE_Z))  # axle, rear
    cuts.append(xcyl(ROD_R + FIT, BAY_X1 - 1, BAY_X1 + 10, z=AXLE_Z))            # axle, front
    cuts.append(box(3.7, 30.3, -5.2, 5.2, FRAME_BOT_Z - 1, -37.7))               # grip tongue pocket

    px, pz = TRIGGER_PIVOT
    cavity = Pos(px, pz) * Circle(6.2) + rect(px - 7.6, px + 2.4, FRAME_BOT_Z - 1, pz)
    cuts.append(prism_xz(cavity, -(TRIGGER_HALF_W + 0.3), TRIGGER_HALF_W + 0.3))
    cuts.append(xcyl(2.6, 34, px - 7.5, z=pz - 6.5))                             # pen-spring channel

    for x, z in FRAME_SCREWS + GRIP_TONGUE_SCREWS + [TRIGGER_PIVOT]:
        cuts.append(ycyl(SCREW_CLEAR_R, -w - 2, 0, x, z))
        cuts.append(ycyl(SCREW_HEAD_R, -w - 2, -w + SCREW_HEAD_DEPTH, x, z))
        cuts.append(ycyl(SCREW_TAP_R, 0, 14, x, z))
    for c in cuts:
        body -= c

    # --- inscriptions ------------------------------------------------------
    text_z = (STRAP_BOT_Z + FRAME_TOP_Z) / 2
    left_plane = Plane(origin=(98, w, text_z), x_dir=(-1, 0, 0), z_dir=(0, 1, 0))
    right_plane = Plane(origin=(90, -w, text_z), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    for plane, label in ((left_plane, TEXT_LEFT), (right_plane, TEXT_RIGHT)):
        txt = Text(label, font_size=TEXT_SIZE, font=TEXT_FONT, font_style=FontStyle.BOLD)
        body -= extrude(plane * txt, amount=-TEXT_DEPTH)
    return body


def split_frame(full):
    left = full & box(-100, 400, 0, 100, -300, 300)
    right = full & box(-100, 400, -100, 0, -300, 300)
    return left, right


def trigger():
    px, pz = TRIGGER_PIVOT
    t = prism_xz(trigger_sketch(), -TRIGGER_HALF_W, TRIGGER_HALF_W)
    t -= ycyl(SCREW_CLEAR_R + 0.1, -10, 10, px, pz)
    t -= xcyl(2.5, px - 7, px - 3.5, z=pz - 6.5)  # seat for the return spring
    return t


def grip_full():
    """Pistol grip with a tongue that is clamped between the frame halves."""
    rake = math.tan(math.radians(15))

    def section(z, a, b):
        cx = 18 + (z - FRAME_BOT_Z) * rake  # z is negative below the frame, so the grip sweeps back
        return Pos(cx, 0, z) * Ellipse(a, b)

    sections = [
        section(FRAME_BOT_Z, 18.0, 13.0),
        section(-95, 19.5, 14.5),
        section(-135, 20.5, 14.0),
        section(-160, 22.0, 15.0),
        section(-166, 24.0, 16.5),
    ]
    body = loft(sections)
    # Finger grooves along the front strap.
    for z in (-82, -104, -126):
        cx = 18 + (z - FRAME_BOT_Z) * rake
        body -= ycyl(10, -30, 30, cx + 20 + 7.6, z)
    # Tongue.
    body += box(4, 30, -5, 5, FRAME_BOT_Z - 2, -38)
    for x, z in GRIP_TONGUE_SCREWS:
        body -= ycyl(SCREW_CLEAR_R, -10, 10, x, z)
    for x, z in GRIP_BODY_SCREWS:
        body -= ycyl(SCREW_CLEAR_R, -30, 0, x, z)
        body -= ycyl(SCREW_HEAD_R, -30, -9.0, x, z)
        body -= ycyl(SCREW_TAP_R, 0, 12, x, z)
    return body


def split_grip(full):
    left = full & box(-200, 200, 0, 100, -300, 100)
    right = full & box(-200, 200, -100, 0, -300, 100)
    return left, right


# --------------------------------------------------------------------------
# Drum, shield and shells
# --------------------------------------------------------------------------


def chamber_centres():
    out = []
    for k in range(N_CHAMBERS):
        a = math.radians(k * 360 / N_CHAMBERS)
        out.append((DRUM_PITCH_R * math.sin(a), AXLE_Z + DRUM_PITCH_R * math.cos(a)))
    return out


def recoil_shield():
    r = DRUM_R + 2.0
    sk = Pos(0, AXLE_Z) * Circle(r)
    sk &= rect(-100, 100, AXLE_Z - 100, STRAP_BOT_Z - 0.2)
    sk -= Pos(0, AXLE_Z) * Rectangle(12.4, 12.4)
    # Loading gate on the right-hand side.
    sk -= Pos(-DRUM_PITCH_R, AXLE_Z) * Circle(SHELL_RIM_R + 0.6)
    sk -= rect(-100, -DRUM_PITCH_R, AXLE_Z - (SHELL_RIM_R + 0.6), AXLE_Z + (SHELL_RIM_R + 0.6))
    return prism_yz(sk, SHIELD_X0, SHIELD_X1)


def drum():
    d = xcyl(DRUM_R, DRUM_X0, DRUM_X1, z=AXLE_Z)
    d = chamfer(d.edges().filter_by(lambda e: e.length > 2 * math.pi * DRUM_R * 0.99), 1.5)
    d -= xcyl(ROD_R + SLIDE, DRUM_X0 - 1, DRUM_X1 + 1, z=AXLE_Z)
    for y, z in chamber_centres():
        d -= xcyl(CHAMBER_R, DRUM_X0 - 1, DRUM_X1 - DRUM_FRONT_WALL, y, z)
        d -= xcyl(SHELL_RIM_R + 0.35, DRUM_X0 - 1, DRUM_X0 + SHELL_RIM_T + 0.2, y, z)
        d -= xcyl(7.0, DRUM_X1 - DRUM_FRONT_WALL - 1, DRUM_X1 + 1, y, z)
    # Flutes between chambers.  They open at the front face (the print bed)
    # and close with a 45 degree cone so no support is needed.
    flute_r, flute_c = 9.0, DRUM_R + 5.5
    for k in range(N_CHAMBERS):
        a = math.radians((k + 0.5) * 360 / N_CHAMBERS)
        y, z = flute_c * math.sin(a), AXLE_Z + flute_c * math.cos(a)
        d -= xcyl(flute_r, DRUM_X0 + 30, DRUM_X1 + 1, y, z)
        d -= xcone(0, flute_r, DRUM_X0 + 30 - flute_r, DRUM_X0 + 30, y, z)
    return d


def shell():
    """Dummy shell, modelled in the top chamber."""
    x0 = DRUM_X0
    x1 = DRUM_X1 - DRUM_FRONT_WALL - 0.2
    s = xcyl(SHELL_RIM_R, x0, x0 + SHELL_RIM_T) + xcyl(SHELL_R, x0 + SHELL_RIM_T - 0.1, x1)
    front_edge = s.edges().filter_by(lambda e: abs(e.center().X - x1) < 1e-3)
    s = chamfer(front_edge, 1.5)
    # Engraved cross on the slug nose, primer ring on the base.
    nose = Plane(origin=(x1, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    s -= extrude(nose * (Rot(0, 0, 90) * cross_sketch(9, 6.5, 1.8)), amount=-0.8)
    s -= xcyl(3.4, x0 - 1, x0 + 0.5) - xcyl(2.6, x0 - 1, x0 + 0.5)
    return s


# --------------------------------------------------------------------------
# Barrel and shroud
# --------------------------------------------------------------------------


def barrel_rear():
    return xcyl(BARREL_R, BARREL_X0, BARREL_SPLIT_X) - xcyl(ROD_R + FIT + 0.05, BARREL_X0 - 1, BARREL_SPLIT_X + 1)


def barrel_front():
    b = xcyl(BARREL_R, BARREL_SPLIT_X, MUZZLE_X)
    b = chamfer(b.edges().filter_by(lambda e: abs(e.center().X - MUZZLE_X) < 1e-3), 1.0)
    b -= xcyl(ROD_R + FIT + 0.05, BARREL_SPLIT_X - 1, SPINE_X1)
    b -= xcone(ROD_R + FIT + 0.05, 0, SPINE_X1, SPINE_X1 + 4)   # self-supporting end of the rod pocket
    b -= xcyl(8.0, MUZZLE_X - 6, MUZZLE_X + 1)                   # shallow recess that reads as a bore
    return b


def _vent_cutters(stations, staggered):
    """Cross-shaped vents: rows on both sides plus two lower diagonal rows."""
    cross = cross_sketch(26, 14, 5, gusset=2.5)
    proto = extrude(Pos(0, 0, SHROUD_R_IN - 4) * cross, amount=10)  # pierces the wall at the top
    out = []
    for ang in (90, 270):
        for x in stations:
            out.append(Pos(x, 0, 0) * Rot(ang, 0, 0) * proto)
    for ang in (142, 218):
        for x in staggered:
            out.append(Pos(x, 0, 0) * Rot(ang, 0, 0) * proto)
    return out


def _shroud_segment(x0, x1, cap_x1):
    """Tube from x0 to x1 with the top rib, a decorative band at x1 and an
    internal 45 degree shoulder that centres the barrel.  cap_x1 is where the
    reduced-diameter nose beyond the band ends."""
    rib = box(x0, x1, -RIB_HALF_W, RIB_HALF_W, SHROUD_R_IN - 0.5, RIB_TOP_Z)
    seg = xcyl(SHROUD_R_OUT, x0, x1) + rib
    seg += xcyl(BAND_R, x1 - 4, x1) + xcone(SHROUD_R_OUT, BAND_R, x1 - 6, x1 - 4)
    seg -= xcyl(SHROUD_R_IN, x0 - 1, x1 - 10.3)
    shoulder = SHROUD_R_IN - (BARREL_R + 0.2)
    seg -= xcone(SHROUD_R_IN, BARREL_R + 0.2, x1 - 10.3, x1 - 10.3 + shoulder)
    seg += xcyl(SPIGOT_R, x1, cap_x1)
    seg -= xcyl(BARREL_R + 0.2, x0 - 1, cap_x1 + 1)
    # Key notch at the rear end.
    seg -= box(x0 - 1, x0 + 4.4, -3.05, 3.05, -(SHROUD_R_OUT + 1), -(SHROUD_R_IN - 1.5))
    return seg


def shroud_rear():
    x0, x1 = SHROUD_X0, SHROUD_SPLIT_X
    seg = _shroud_segment(x0, x1, x1 + SPIGOT_LEN)
    # Key tab on the spigot for the front segment.
    seg += box(x1, x1 + 4, -2.8, 2.8, -(SHROUD_R_OUT - 0.2), -(SPIGOT_R - 0.5))
    for c in _vent_cutters([x0 + 24 + 34 * k for k in range(4)], [x0 + 41 + 34 * k for k in range(3)]):
        seg -= c
    return seg


def shroud_front():
    x0, x1 = SHROUD_SPLIT_X, SHROUD_X1
    seg = _shroud_segment(x0, x1, x1 + 4)
    nose_edge = seg.edges().filter_by(
        lambda e: abs(e.center().X - (x1 + 4)) < 1e-3 and e.length > 2 * math.pi * (SPIGOT_R - 0.5)
    )
    seg = chamfer(nose_edge, 1.5)
    for c in _vent_cutters([x0 + 24 + 34 * k for k in range(4)], [x0 + 41 + 34 * k for k in range(3)]):
        seg -= c
    # Notch for the crossbar; chamfered ends keep it printable upright.
    notch = poly((436.3, RIB_TOP_Z + 0.2), (440, 22.5), (452, 22.5), (455.7, RIB_TOP_Z + 0.2))
    seg -= prism_xz(notch, -RIB_HALF_W - 1, RIB_HALF_W + 1)
    # Slot for the front sight.
    seg -= box(485.85, 489.15, -1.95, 1.95, 22.0, RIB_TOP_Z + 1)
    return seg


def crossbar():
    sk = Rectangle(11.6, 96) + Pos(0, 48) * Circle(8) + Pos(0, -48) * Circle(8)
    bar = extrude(Pos(446, 0, 22.5) * sk, amount=7)
    top = bar.edges().filter_by(lambda e: abs(e.center().Z - 29.5) < 1e-3)
    return chamfer(top, 1.2)


def front_sight():
    sk = rect(-1.75, 1.75, 22.2, 44) + rect(-6, 6, 35, 38.5)
    return prism_yz(sk, 486, 489)


def muzzle_crown():
    x0, x1 = 530.0, MUZZLE_X
    c = xcyl(15.0, x0, x1) + xcyl(16.5, x0 + 4, x0 + 8)
    c += xcone(15.0, 16.5, x0 + 2.5, x0 + 4) + xcone(16.5, 15.0, x0 + 8, x0 + 9.5)
    c = chamfer(c.edges().filter_by(lambda e: abs(e.center().X - x1) < 1e-3), 1.2)
    c -= xcyl(BARREL_R + FIT, x0 - 1, x1 + 1)
    cross = cross_sketch(15, 9, 3.2, gusset=1.2)
    proto = extrude(Pos(0, 0, BARREL_R - 2) * cross, amount=10)
    for ang in (0, 90, 180, 270):
        c -= Pos(x1 - 10.5, 0, 0) * Rot(ang, 0, 0) * proto
    return c


# --------------------------------------------------------------------------
# Torch, fore grip and Dragon's Breath
# --------------------------------------------------------------------------


def torch():
    x0, x1, z = TORCH_X0, TORCH_X1, TORCH_Z
    t = xcyl(13, x0, x0 + 12, z=z) + xcyl(12, x0 + 11, x1 - 27, z=z)
    t += xcone(12, 15, x1 - 27, x1 - 24, z=z) + xcyl(15, x1 - 24, x1, z=z)
    for gx in (x0 + 3, x0 + 6, x0 + 9):                       # grip rings on the tail cap
        t -= xcyl(14, gx, gx + 1.2, z=z) - xcyl(12.4, gx - 1, gx + 2.2, z=z)
    t -= xcyl(12.5, x1 - 2.5, x1 + 1, z=z)                     # lens seat
    t -= xcone(4, 12.5, x1 - 12, x1 - 2.5, z=z)                # reflector
    t -= box(x0 - 1, x1 + 1, -(RIB_HALF_W + 0.2), RIB_HALF_W + 0.2, 0, RIB_TOP_Z + 0.2)  # sits on the rib
    return t


def foregrip_collar():
    ring = Circle(SHROUD_R_OUT + 4.5) - Circle(SHROUD_R_OUT + 0.2)
    ring -= rect(-(RIB_HALF_W + 0.3), RIB_HALF_W + 0.3, 0, 40)
    tenon = poly((-6, -23), (6, -23), (9, -30.5), (-9, -30.5))
    return prism_yz(ring + tenon - Circle(SHROUD_R_OUT + 0.2), FOREGRIP_X0, FOREGRIP_X1)


def foregrip_handle():
    xc = (FOREGRIP_X0 + FOREGRIP_X1) / 2
    top_z, bot_z = -25.0, -125.0
    body = extrude(Pos(xc, 0, bot_z + 8) * RectangleRounded(34, 28, 10), amount=top_z - bot_z - 8)
    body += loft([
        Pos(xc, 0, bot_z) * RectangleRounded(38, 32, 12),
        Pos(xc, 0, bot_z + 8) * RectangleRounded(34, 28, 10),
    ])
    for z in (-50, -72, -94):
        body -= ycyl(9, -30, 30, xc + 17 + 5.6, z)
    slot = poly((-6.25, -23), (6.25, -23), (9.37, -30.8), (-9.37, -30.8))
    body -= prism_yz(slot, FOREGRIP_X0 - 5, FOREGRIP_X1 + 5)
    return body


def dragon_tube():
    x0, x1, z, r = DRAGON_X0, DRAGON_X1, DRAGON_Z, DRAGON_R
    t = xcyl(13, x0, x0 + 8, z=z) + xcyl(r, x0 + 7, x1 - 32, z=z)
    t += xcone(r, 7, x1 - 32, x1 - 24, z=z) + xcyl(7, x1 - 24, x1 - 6, z=z)
    t += xcone(7, 8.5, x1 - 7.5, x1 - 6, z=z) + xcyl(8.5, x1 - 6, x1, z=z)
    for gx in (x0 + 2, x0 + 5):
        t -= xcyl(14, gx, gx + 1.2, z=z) - xcyl(12.3, gx - 1, gx + 2.2, z=z)
    t -= xcyl(4.5, x1 - 8, x1 + 1, z=z)                        # nozzle recess
    return t


def dragon_cradle(x0):
    """Double C-clip: snaps onto the shroud above and holds the tube below."""
    def c_clip(centre_z, r_in, wall, open_dir, half_open_deg):
        ring = Pos(0, centre_z) * (Circle(r_in + wall) - Circle(r_in))
        a = math.radians(half_open_deg)
        far = 80
        wedge = poly(
            (0, centre_z),
            (far * math.sin(a), centre_z + open_dir * far * math.cos(a)),
            (0, centre_z + open_dir * far * 1.6),
            (-far * math.sin(a), centre_z + open_dir * far * math.cos(a)),
        )
        ring -= wedge
        rm = r_in + wall / 2
        for s in (-1, 1):  # rounded lead-in on the tips
            ring += Pos(s * rm * math.sin(a), centre_z + open_dir * rm * math.cos(a)) * Circle(wall / 2)
        return ring

    upper = c_clip(0, SHROUD_R_OUT + 0.1, 3.0, +1, 65)
    lower = c_clip(DRAGON_Z, DRAGON_R + 0.1, 3.0, -1, 60)
    web = rect(-9, 9, DRAGON_Z + DRAGON_R, -SHROUD_R_OUT)
    sk = upper + lower + web
    sk -= Circle(SHROUD_R_OUT + 0.1)
    sk -= Pos(0, DRAGON_Z) * Circle(DRAGON_R + 0.1)
    return prism_yz(sk, x0, x0 + 14)


# --------------------------------------------------------------------------
# Hardware shown in the assembly (not printed)
# --------------------------------------------------------------------------


def spine_rod():
    return xcyl(ROD_R, SPINE_X0 + 0.5, SPINE_X1 - 0.5)


def axle_rod():
    return xcyl(ROD_R, REAR_BLOCK_X1 - 9.5, BAY_X1 + 9.5, z=AXLE_Z)


# --------------------------------------------------------------------------
# Part registry
# --------------------------------------------------------------------------

REAR_DOWN = Rot(0, -90, 0)   # +X of the prop points up on the bed
FRONT_DOWN = Rot(0, 90, 0)   # -X of the prop points up on the bed
LEFT_HALF = Rot(90, 0, 0)    # split face on the bed, outer (+Y) face up
RIGHT_HALF = Rot(-90, 0, 0)  # split face on the bed, outer (-Y) face up
AS_IS = Rot(0, 0, 0)


@dataclass
class PropPart:
    name: str
    solid: Part
    print_rot: Location = AS_IS
    color: tuple = BRASS
    filament: str = "brass / gold"
    printed: bool = True
    placements: list = field(default_factory=lambda: [Location()])
    explode: tuple = (0.0, 0.0, 0.0)   # offset direction * distance for the exploded view
    notes: str = ""

    @property
    def qty(self):
        return len(self.placements)


def build_parts():
    frame_l, frame_r = split_frame(frame_full())
    grip_l, grip_r = split_grip(grip_full())
    shell_spots = [about_axle(-k * 360 / N_CHAMBERS) for k in range(N_CHAMBERS)]
    parts = [
        PropPart("frame_left", frame_l, LEFT_HALF, BRASS, explode=(0, 90, 0),
                 notes="Split face on the bed, engraving up. No supports."),
        PropPart("frame_right", frame_r, RIGHT_HALF, BRASS, explode=(0, -90, 0),
                 notes="Split face on the bed, engraving up. No supports."),
        PropPart("grip_left", grip_l, LEFT_HALF, WOOD, "wood / dark brown", explode=(-60, 30, -70),
                 notes="Split face on the bed."),
        PropPart("grip_right", grip_r, RIGHT_HALF, WOOD, "wood / dark brown", explode=(-60, -30, -70),
                 notes="Split face on the bed."),
        PropPart("trigger", trigger(), LEFT_HALF, STEEL, "black / steel", explode=(0, 0, -75),
                 notes="Flat on its side."),
        PropPart("recoil_shield", recoil_shield(), REAR_DOWN, STEEL, "black / steel", explode=(-35, 0, 0),
                 notes="Flat."),
        PropPart("drum", drum(), FRONT_DOWN, STEEL, "black / steel", explode=(0, 0, 0),
                 notes="Front face on the bed so the chambers open upward."),
        PropPart("shell", shell(), REAR_DOWN, GOLD, "gold", placements=shell_spots, explode=(-120, 0, 0),
                 notes="Rim on the bed. Print 12."),
        PropPart("barrel_rear", barrel_rear(), REAR_DOWN, STEEL, "black / steel", explode=(60, 0, 140),
                 notes="Upright, use a brim."),
        PropPart("barrel_front", barrel_front(), REAR_DOWN, STEEL, "black / steel", explode=(150, 0, 140),
                 notes="Upright, muzzle up, use a brim."),
        PropPart("shroud_rear", shroud_rear(), REAR_DOWN, BRASS, explode=(60, 0, 0),
                 notes="Upright, frame end on the bed."),
        PropPart("shroud_front", shroud_front(), REAR_DOWN, BRASS, explode=(150, 0, 0),
                 notes="Upright, banded nose up."),
        PropPart("crossbar", crossbar(), AS_IS, BRASS, explode=(150, 0, 45), notes="Flat."),
        PropPart("front_sight", front_sight(), FRONT_DOWN, BRASS, explode=(150, 0, 75), notes="Flat on its back."),
        PropPart("muzzle_crown", muzzle_crown(), REAR_DOWN, BRASS, explode=(240, 0, 0), notes="Upright."),
        PropPart("torch", torch(), REAR_DOWN, STEEL, "black / steel", explode=(60, 0, 55),
                 notes="Upright, tail cap on the bed."),
        PropPart("foregrip_collar", foregrip_collar(), REAR_DOWN, BRASS, explode=(60, 0, -35), notes="Ring flat on the bed."),
        PropPart("foregrip_handle", foregrip_handle(), AS_IS, WOOD, "wood / dark brown", explode=(60, 0, -95),
                 notes="Upright, pommel on the bed."),
        PropPart("dragon_tube", dragon_tube(), REAR_DOWN, GOLD, "gold", explode=(150, 0, -110),
                 notes="Upright, knurled cap on the bed, use a brim."),
        PropPart("dragon_cradle", dragon_cradle(316), REAR_DOWN, BRASS,
                 placements=[Location(), Pos(130, 0, 0)], explode=(150, 0, -50),
                 notes="Flat. Print 2."),
        PropPart("spine_rod", spine_rod(), AS_IS, HARDWARE, printed=False, explode=(105, 0, 190),
                 notes="8 mm rod, 380 mm long."),
        PropPart("axle_rod", axle_rod(), AS_IS, HARDWARE, printed=False, explode=(0, 0, -140),
                 notes="8 mm rod, 88 mm long."),
    ]
    return parts
