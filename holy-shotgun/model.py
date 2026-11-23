"""Parametric model of a relic-style "holy shotgun" display prop.

A non-functional costume/display piece modelled on the crucifix shotgun in
the film Constantine (2005).  Nothing here can chamber or fire anything: the
barrel is a hollow sleeve over a solid rod, the drum is a free-spinning
ornament, and the shells are solid dummies.

Coordinate system for the assembled prop (millimetres):
    X  runs along the barrel, muzzle at +X, rear face of the drum at X=0
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
    FontStyle,
    Line,
    Location,
    Part,
    Plane,
    Polygon,
    Pos,
    Rectangle,
    RegularPolygon,
    Rot,
    SlotOverall,
    Solid,
    Spline,
    Text,
    chamfer,
    extrude,
    fillet,
    make_face,
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
ROD_R = 4.0          # 8 mm rod: barrel spine, cross spine and drum axle
SCREW_CLEAR_R = 1.7  # M3 clearance hole
SCREW_TAP_R = 1.4    # M3 self-tapping pilot (2.8 mm)
SCREW_HEAD_R = 3.2   # M3 socket-head counterbore
SCREW_HEAD_DEPTH = 3.2

# Drum: an open cage of two flanges on a hub, twelve exposed dummy shells.
# Striker style, so the top chamber lines up with the barrel.
N_CHAMBERS = 12
DRUM_PITCH_R = 43.5
AXLE_Z = -DRUM_PITCH_R
DRUM_R = 56.0
DRUM_X0, DRUM_X1 = 0.0, 64.0
DRUM_REAR_T = 8.0        # rear flange thickness
DRUM_FRONT_T = 12.0      # front flange thickness
DRUM_HUB_R = 30.0
DRUM_HEX_AF = 44.0       # hex spigot that keys the rear flange to the hub
SHELL_R = 9.5
SHIELD_X0, SHIELD_X1 = -4.5, -0.5

# Receiver, printed as left/right halves split on Y=0.
RECV_HALF_W = 18.0
RECV_X0 = -26.0          # rear face, where the grip bolts on
RECV_X1 = 104.0          # front face, where the barrel starts
RECV_TOP_Z = 23.5
RECV_BOT_Z = -66.0
STRAP_BOT_Z = 13.5
HOOD_R_IN, HOOD_R_OUT = 57.2, 67.0   # curved hood over the drum, measured from the axle
HOOD_HALF_W = 38.0

# Grip.
GRIP_HALF_W = 17.0

# Crucifix barrel: octagonal sleeves joined by a hub, all threaded on 8 mm rod.
OCT_AF = 34.0            # across flats
CAV_R = 14.2             # hollow interior of the sleeves
TENON_AF = 24.0
TENON_LEN = 12.0
MORTISE_DEPTH = TENON_LEN + 0.4
SPINE_Z = 4.5            # the two rods cross in the hub, so one rides high
CROSS_Z = -4.5           # and the other low
TAIL_LEN = 190.0         # receiver to hub
HUB_X0, HUB_X1 = RECV_X1 + TAIL_LEN, RECV_X1 + TAIL_LEN + 44.0
HUB_XC = (HUB_X0 + HUB_X1) / 2
HUB_HALF_Y = 32.0
HEAD_LEN = 90.0          # hub to muzzle cap
ARM_LEN = 68.0           # hub to arm cap
CAP_R = 19.5
CAP_LEN = 12.0
MUZZLE_X = HUB_X1 + HEAD_LEN + CAP_LEN

# Torch (the scope-like tube on top) and its pedestal.
TORCH_Z = 46.0
TORCH_X0, TORCH_X1 = 112.0, 302.0
PEDESTAL_X0, PEDESTAL_X1 = 180.0, 226.0

# Dragon's Breath tube and the twisted rod that runs back to the receiver.
DRAGON_Z = -34.0
DRAGON_R = 12.0
DRAGON_X0, DRAGON_X1 = 288.0, 412.0
TWIST_SOCKET_R = 5.95  # the twisted rod is 11.4 mm across

# Inscriptions, as far as they can be read from photos of the film prop.
TEXT_FONT = "DejaVu Serif"
TEXT_DEPTH = 0.7
TEXT_TAIL_RIGHT = "QUI DESIDERAT PACEM"
TEXT_TAIL_LEFT = "BREVE ET EFFICAX PER EXEMPLA"
TEXT_HEAD_RIGHT = "PATER IN MANUS TUAS"
TEXT_HEAD_LEFT = "COMMENDO SPIRITUM"

# Screws (X, Z).  M3 x 30 through the receiver, heads on the right-hand side.
RECV_SCREWS = [(-18, 15.5), (72, 15.5), (74, -20), (92, -50), (96, -12)]  # all clear of the hood
TONGUE_SCREWS = [(-17, 4), (-17, -24)]
TRIGGER_SCREW = (-14, -59)
GRIP_SCREWS = [(-66, -10), (-93, -84), (-104, -150)]  # M3 x 20

# Colours used for previews and as a filament suggestion.
BRASS = (0.78, 0.62, 0.25)
SILVER = (0.72, 0.74, 0.77)
HARDWARE = (0.45, 0.47, 0.50)

# --------------------------------------------------------------------------
# Small geometry helpers
# --------------------------------------------------------------------------


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


def octagon(af):
    """Octagon with flats on the top, bottom and sides."""
    return RegularPolygon(af / 2, 8, major_radius=False, rotation=22.5)


def oct_x(af, x0, x1, z=0.0):
    """Octagonal prism along X."""
    return prism_yz(Pos(0, z) * octagon(af), x0, x1)


def oct_y(af, y0, y1, x=0.0):
    """Octagonal prism along Y."""
    return prism_xz(Pos(x, 0) * octagon(af), y0, y1)


def cross_sketch(length, width, bar, arm_pos=0.3):
    """Latin cross, long axis on local x with the head at +x."""
    cx = length / 2 - arm_pos * length
    return Rectangle(length, bar) + Pos(cx, 0) * Rectangle(bar, width)


def cross_pattee(size, waist=0.22):
    """Cross with arms that flare toward the tips."""
    h, w = size / 2, size * waist / 2
    arm = poly((0, w), (h, h * 0.62), (h, -h * 0.62), (0, -w))
    sk = Rectangle(2 * w, 2 * w)
    for a in (0, 90, 180, 270):
        sk += Rot(0, 0, a) * arm
    return sk


def fitted_text(label, max_len, size):
    """Bold text, shrunk if needed so it is no longer than max_len."""
    txt = Text(label, font_size=size, font=TEXT_FONT, font_style=FontStyle.BOLD)
    width = txt.bounding_box().size.X
    if width > max_len:
        txt = Text(label, font_size=size * max_len / width, font=TEXT_FONT, font_style=FontStyle.BOLD)
    return txt


def about_axle(angle_deg):
    """Location that rotates about the drum axle by angle_deg."""
    return Pos(0, 0, AXLE_Z) * Rot(angle_deg, 0, 0) * Pos(0, 0, -AXLE_Z)


def spiral_band(cx, cz, r_max, turns, width, start_deg=0.0, hand=1):
    """A scroll: a tapering band along an Archimedean spiral, as an (X, Z) sketch."""
    r_min = 2.5
    n = int(turns * 14)
    inner, outer = [], []
    for i in range(n + 1):
        t = i / n
        r = r_min + (r_max - r_min) * t
        a = math.radians(start_deg) + hand * 2 * math.pi * turns * t
        half = width / 2 * (0.5 + 0.5 * t)
        inner.append((cx + (r - half) * math.cos(a), cz + (r - half) * math.sin(a)))
        outer.append((cx + (r + half) * math.cos(a), cz + (r + half) * math.sin(a)))
    return make_face([
        Spline(*outer), Line(outer[-1], inner[-1]), Spline(*inner[::-1]), Line(inner[0], outer[0]),
    ])


# --------------------------------------------------------------------------
# Receiver, trigger and grip
# --------------------------------------------------------------------------


def receiver_full():
    """The whole receiver before it is split into halves: a rear plate behind
    the drum, a strap over it and a block in front that carries the barrel."""
    w = RECV_HALF_W
    outline = poly(
        (RECV_X0, RECV_BOT_Z),
        (SHIELD_X0, RECV_BOT_Z),
        (SHIELD_X0, STRAP_BOT_Z),
        (DRUM_X1 + 0.5, STRAP_BOT_Z),
        (DRUM_X1 + 0.5, -64),
        (86, -64),
        (RECV_X1, -46),
        (RECV_X1, 19),
        (99, RECV_TOP_Z),
        (RECV_X0, RECV_TOP_Z),
    )
    body = prism_xz(outline, -w, w)
    body = chamfer(body.edges().filter_by(lambda e: abs(abs(e.center().Y) - w) < 1e-6), 2.0)

    # Hood: a curved fender over the top of the drum, concentric with it.
    hood = Pos(0, AXLE_Z) * (Circle(HOOD_R_OUT) - Circle(HOOD_R_IN)) & rect(-HOOD_HALF_W, HOOD_HALF_W, 0, 40)
    body += prism_yz(hood, -12, DRUM_X1 + 0.5)
    # Crown the whole top to the same curve.
    body &= xcyl(HOOD_R_OUT, RECV_X0 - 1, RECV_X1 + 1, z=AXLE_Z) + box(RECV_X0 - 1, RECV_X1 + 1, -60, 60, -120, 0)

    # Square boss that keys the recoil shield and carries the drum axle.
    body += box(SHIELD_X0 - 1, SHIELD_X1, -6, 6, AXLE_Z - 6, AXLE_Z + 6)
    # Tenon for the rear barrel sleeve.
    body += oct_x(TENON_AF, RECV_X1 - 1, RECV_X1 + TENON_LEN)

    cuts = [
        xcyl(ROD_R + FIT, 84, RECV_X1 + TENON_LEN + 1, z=SPINE_Z),          # barrel spine
        xcyl(ROD_R + FIT, -15, SHIELD_X1 + 1, z=AXLE_Z),                     # axle, rear
        xcyl(ROD_R + FIT, DRUM_X1 + 0.4, 76, z=AXLE_Z),                      # axle, front
        xcyl(TWIST_SOCKET_R, 94, RECV_X1 + 1, z=DRAGON_Z),                   # twisted rod socket
        box(RECV_X0 - 1, -7.8, -5.2, 5.2, -34.3, 12.3),                      # grip tongue pocket
        box(-20, -8, -4.2, 4.2, RECV_BOT_Z - 1, -52),                        # trigger pocket
    ]
    for x, z in RECV_SCREWS + TONGUE_SCREWS + [TRIGGER_SCREW]:
        cuts.append(ycyl(SCREW_CLEAR_R, -w - 1, 0, x, z))
        cuts.append(ycyl(SCREW_HEAD_R, -w - 1, -w + SCREW_HEAD_DEPTH, x, z))
        cuts.append(ycyl(SCREW_TAP_R, 0, 16, x, z))
    for c in cuts:
        body -= c

    # Engraved medallion on each side of the front block.
    medallion = Pos(83, -34) * (Circle(12) - Circle(10.6) + cross_pattee(15))
    body -= prism_xz(medallion, w - TEXT_DEPTH, w + 1)
    body -= prism_xz(medallion, -w - 1, -w + TEXT_DEPTH)
    return body


def split_halves(full):
    left = full & box(-400, 600, 0, 200, -400, 400)
    right = full & box(-400, 600, -200, 0, -400, 400)
    return left, right


def trigger():
    """A fixed spur trigger, pinned in the receiver by one screw."""
    sk = poly(
        (-19.7, -52.3), (-8.3, -52.3), (-8.3, -66), (-7.6, -74), (-9.2, -84), (-12.0, -92),
        (-15.0, -92), (-15.6, -82), (-17.6, -74), (-19.7, -66),
    )
    t = prism_xz(sk, -4.0, 4.0)
    x, z = TRIGGER_SCREW
    return t - ycyl(SCREW_CLEAR_R, -10, 10, x, z)


def grip_outline():
    back = [
        (RECV_X0, RECV_TOP_Z), (-46, 22.5), (-68, 15), (-88, -1), (-104, -26), (-116, -60),
        (-127, -96), (-137, -128), (-141, -150), (-135, -166), (-120, -172), (-104, -166),
        (-94, -150), (-86, -124), (-76, -100), (-62, -82), (-46, -71), (RECV_X0, RECV_BOT_Z),
    ]
    return make_face([Spline(*back), Line(back[-1], back[0])])


def grip_full():
    """Bird's-head grip with a tongue that is clamped between the receiver halves."""
    w = GRIP_HALF_W
    body = prism_xz(grip_outline(), -w, w)
    side_edges = body.edges().filter_by(lambda e: abs(abs(e.center().Y) - w) < 1e-6 and e.center().X < RECV_X0 - 2)
    body = fillet(side_edges, 6.0)

    # Scrollwork, engraved on both faces.
    scrolls = [
        (-54, 2, 15, 2.1, 200, 1), (-80, -26, 13, 2.0, 30, -1), (-52, -44, 12, 1.9, 120, 1),
        (-98, -62, 12, 2.0, 250, 1), (-76, -72, 8, 1.6, 0, -1), (-110, -102, 12, 2.0, 60, -1),
        (-118, -136, 12, 2.0, 220, 1), (-118, -160, 6, 1.4, 90, -1),
    ]
    for cx, cz, r, turns, start, hand in scrolls:
        band = spiral_band(cx, cz, r, turns, 2.0, start, hand)
        body -= prism_xz(band, w - TEXT_DEPTH, w + 1)
        body -= prism_xz(band, -w - 1, -w + TEXT_DEPTH)

    body += box(RECV_X0 - 1, -8, -5, 5, -34, 12)                 # tongue
    for x, z in TONGUE_SCREWS:
        body -= ycyl(SCREW_CLEAR_R, -10, 10, x, z)
    for x, z in GRIP_SCREWS:
        body -= ycyl(SCREW_CLEAR_R, -w - 1, 0, x, z)
        body -= ycyl(SCREW_HEAD_R, -w - 1, -11.0, x, z)
        body -= ycyl(SCREW_TAP_R, 0, 11, x, z)
    return body


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
    """Fixed plate behind the drum.  It keeps the shells in; they load through
    the gate on the right-hand side."""
    sk = Pos(0, AXLE_Z) * Circle(DRUM_R + 0.6)
    sk &= rect(-100, 100, AXLE_Z - 100, STRAP_BOT_Z - 0.2)
    sk -= Pos(0, AXLE_Z) * Rectangle(12.4, 12.4)
    gate = SHELL_R + 0.6
    sk -= Pos(-DRUM_PITCH_R, AXLE_Z) * Circle(gate)
    sk -= rect(-100, -DRUM_PITCH_R, AXLE_Z - gate, AXLE_Z + gate)
    return prism_yz(sk, SHIELD_X0, SHIELD_X1)


def drum_core():
    """Front flange, hub and the hex spigot the rear flange slides onto."""
    front_x = DRUM_X1 - DRUM_FRONT_T
    d = xcyl(DRUM_R, front_x, DRUM_X1, z=AXLE_Z)
    d = chamfer(d.edges().filter_by(lambda e: abs(e.center().X - DRUM_X1) < 1e-6), 1.5)
    d += xcyl(DRUM_HUB_R, DRUM_X0 + DRUM_REAR_T, front_x + 0.1, z=AXLE_Z)
    hexagon = Pos(0, AXLE_Z) * RegularPolygon(DRUM_HEX_AF / 2, 6, major_radius=False)
    d += prism_yz(hexagon, DRUM_X0, DRUM_X0 + DRUM_REAR_T + 0.1)
    d -= xcyl(ROD_R + SLIDE, DRUM_X0 - 1, DRUM_X1 + 1, z=AXLE_Z)
    for y, z in chamber_centres():
        d -= xcyl(SHELL_R + 0.3, front_x - 1, DRUM_X1 - 4, y, z)     # seat for the shell nose
        d -= xcyl(6.5, DRUM_X1 - 5, DRUM_X1 + 1, y, z)               # window onto the slug
    # Ring of dimples between the windows, like the engraved band on the prop.
    for k in range(N_CHAMBERS):
        a = math.radians((k + 0.5) * 360 / N_CHAMBERS)
        r = DRUM_PITCH_R + 4.0
        d -= xcyl(2.2, DRUM_X1 - 1.0, DRUM_X1 + 1, r * math.sin(a), AXLE_Z + r * math.cos(a))
    return d


def drum_rear():
    sk = Pos(0, AXLE_Z) * (Circle(DRUM_R) - RegularPolygon(DRUM_HEX_AF / 2 + FIT, 6, major_radius=False))
    for y, z in chamber_centres():
        sk -= Pos(y, z) * Circle(SHELL_R + 0.3)
    return prism_yz(sk, DRUM_X0, DRUM_X0 + DRUM_REAR_T)


def shell():
    """Dummy shell, modelled in the top chamber."""
    x0, x1 = DRUM_X0 + 0.2, DRUM_X1 - 4.2
    s = xcyl(SHELL_R, x0, x1)
    s = chamfer(s.edges().filter_by(lambda e: abs(e.center().X - x1) < 1e-3), 1.2)
    for gx in (20, 44):                                            # two engraved bands
        s -= xcyl(SHELL_R + 1, gx, gx + 1.0) - xcyl(SHELL_R - 0.5, gx - 1, gx + 2)
    nose = Plane(origin=(x1, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    s -= extrude(nose * (Rot(0, 0, 90) * cross_sketch(9, 6.5, 1.8)), amount=-0.8)
    s -= xcyl(3.4, x0 - 1, x0 + 0.5) - xcyl(2.6, x0 - 1, x0 + 0.5)  # primer ring
    return s


# --------------------------------------------------------------------------
# Crucifix barrel
# --------------------------------------------------------------------------


def barrel_sleeve(length, rod_z, slot_centres, slot_len, text_right=None, text_left=None, text_size=6.0):
    """One octagonal sleeve, built along +X from x=0.

    The x=0 end has a mortise and sits on the print bed.  The far end closes
    over a 45 degree shoulder and carries a tenon, so the sleeve prints
    upright without supports.  Slots go through the two side faces; text is
    engraved on the two upper diagonal faces.
    """
    body = oct_x(OCT_AF, 0, length) + oct_x(TENON_AF, length - 0.1, length + TENON_LEN)
    cav_top = length - 8.4
    body -= oct_x(TENON_AF + 2 * FIT, -1, MORTISE_DEPTH)
    body -= xcyl(CAV_R, MORTISE_DEPTH - 0.1, cav_top)
    body -= xcone(CAV_R, 9.0, cav_top, cav_top + (CAV_R - 9.0))
    body -= xcyl(ROD_R + FIT + 0.05, cav_top, length + TENON_LEN + 1, z=rod_z)
    for gx in (5.0, length - 6.2):                                 # border grooves
        body -= oct_x(OCT_AF + 2, gx, gx + 1.2) - oct_x(OCT_AF - 1.2, gx - 1, gx + 2.2)

    slot = extrude(Pos(0, 0, 9) * SlotOverall(slot_len, 6.0), amount=12)
    for cx in slot_centres:
        for ang in (90, 270):
            body -= Pos(cx, 0, 0) * Rot(ang, 0, 0) * slot

    s = math.sqrt(0.5)
    half = OCT_AF / 2
    usable = length - MORTISE_DEPTH - 18
    mid = (MORTISE_DEPTH + 4 + length - 14) / 2
    faces = (
        (text_right, Plane(origin=(mid, -half * s, half * s), x_dir=(1, 0, 0), z_dir=(0, -s, s))),
        (text_left, Plane(origin=(mid, half * s, half * s), x_dir=(-1, 0, 0), z_dir=(0, s, s))),
    )
    for label, plane in faces:
        if label:
            body -= extrude(plane * fitted_text(label, usable, text_size), amount=-TEXT_DEPTH)
    return body


def barrel_tail():
    sleeve = barrel_sleeve(TAIL_LEN, SPINE_Z, [40, 80, 120, 160], 30.0, TEXT_TAIL_RIGHT, TEXT_TAIL_LEFT, 6.0)
    return Pos(RECV_X1, 0, 0) * sleeve


def barrel_head():
    """Hub to muzzle.  Built muzzle-end first so the muzzle sits on the bed."""
    # After the half turn below, the sleeve's right face is on the prop's left.
    sleeve = barrel_sleeve(HEAD_LEN, SPINE_Z, [46], 38.0, TEXT_HEAD_LEFT, TEXT_HEAD_RIGHT, 5.2)
    sleeve -= box(14.0, 17.3, -1.95, 1.95, 12, OCT_AF / 2 + 1)      # slot for the front sight
    return Pos(HUB_X1 + HEAD_LEN, 0, 0) * Rot(0, 0, 180) * sleeve


def barrel_arm():
    """The right-hand arm of the cross.  The left one is the same part."""
    sleeve = barrel_sleeve(ARM_LEN, CROSS_Z, [26, 46], 14.0)
    return Pos(HUB_XC, -(HUB_HALF_Y + ARM_LEN), 0) * Rot(0, 0, 90) * sleeve


def cross_hub():
    """Where the barrel and the arms meet: four mortises and two rod holes."""
    hub = oct_x(OCT_AF, HUB_X0, HUB_X1) + oct_y(OCT_AF, -HUB_HALF_Y, HUB_HALF_Y, HUB_XC)
    af = TENON_AF + 2 * FIT
    hub -= oct_x(af, HUB_X0 - 1, HUB_X0 + MORTISE_DEPTH) + oct_x(af, HUB_X1 - MORTISE_DEPTH, HUB_X1 + 1)
    hub -= oct_y(af, -HUB_HALF_Y - 1, -HUB_HALF_Y + MORTISE_DEPTH, HUB_XC)
    hub -= oct_y(af, HUB_HALF_Y - MORTISE_DEPTH, HUB_HALF_Y + 1, HUB_XC)
    hub -= xcyl(ROD_R + FIT + 0.05, HUB_X0 - 1, HUB_X1 + 1, z=SPINE_Z)
    hub -= ycyl(ROD_R + FIT + 0.05, -HUB_HALF_Y - 1, HUB_HALF_Y + 1, HUB_XC, CROSS_Z)
    return hub


def end_cap(rod_z, bore):
    """Ringed round cap, built along +X: the disc spans x -CAP_LEN..0 and the
    tenon 0..TENON_LEN.  Prints with the ringed face on the bed."""
    c = xcyl(CAP_R, -CAP_LEN, 0)
    c = chamfer(c.edges().filter_by(lambda e: abs(e.center().X + CAP_LEN) < 1e-6), 1.5)
    c += oct_x(TENON_AF, -0.1, TENON_LEN)
    rings = (11.5, 15.5) if bore else (5.0, 10.0, 15.0)
    for r in rings:
        c -= xcyl(r + 0.7, -CAP_LEN - 1, -CAP_LEN + 0.8) - xcyl(r - 0.7, -CAP_LEN - 1, -CAP_LEN + 0.8)
    if bore:
        c -= xcyl(8.0, -CAP_LEN - 1, -CAP_LEN + 7)                  # shallow recess that reads as a bore
    c -= xcyl(ROD_R + FIT + 0.05, -2.0, TENON_LEN + 1, z=rod_z)
    return c


def muzzle_cap():
    return Pos(HUB_X1 + HEAD_LEN, 0, 0) * Rot(0, 0, 180) * end_cap(SPINE_Z, bore=True)


def arm_cap():
    return Pos(HUB_XC, -(HUB_HALF_Y + ARM_LEN), 0) * Rot(0, 0, 90) * end_cap(CROSS_Z, bore=False)


def front_sight():
    """Small upright cross that plugs into the top of the barrel at the muzzle."""
    x1 = HUB_X1 + HEAD_LEN - 14.0
    half = OCT_AF / 2
    sk = rect(-1.75, 1.75, half - 2.5, half + 21) + rect(-6, 6, half + 12, half + 15.5)
    return prism_yz(sk, x1 - 3.0, x1)


# --------------------------------------------------------------------------
# Torch, Dragon's Breath and the twisted rod
# --------------------------------------------------------------------------


def torch():
    x0, x1, z = TORCH_X0, TORCH_X1, TORCH_Z
    fat0, fat1 = PEDESTAL_X0 - 6, PEDESTAL_X1 + 6
    t = xcyl(15, x0, x0 + 12, z=z) + xcyl(13, x0 + 11, fat0 - 6, z=z)
    t += xcone(13, 19, fat0 - 6, fat0, z=z) + xcyl(19, fat0, fat1, z=z) + xcone(19, 13, fat1, fat1 + 6, z=z)
    t += xcyl(13, fat1 + 6, x1 - 24, z=z)
    t += xcone(13, 20, x1 - 24, x1 - 10, z=z) + xcyl(20, x1 - 10, x1, z=z)      # flared bell
    bands = ((x0 + 3, 15), (x0 + 6.5, 15), (fat0 - 14, 13), (fat1 + 12, 13), (x1 - 6, 20))
    for gx, r_here in bands:                                                     # engraved bands
        t -= xcyl(22, gx, gx + 1.2, z=z) - xcyl(r_here - 0.6, gx - 1, gx + 2.2, z=z)
    t -= xcyl(17.5, x1 - 4, x1 + 1, z=z)                                         # lens seat
    t -= xcone(6, 17.5, x1 - 16, x1 - 4, z=z)                                    # reflector
    # Cross engraved on each side of the wide middle section.
    skin = xcyl(20, fat0, fat1, z=z) - xcyl(19 - 0.8, fat0 - 1, fat1 + 1, z=z)
    mark = extrude(Pos(0, 0, 5) * cross_pattee(24), amount=20)
    for ang in (90, 270):
        t -= skin & (Pos((fat0 + fat1) / 2, 0, z) * Rot(ang, 0, 0) * mark)
    return t


def torch_pedestal():
    top_flat = OCT_AF / 2
    p = box(PEDESTAL_X0, PEDESTAL_X1, -10, 10, top_flat, TORCH_Z - 16)
    p = chamfer(p.edges().filter_by(lambda e: abs(e.center().Z - top_flat) < 1e-6), 3.0)
    return p - xcyl(19 + FIT, PEDESTAL_X0 - 1, PEDESTAL_X1 + 1, z=TORCH_Z)


def dragon_tube():
    x0, x1, z, r = DRAGON_X0, DRAGON_X1, DRAGON_Z, DRAGON_R
    crown0 = x1 - 12
    t = xcyl(r, x0, x1, z=z)
    for bx in (x0 + 4, crown0 - 22):                                             # raised bands
        t += xcyl(r + 1.5, bx, bx + 6, z=z)
        t += xcone(r, r + 1.5, bx - 1.5, bx, z=z) + xcone(r + 1.5, r, bx + 6, bx + 7.5, z=z)
    t -= xcyl(TWIST_SOCKET_R, x0 - 1, x0 + 9, z=z)                               # twisted rod socket
    t -= xcyl(8.5, crown0 - 4, x1 + 1, z=z)                                      # nozzle
    # Crown: eight pointed teeth around the nozzle.
    tooth_gap = extrude(Pos(0, 0, 4) * poly((crown0 + 2, 0), (x1 + 1, 4.9), (x1 + 1, -4.9)), amount=12)
    for k in range(8):
        t -= Pos(0, 0, z) * Rot(k * 45, 0, 0) * tooth_gap
    return t


def dragon_mount():
    """Saddle between the underside of the hub and the Dragon's Breath tube."""
    m = box(HUB_XC - 12, HUB_XC + 12, -7, 7, DRAGON_Z + 4, -OCT_AF / 2)
    return m - xcyl(DRAGON_R + FIT, HUB_XC - 13, HUB_XC + 13, z=DRAGON_Z)


def twisted_rod():
    """Two strands twisted together.  Its plain ends plug into round sockets
    in the receiver and in the Dragon's Breath tube."""
    x0, x1 = 95.0, DRAGON_X0 + 8.5
    length = x1 - x0
    strands = Pos(2.4, 0) * Circle(3.3) + Pos(-2.4, 0) * Circle(3.3)
    half_turns = round(length / 20)   # a whole number of half turns keeps both end faces aligned
    twist = Solid.extrude_linear_with_rotation(strands.faces()[0], (0, 0, 0), (0, 0, length), 180 * half_turns)
    return Part() + Pos(x0, 0, DRAGON_Z) * Rot(0, 90, 0) * twist


# --------------------------------------------------------------------------
# Hardware shown in the assembly (not printed)
# --------------------------------------------------------------------------


def spine_rod():
    return xcyl(ROD_R, 84.5, HUB_X1 + HEAD_LEN + 1.5, z=SPINE_Z)


def cross_rod():
    reach = HUB_HALF_Y + ARM_LEN + 1.5
    return ycyl(ROD_R, -reach, reach, HUB_XC, CROSS_Z)


def axle_rod():
    return xcyl(ROD_R, -14.5, 75.5, z=AXLE_Z)


# --------------------------------------------------------------------------
# Part registry
# --------------------------------------------------------------------------

REAR_DOWN = Rot(0, -90, 0)   # +X of the prop points up on the bed
FRONT_DOWN = Rot(0, 90, 0)   # -X of the prop points up on the bed
LEFT_HALF = Rot(90, 0, 0)    # +Y of the prop points up on the bed
RIGHT_HALF = Rot(-90, 0, 0)  # -Y of the prop points up on the bed
UPSIDE_DOWN = Rot(180, 0, 0)
AS_IS = Rot(0, 0, 0)


@dataclass
class PropPart:
    name: str
    solid: Part
    print_rot: Location = AS_IS
    color: tuple = BRASS
    filament: str = "brass"
    printed: bool = True
    placements: list = field(default_factory=lambda: [Location()])
    explode: tuple = (0.0, 0.0, 0.0)        # exploded-view offset, same for every copy
    explode_local: tuple = (0.0, 0.0, 0.0)  # extra offset that turns with each copy's placement
    notes: str = ""

    @property
    def qty(self):
        return len(self.placements)

    def explode_for(self, index):
        """Exploded-view offset of one copy of the part."""
        trsf = self.placements[index].wrapped.Transformation()
        turned = [sum(trsf.Value(r, c) * self.explode_local[c - 1] for c in (1, 2, 3)) for r in (1, 2, 3)]
        return tuple(base + extra for base, extra in zip(self.explode, turned))


def build_parts():
    recv_l, recv_r = split_halves(receiver_full())
    grip_l, grip_r = split_halves(grip_full())
    shell_spots = [about_axle(-k * 360 / N_CHAMBERS) for k in range(N_CHAMBERS)]
    both_arms = [Location(), Pos(HUB_XC, 0, 0) * Rot(0, 0, 180) * Pos(-HUB_XC, 0, 0)]
    silver = "silver"
    return [
        PropPart("receiver_left", recv_l, LEFT_HALF, explode=(0, 85, 0),
                 notes="Split face on the bed, engraving up."),
        PropPart("receiver_right", recv_r, RIGHT_HALF, explode=(0, -85, 0),
                 notes="Split face on the bed, engraving up."),
        PropPart("grip_left", grip_l, LEFT_HALF, explode=(-175, 30, -10),
                 notes="Split face on the bed, scrollwork up."),
        PropPart("grip_right", grip_r, RIGHT_HALF, explode=(-175, -30, -10),
                 notes="Split face on the bed, scrollwork up."),
        PropPart("trigger", trigger(), LEFT_HALF, SILVER, silver, explode=(0, 0, -60),
                 notes="Flat on its side."),
        PropPart("recoil_shield", recoil_shield(), REAR_DOWN, SILVER, silver, explode=(-50, 0, 0),
                 notes="Flat."),
        PropPart("drum_core", drum_core(), FRONT_DOWN, SILVER, silver, explode=(0, 0, 0),
                 notes="Front flange on the bed, hub and hex spigot up."),
        PropPart("drum_rear", drum_rear(), REAR_DOWN, SILVER, silver, explode=(-25, 0, 0),
                 notes="Flat."),
        PropPart("shell", shell(), REAR_DOWN, SILVER, silver, placements=shell_spots, explode=(-125, 0, 0),
                 notes="Upright, base on the bed. Print 12."),
        PropPart("barrel_tail", barrel_tail(), REAR_DOWN, explode=(60, 0, 0),
                 notes="Upright, mortise end on the bed. Use a brim."),
        PropPart("cross_hub", cross_hub(), AS_IS, explode=(135, 0, 0),
                 notes="As it sits on the prop, bottom flat on the bed."),
        PropPart("barrel_head", barrel_head(), FRONT_DOWN, explode=(215, 0, 0),
                 notes="Upright, muzzle end on the bed."),
        PropPart("barrel_arm", barrel_arm(), LEFT_HALF, placements=both_arms, explode=(135, 0, 0),
                 explode_local=(0, -55, 0), notes="Upright, cap end on the bed. Print 2."),
        PropPart("arm_cap", arm_cap(), LEFT_HALF, placements=both_arms, explode=(135, 0, 0),
                 explode_local=(0, -100, 0), notes="Ringed face on the bed. Print 2."),
        PropPart("muzzle_cap", muzzle_cap(), FRONT_DOWN, explode=(275, 0, 0),
                 notes="Ringed face on the bed."),
        PropPart("front_sight", front_sight(), FRONT_DOWN, explode=(215, 0, 45), notes="Flat on its back."),
        PropPart("torch", torch(), REAR_DOWN, explode=(60, 0, 80),
                 notes="Upright, flared bell up. Use a brim."),
        PropPart("torch_pedestal", torch_pedestal(), AS_IS, explode=(60, 0, 35), notes="Flat base on the bed."),
        PropPart("dragon_tube", dragon_tube(), REAR_DOWN, explode=(175, 0, -75),
                 notes="Upright, crown up."),
        PropPart("dragon_mount", dragon_mount(), UPSIDE_DOWN, explode=(135, 0, -35),
                 notes="Flat face on the bed, cradle up."),
        PropPart("twisted_rod", twisted_rod(), REAR_DOWN, explode=(60, 0, -65),
                 notes="Upright. Use a brim and slow the print down."),
        PropPart("spine_rod", spine_rod(), AS_IS, HARDWARE, printed=False, explode=(140, 0, 150),
                 notes="8 mm rod, 345 mm long."),
        PropPart("cross_rod", cross_rod(), AS_IS, HARDWARE, printed=False, explode=(135, 0, -150),
                 notes="8 mm rod, 203 mm long."),
        PropPart("axle_rod", axle_rod(), AS_IS, HARDWARE, printed=False, explode=(0, 0, -150),
                 notes="8 mm rod, 90 mm long."),
    ]


# Parts that turn together when the drum is spun; used by the motion check.
DRUM_PARTS = ("drum_core", "drum_rear", "shell")
