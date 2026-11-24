"""Assembly checks: do the parts fit, move and go together as intended?

The model declares three kinds of intent (see the end of model.py):

    Motion  a group of parts that turns on an axis, such as the drum
    Fit     how much play a part should have in given directions
    Step    one step of the build order: which parts go on, along what path

and the functions here test the geometry against them:

    check_motion      nothing is hit at any sampled angle, and a running
                      clearance is kept all the way round
    check_fits        each part is free up to just under its declared play
                      and stopped just beyond it
    check_sequence    each part can travel its insertion path without
                      passing through anything already installed, and every
                      part is installed by some step.  Sub-assemblies made
                      on the bench are checked against only the parts they
                      are built onto

A part is addressed as "name" (every copy) or ("name", index) (one copy).
Everything works on the solids in their assembled positions; nothing here
knows about this particular prop.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from build123d import Axis, Pos

OVERLAP_TOL = 0.3    # mm3; smaller overlaps are touching faces and numerical noise
# mm between samples along an insertion path.  A collision can only slip
# between two samples if the moving part and the obstacle are together
# thinner than this along the direction of travel, so keep it under the sum
# of the two thinnest features in the model (here a 3 mm sight and 2.6 mm walls).
PATH_SPACING = 4.0
FIT_UNDER = 0.05     # a part must still be free this far short of its declared play
FIT_OVER = 0.10      # and must be stopped this far beyond it


@dataclass
class Motion:
    name: str
    parts: list              # what turns
    origin: tuple            # a point on the axis
    direction: tuple         # axis direction
    angles: list             # degrees to test
    carried_by: list         # parts it turns on; excluded from the clearance check
    min_gap: float           # running clearance to everything else, mm


@dataclass
class Fit:
    parts: list              # moved together as one body
    directions: list         # unit vectors to test
    play: float              # intended free movement in each of those directions, mm
    note: str = ""


@dataclass
class Step:
    title: str               # the instruction, as a person would read it
    moving: list             # parts that travel in this step
    path: list               # offsets from the final position, in the order travelled; the part ends at (0, 0, 0)
    bench: list | None = None       # set for a sub-assembly made off the prop: the parts it is built onto.
                                    # Only those are checked, and nothing counts as installed yet.
    stands_for: list | None = None  # other parts installed the same way, e.g. the remaining copies


class Instances:
    """Every copy of every part, in its assembled position."""

    def __init__(self, solids: dict):
        self.solids = solids                                   # (name, index) -> solid
        self.boxes = {k: _box(s) for k, s in solids.items()}

    def resolve(self, specs):
        keys = []
        for spec in specs:
            if isinstance(spec, tuple):
                keys.append(spec)
            else:
                found = [k for k in self.solids if k[0] == spec]
                if not found:
                    raise KeyError(f"no part named {spec!r}")
                keys.extend(found)
        return keys

    @staticmethod
    def label(key):
        return f"{key[0]}[{key[1]}]"


def _box(solid):
    bb = solid.bounding_box()
    return (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)


def _shift(box, d):
    return (box[0] + d[0], box[1] + d[1], box[2] + d[2], box[3] + d[0], box[4] + d[1], box[5] + d[2])


def _apart(a, b, margin=0.0):
    return any(a[i] > b[i + 3] + margin or b[i] > a[i + 3] + margin for i in range(3))


def overlap(a, b):
    """Shared volume of two solids, mm3."""
    common = a & b
    if common is None:
        return 0.0
    if isinstance(common, (list, tuple)):
        return sum(getattr(c, "volume", 0.0) for c in common)
    return getattr(common, "volume", 0.0)


def _hits(inst, moving, others, offset=(0.0, 0.0, 0.0), moved=None):
    """Overlaps between the moving parts (shifted by offset, or replaced by
    `moved` solids) and the others.  Returns [(moving key, other key, mm3)]."""
    out = []
    for m in moving:
        solid = moved[m] if moved else Pos(*offset) * inst.solids[m]
        box = _box(solid) if moved else _shift(inst.boxes[m], offset)
        for o in others:
            if _apart(box, inst.boxes[o]):
                continue
            vol = overlap(solid, inst.solids[o])
            if vol > OVERLAP_TOL:
                out.append((m, o, vol))
    return out


# --------------------------------------------------------------------------
# Motion
# --------------------------------------------------------------------------


def check_motion(inst, motion):
    """Returns (problems, smallest running clearance in mm)."""
    moving = inst.resolve(motion.parts)
    carried = set(inst.resolve(motion.carried_by))
    others = [k for k in inst.solids if k not in moving]
    axis = Axis(motion.origin, motion.direction)
    problems = []
    for angle in motion.angles:
        turned = {m: inst.solids[m].rotate(axis, angle) for m in moving}
        for m, o, vol in _hits(inst, moving, others, moved=turned):
            problems.append(f"{motion.name} at {angle:g} deg: {inst.label(m)} hits {inst.label(o)} ({vol:.1f} mm3)")

    # Running clearance, measured at rest.  The turning parts are bodies of
    # revolution about the axis as far as their neighbours are concerned.
    smallest = math.inf
    for m in moving:
        for o in others:
            if o in carried or _apart(inst.boxes[m], inst.boxes[o], motion.min_gap + 1.0):
                continue
            gap = inst.solids[m].distance(inst.solids[o])
            smallest = min(smallest, gap)
            if gap < motion.min_gap - 1e-6:
                problems.append(f"{motion.name}: {inst.label(m)} runs {gap:.2f} mm from {inst.label(o)}, "
                                f"under the {motion.min_gap:g} mm it should keep")
    return problems, smallest


# --------------------------------------------------------------------------
# Fits
# --------------------------------------------------------------------------


def check_fits(inst, fits):
    """Returns (problems, number of direction tests run)."""
    problems, tests = [], 0
    for fit in fits:
        moving = inst.resolve(fit.parts)
        others = [k for k in inst.solids if k not in moving]
        name = " + ".join(dict.fromkeys(k[0] for k in moving))
        for d in fit.directions:
            tests += 1
            under = tuple(c * (fit.play - FIT_UNDER) for c in d)
            over = tuple(c * (fit.play + FIT_OVER) for c in d)
            early = _hits(inst, moving, others, under)
            if early:
                m, o, vol = max(early, key=lambda h: h[2])
                problems.append(f"{name} toward {d}: tighter than the {fit.play:g} mm declared; "
                                f"already into {inst.label(o)} at {fit.play - FIT_UNDER:.2f} mm")
            elif not _hits(inst, moving, others, over):
                problems.append(f"{name} toward {d}: looser than the {fit.play:g} mm declared; "
                                f"nothing stops it at {fit.play + FIT_OVER:.2f} mm")
    return problems, tests


# --------------------------------------------------------------------------
# Build order
# --------------------------------------------------------------------------


def _samples(path):
    """Offsets along the path, PATH_SPACING apart, stopping short of the final position."""
    points = [tuple(p) for p in path] + [(0.0, 0.0, 0.0)]
    out = []
    for a, b in zip(points, points[1:]):
        n = max(1, math.ceil(math.dist(a, b) / PATH_SPACING))
        for i in range(n):
            t = i / n
            out.append(tuple(a[k] + (b[k] - a[k]) * t for k in range(3)))
    return out


def check_sequence(inst, steps):
    """Returns (problems, number of positions tested)."""
    problems, positions = [], 0
    installed = []
    for number, step in enumerate(steps, 1):
        moving = inst.resolve(step.moving)
        if step.bench is not None:
            world = [k for k in inst.resolve(step.bench) if k not in moving]
        else:
            world = [k for k in installed if k not in moving]
        blocked = set()
        for offset in _samples(step.path):
            positions += 1
            for m, o, vol in _hits(inst, moving, [w for w in world], offset):
                if (m, o) in blocked:
                    continue
                blocked.add((m, o))
                left = math.dist(offset, (0, 0, 0))
                problems.append(f"step {number} ({step.title}): {inst.label(m)} runs into {inst.label(o)} "
                                f"with {left:.0f} mm still to travel")
        if step.bench is None:
            for k in moving + (inst.resolve(step.stands_for) if step.stands_for else []):
                if k not in installed:
                    installed.append(k)
    missing = sorted({k[0] for k in inst.solids if k not in installed})
    if missing:
        problems.append("no step installs: " + ", ".join(missing))
    return problems, positions
