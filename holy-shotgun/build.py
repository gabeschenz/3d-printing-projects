"""Build, check and export the holy shotgun prop.

    python build.py              # checks + STL + STEP + drawings + renders + PARTS.md
    python build.py --no-draw    # skip the (slow) line drawings
    python build.py --no-render  # skip the README renders and animation
    python build.py --no-assembly  # skip the motion, fit and build-order checks

Outputs, relative to this file:
    stl/<part>.stl            one file per printed part, already in print orientation
    step/assembly.step        full assembly with part names and colours
    docs/*.svg                line drawings of the assembly and the exploded view
    docs/*.png, *.gif         shaded renders and the pull-apart animation (see render.py)
    viewer/parts.json         meshes and part data for the interactive viewer
    viewer/index.html         the viewer as a complete page, built from viewer/page.html
    PARTS.md                  generated print list
    ASSEMBLY.md               generated assembly order
"""

from __future__ import annotations

import argparse
import base64
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
from build123d import Color, Compound, ExportSVG, Pos, export_step, export_stl

import assembly
import model

HERE = Path(__file__).parent
PLA_DENSITY = 1.24  # g/cm3
SOLID_FRACTION = 0.35  # rough share of the solid volume that is plastic at 3 walls / 15% infill


def print_oriented(part: model.PropPart):
    """The part rotated into print orientation, sitting on Z=0 and centred on the bed origin."""
    s = part.print_rot * part.solid
    bb = s.bounding_box()
    return Pos(-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z) * s


def placed(part: model.PropPart, exploded=False):
    """The part's solids in assembled position, or pushed apart for the exploded view."""
    out = []
    for i, loc in enumerate(part.placements):
        s = loc * part.solid
        if exploded:
            s = Pos(*part.explode_for(i)) * s
        out.append(s)
    return out


def check_parts(parts):
    """Every printed part must be one valid solid that fits the bed."""
    ok = True
    rows = []
    limit_xy = (model.BED_X - 2 * model.BED_MARGIN, model.BED_Y - 2 * model.BED_MARGIN)
    for p in parts:
        if not p.printed:
            continue
        s = print_oriented(p)
        bb = s.bounding_box()
        size = (bb.max.X - bb.min.X, bb.max.Y - bb.min.Y, bb.max.Z - bb.min.Z)
        problems = []
        if not s.is_valid:
            problems.append("invalid solid")
        if len(s.solids()) != 1:
            problems.append(f"{len(s.solids())} solids")
        fits = (size[0] <= limit_xy[0] and size[1] <= limit_xy[1]) or (size[1] <= limit_xy[0] and size[0] <= limit_xy[1])
        if not fits or size[2] > model.BED_Z - 20:
            problems.append("does not fit the bed")
        ok &= not problems
        rows.append((p, size, s.volume / 1000.0, problems))
    return ok, rows


def check_interference(parts, tol_mm3=1.0):
    """No two parts may occupy the same space in the assembled prop."""
    solids = []
    for p in parts:
        for i, s in enumerate(placed(p)):
            label = p.name if p.qty == 1 else f"{p.name}[{i}]"
            solids.append((label, s, s.bounding_box()))
    clashes = []
    for (na, a, ba), (nb, b, bb) in itertools.combinations(solids, 2):
        if na.split("[")[0] == nb.split("[")[0] == "shell":
            continue
        if (ba.max.X < bb.min.X or bb.max.X < ba.min.X or ba.max.Y < bb.min.Y or bb.max.Y < ba.min.Y
                or ba.max.Z < bb.min.Z or bb.max.Z < ba.min.Z):
            continue
        if assembly.overlap(a, b) > tol_mm3:
            clashes.append((na, nb, assembly.overlap(a, b)))
    return clashes


def check_assembly(parts):
    """Run the motion, fit and build-order checks.  Returns the list of problems."""
    inst = assembly.Instances({(p.name, i): s for p in parts for i, s in enumerate(placed(p))})
    problems = []

    t = time.time()
    for motion in model.MOTIONS:
        found, gap = assembly.check_motion(inst, motion)
        problems += found
        state = "clear" if not found else f"{len(found)} problem(s)"
        print(f"motion check, {motion.name}: {state}; closest running clearance {gap:.2f} mm ({time.time() - t:.0f}s)")

    t = time.time()
    found, tests = assembly.check_fits(inst, model.FITS)
    problems += found
    print(f"fit check: {tests} directions over {len(model.FITS)} fits, {len(found)} problem(s) ({time.time() - t:.0f}s)")

    t = time.time()
    found, positions = assembly.check_sequence(inst, model.BUILD_ORDER)
    problems += found
    print(f"build-order check: {len(model.BUILD_ORDER)} steps, {positions} positions, "
          f"{len(found)} problem(s) ({time.time() - t:.0f}s)")

    for line in problems:
        print(f"  PROBLEM {line}")
    return problems


def export_stls(parts):
    out = HERE / "stl"
    out.mkdir(exist_ok=True)
    wanted = {f"{p.name}.stl" for p in parts if p.printed}
    for stale in out.glob("*.stl"):          # drop files left over from parts that no longer exist
        if stale.name not in wanted:
            stale.unlink()
    for p in parts:
        if p.printed:
            export_stl(print_oriented(p), str(out / f"{p.name}.stl"), tolerance=0.02, angular_tolerance=0.15)


def assembly_compound(parts, exploded=False):
    children = []
    for p in parts:
        for i, s in enumerate(placed(p, exploded)):
            s.label = p.name if p.qty == 1 else f"{p.name}_{i + 1}"
            s.color = Color(*p.color)
            children.append(s)
    return Compound(label="holy_shotgun", children=children)


def draw(shape, path, origin, look_at, up=(0, 0, 1), width_mm=260):
    visible, _hidden = shape.project_to_viewport(origin, up, look_at)
    bb = Compound(children=visible).bounding_box()
    scale = width_mm / max(bb.max.X - bb.min.X, 1e-6)
    svg = ExportSVG(scale=scale, margin=4)
    svg.add_layer("visible", line_weight=0.18)
    svg.add_shape(visible, layer="visible")
    svg.write(str(path))


def _mesh_payload(solid, crease_deg=32.0):
    """Tessellate for the web viewer: quantised positions and crease-aware normals, base64 encoded."""
    verts, tris = solid.tessellate(0.12, 0.3)
    v = np.array([(p.X, p.Y, p.Z) for p in verts], dtype=np.float64)
    t = np.array(tris, dtype=np.int64)
    corners = v[t]                                             # (n, 3, 3)
    fn = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
    area = np.linalg.norm(fn, axis=1, keepdims=True)
    keep = area[:, 0] > 1e-9
    t, corners, fn, area = t[keep], corners[keep], fn[keep], area[keep]
    unit = fn / area
    # Smooth each corner over the neighbouring faces that lie within the crease angle.
    faces_at = {}
    for fi, tri in enumerate(t):
        for vi in tri:
            faces_at.setdefault(int(vi), []).append(fi)
    cos_crease = np.cos(np.radians(crease_deg))
    normals = np.zeros_like(corners)
    for fi, tri in enumerate(t):
        for ci, vi in enumerate(tri):
            near = [fj for fj in faces_at[int(vi)] if unit[fi] @ unit[fj] >= cos_crease]
            n = fn[near].sum(axis=0)
            normals[fi, ci] = n / max(np.linalg.norm(n), 1e-12)
    lo, hi = v.min(axis=0), v.max(axis=0)
    scale = float(max((hi - lo).max(), 1e-6)) / 65535.0
    qpos = np.round((corners.reshape(-1, 3) - lo) / scale).astype(np.uint16)
    qnrm = np.round(normals.reshape(-1, 3) * 127).astype(np.int8)
    packed = np.concatenate([qpos.view(np.uint8).reshape(-1, 6), qnrm.view(np.uint8).reshape(-1, 3)], axis=1)
    uniq, inverse = np.unique(packed, axis=0, return_inverse=True)
    pos = np.ascontiguousarray(uniq[:, :6]).view(np.uint16).reshape(-1, 3)
    nrm = np.ascontiguousarray(uniq[:, 6:]).view(np.int8).reshape(-1, 3)
    idx = inverse.reshape(-1).astype(np.uint32)
    b64 = lambda a: base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()
    return {"origin": [round(float(x), 4) for x in lo], "scale": scale, "triangles": int(len(t)),
            "pos": b64(pos), "nrm": b64(nrm), "idx": b64(idx)}


def _matrix(loc):
    trsf = loc.wrapped.Transformation()
    return [[round(trsf.Value(r, c), 6) for c in range(1, 5)] for r in range(1, 4)]


def export_viewer(parts, rows):
    """Write viewer/parts.json for the interactive exploded view."""
    info = {p.name: (size, vol) for p, size, vol, _ in rows}
    out = []
    for p in parts:
        entry = {
            "name": p.name,
            "qty": p.qty,
            "printed": p.printed,
            "color": [round(c, 3) for c in p.color],
            "filament": p.filament if p.printed else "hardware",
            "notes": p.notes,
            "explodes": [[round(v, 3) for v in p.explode_for(i)] for i in range(p.qty)],
            "placements": [_matrix(loc) for loc in p.placements],
            "mesh": _mesh_payload(p.solid),
        }
        if p.name in info:
            size, vol = info[p.name]
            entry["bed"] = [round(x) for x in size]
            entry["grams"] = round(vol * PLA_DENSITY * SOLID_FRACTION)
        out.append(entry)
    (HERE / "viewer").mkdir(exist_ok=True)
    lines = ",\n".join(json.dumps(e, separators=(",", ":")) for e in out)   # one part per line
    (HERE / "viewer" / "parts.json").write_text("[\n" + lines + "\n]\n")
    return sum(e["mesh"]["triangles"] for e in out)


# viewer/page.html is a fragment: the host it was written for supplies the
# document around it.  A static host such as GitHub Pages does not, so the
# build wraps it into a complete page.  The reset below matches what that
# host provides, which keeps the two renderings the same.
PAGE_HEAD = """<!doctype html>
<!-- Generated by build.py from page.html. Edit page.html, then rebuild. -->
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>
  :root { color-scheme: light; padding: env(safe-area-inset-top, 0px) 0 env(safe-area-inset-bottom, 0px); }
  body { margin: 0; font: 14px system-ui, sans-serif; }
  img { max-width: 100%; }
  [hidden] { display: none !important; }
</style>
"""
PAGE_BODY_STARTS_AT = '<div class="wrap">'


def write_viewer_page():
    """Write viewer/index.html, a standalone copy of the viewer page."""
    fragment = (HERE / "viewer" / "page.html").read_text()
    cut = fragment.index(PAGE_BODY_STARTS_AT)   # title, fonts and styles come before this and belong in <head>
    page = PAGE_HEAD + fragment[:cut].rstrip() + "\n</head>\n<body>\n" + fragment[cut:].rstrip() + "\n</body>\n</html>\n"
    (HERE / "viewer" / "index.html").write_text(page)


def write_assembly_md(checked):
    """Write ASSEMBLY.md from the build order declared in model.py."""
    lines = [
        "# Assembly order",
        "",
        "Generated by `build.py` from `BUILD_ORDER` in `model.py`.",
        "",
    ]
    if checked:
        lines += [
            "Every step below has been checked against the model: the part can travel its",
            "insertion path without passing through anything fitted before it.",
            "",
        ]
    else:
        lines += ["The build-order check was skipped on the build that wrote this file.", ""]
    for number, step in enumerate(model.BUILD_ORDER, 1):
        lines.append(f"{number}. {step.title}")
    lines.append("")
    (HERE / "ASSEMBLY.md").write_text("\n".join(lines))


def write_parts_md(rows):
    lines = [
        "# Print list",
        "",
        "Generated by `build.py`. Sizes are the bounding box in print orientation.",
        "Plastic is a rough estimate at 3 walls and 15% infill in PLA.",
        "",
        "| File | Qty | Filament | Size on bed (mm) | Height (mm) | Plastic each (g) | Orientation |",
        "|---|---|---|---|---|---|---|",
    ]
    total = 0.0
    for p, size, vol, _ in rows:
        grams = vol * PLA_DENSITY * SOLID_FRACTION
        total += grams * p.qty
        lines.append(
            f"| `stl/{p.name}.stl` | {p.qty} | {p.filament} | {size[0]:.0f} x {size[1]:.0f} | {size[2]:.0f} "
            f"| {grams:.0f} | {p.notes} |"
        )
    lines += ["", f"Estimated plastic in total: about {total:.0f} g.", ""]
    (HERE / "PARTS.md").write_text("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-draw", action="store_true")
    ap.add_argument("--no-export", action="store_true")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--no-assembly", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    parts = model.build_parts()
    print(f"built {len(parts)} part types in {time.time() - t0:.1f}s")

    ok, rows = check_parts(parts)
    for p, size, vol, problems in rows:
        flag = "OK  " if not problems else "FAIL"
        print(f"  {flag} {p.name:16s} x{p.qty:<2d} {size[0]:6.1f} x {size[1]:6.1f} x {size[2]:6.1f} mm  "
              f"{vol:6.1f} cm3  {', '.join(problems)}")

    clashes = check_interference(parts)
    for a, b, vol in clashes:
        print(f"  CLASH {a} / {b}: {vol:.1f} mm3")
    print(f"interference check: {len(clashes)} clash(es)")
    if not args.no_assembly:
        clashes += check_assembly(parts)

    asm = assembly_compound(parts)
    bb = asm.bounding_box()
    print(f"assembled size: {bb.max.X - bb.min.X:.0f} long x {bb.max.Y - bb.min.Y:.0f} wide x "
          f"{bb.max.Z - bb.min.Z:.0f} tall mm")

    if not args.no_export:
        export_stls(parts)
        (HERE / "step").mkdir(exist_ok=True)
        export_step(asm, str(HERE / "step" / "assembly.step"))
        write_parts_md(rows)
        write_assembly_md(checked=not args.no_assembly)
        tris = export_viewer(parts, rows)
        write_viewer_page()
        print(f"wrote stl/, step/assembly.step, PARTS.md, viewer/index.html, viewer/parts.json ({tris} triangles)")

    if not args.no_draw:
        docs = HERE / "docs"
        docs.mkdir(exist_ok=True)
        centre = (150, 0, -40)
        t1 = time.time()
        draw(asm, docs / "side.svg", (150, -2000, -40), centre)
        draw(asm, docs / "top.svg", (150, 0, 2000), (150, 0, 0), up=(0, 1, 0))
        draw(asm, docs / "iso.svg", (1300, -1200, 700), centre)
        draw(assembly_compound(parts, exploded=True), docs / "exploded.svg", (1400, -1400, 800), centre)
        print(f"wrote drawings in {time.time() - t1:.1f}s")

    if not args.no_render:
        # Optional step: it needs a browser, so a missing one is reported, not fatal.
        t2 = time.time()
        try:
            import render
            written = render.render_all()
            print(f"wrote {len(written)} renders, including the pull-apart animation, in {time.time() - t2:.1f}s")
        except ImportError as err:
            print(f"renders NOT updated: {err.name} is not installed (pip install -r requirements-render.txt)")
        except Exception as err:  # no browser, no network for the 3D library, and so on
            print(f"renders NOT updated: {str(err).splitlines()[0]}")

    if not ok or clashes:
        sys.exit(1)


if __name__ == "__main__":
    main()
