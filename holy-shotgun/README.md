# Holy shotgun display prop

A 3D-printable display prop modelled on the crucifix shotgun from the film
Constantine (2005): a cross-shaped barrel with ringed end caps, an open
twelve-shell drum, a bird's-head grip, a long torch on top, and the Dragon's
Breath tube underneath on its twisted rod.

It is a costume and shelf piece only. Nothing in it can chamber or fire
anything: the barrel is a hollow sleeve over a solid rod, the drum is a
free-spinning ornament, and the shells are solid dummies.

![Assembled prop](docs/render.png)

How it comes apart (there is an [interactive version](viewer/) with a slider):

![The prop pulling apart into its printed parts and going back together](docs/pull-apart.gif)

![Side view](docs/render-side.png)

| | |
|---|---|
| Assembled size | 581 mm long, 224 mm across the arms, 238 mm tall (about 22.9 x 8.8 x 9.4 in) |
| Printed parts | 21 part types, 34 pieces |
| Filament | roughly 700 g at 3 walls and 15% infill |
| Printer | any bed of 220 x 220 mm or larger, 230 mm of height |
| Supports | none |

## How close is it to the film prop?

The layout and proportions follow photos of the hero prop and a licensed
replica: the crucifix barrel, the drum cage with exposed shells, the curved
hood over the drum, the grip, the torch with its flared bell, and the crowned
lower tube. Nothing was measured from the original, so treat it as a close
likeness rather than a dimensional copy.

Known simplifications:

- The prop is covered in fine hand engraving. Here that is reduced to
  scrollwork on the grip, crosses on the receiver and torch, and border
  grooves on the barrel, because detail much finer than a 0.4 mm nozzle does
  not survive printing.
- The inscriptions are the ones legible in the photos, set in capitals so
  they print: `PATER IN MANUS TUAS` / `COMMENDO SPIRITUM` on the front of the
  barrel, `QUI DESIDERAT PACEM` and `BREVE ET EFFICAX PER EXEMPLA` on the
  rear. The prop carries more text than this.
- The trigger is a fixed spur. The photos do not show how the real one works.

Everything is parametric, so the shape can be adjusted by editing the values
at the top of `model.py` and rebuilding.

## What is in this folder

| Path | What it is |
|---|---|
| `stl/` | One STL per printed part, already turned the way it should sit on the bed |
| `PARTS.md` | Print list: quantity, filament, size and orientation for each STL |
| `ASSEMBLY.md` | Assembly order, generated from the build order the checks verify |
| `step/assembly.step` | The full assembly with named, coloured parts, for Fusion 360, FreeCAD and similar |
| `docs/` | Renders, the pull-apart animation and line drawings (`side.svg`, `top.svg`, `iso.svg`, `exploded.svg`) |
| `viewer/` | Interactive 3D viewer with a pull-apart slider. `index.html` is the page to open; it is generated from `page.html` |
| `model.py` | The parametric model (build123d) |
| `build.py` | Checks the model and regenerates everything above |
| `assembly.py` | The motion, fit and build-order checks that `build.py` runs |
| `render.py` | Makes the renders and the pull-apart animation from the viewer; `build.py` calls it |

## Printing

- 0.4 mm nozzle, 0.2 mm layers, 3 walls, 15% infill. PLA or PETG.
- Load each STL as it is. The orientation is already set and no part needs
  supports. A few hidden pockets rely on bridges of about 18 mm or less.
- Use a brim on the tall, thin parts: `barrel_tail`, `torch` and above all
  `twisted_rod`, which is 11 mm across and 202 mm tall. Print that one
  slowly.
- Two colours cover it. Brass for everything except the drum parts, recoil
  shield, shells and trigger, which are silver.
- Print `cross_hub` and one `barrel_arm` first. They are small, and the way
  the tenon fits the mortise tells you whether the clearances suit your
  printer before you commit to the large parts.

See [PARTS.md](PARTS.md) for the full print list.

## Hardware

| Item | Qty | Used for |
|---|---|---|
| 8 mm rod, 345 mm long | 1 | Barrel spine, from inside the receiver to the muzzle cap |
| 8 mm rod, 203 mm long | 1 | Cross spine, from arm cap to arm cap |
| 8 mm rod, 90 mm long | 1 | Drum axle |
| M3 x 30 socket head screw | 8 | Receiver halves (5), grip tongue (2), trigger (1) |
| M3 x 20 socket head screw | 3 | Grip halves |
| Super glue or epoxy | | Barrel joints, torch, sight, Dragon's Breath tube |

One 1 m length of 8 mm rod covers all three pieces. Aluminium tube, steel rod
or a hardwood dowel all work. The rods carry the bending load, so the printed
barrel joints only have to locate the sleeves. The two long rods cross inside
the hub, which is why one runs 4.5 mm above the barrel centreline and the
other 4.5 mm below it.

The screws thread directly into 2.8 mm pilot holes in the plastic; no nuts or
inserts are needed.

## Assembly

![Exploded view](docs/render-exploded.png)

The step-by-step order is in [ASSEMBLY.md](ASSEMBLY.md). In outline:

1. Build three sub-assemblies on the bench: the grip (two halves screwed
   together), the drum (rear flange, axle and recoil shield on the drum
   core), and later the Dragon's Breath tube with its saddle.
2. Lay the right receiver half down, drop in the grip, trigger, drum and
   spine rod, and close the left half over them with eight screws.
3. Thread the barrel onto the spine rod from the receiver outward: rear
   sleeve, hub, cross rod, arms and caps, front sleeve, muzzle cap.
4. Add the torch, the sight, the twisted rod and the Dragon's Breath tube,
   then load the shells.

That file is generated from the build order declared in `model.py`, and the
build checks every step of it, so it cannot drift from the model.

## Rebuilding and customising

```
pip install -r requirements.txt
python build.py                # everything: checks, STL, STEP, drawings, viewer, renders, lists
python build.py --no-assembly  # skip the motion, fit and build-order checks
python build.py --no-draw      # skip the line drawings
python build.py --no-render    # skip the renders and the pull-apart animation
```

A full build takes about three minutes; the assembly checks are about half of
that. `build.py` exits with an error if any check below fails.

The renders in `docs/`, including the pull-apart animation, are made by
opening the viewer in a headless browser, so that step needs two extra
things:

```
pip install -r requirements-render.txt
playwright install chromium
```

If they are missing, the build still runs and prints
`renders NOT updated` with the reason, so the model checks and STL export
never depend on a browser. `python render.py` redoes just the images from the
last build. Two environment variables cover unusual setups: `CHROMIUM_PATH`
points at an existing Chrome or Chromium binary, and `THREE_DIR` points at a
local copy of the three.js 0.128 package for machines that cannot reach the
CDN the viewer loads it from.

Parameters worth knowing about, all at the top of `model.py`:

| Parameter | Default | Effect |
|---|---|---|
| `BED_X`, `BED_Y`, `BED_Z` | 220, 220, 250 | Printer envelope the bed-fit check uses |
| `FIT` | 0.15 | Radial clearance for glued joints. Raise it if parts are tight |
| `SLIDE` | 0.25 | Radial clearance for the drum on its axle |
| `OCT_AF` | 34 | Barrel thickness, across the flats of the octagon |
| `TAIL_LEN`, `HEAD_LEN`, `ARM_LEN` | 190, 90, 68 | Lengths of the four barrel sleeves, which set the cross proportions |
| `N_CHAMBERS`, `DRUM_PITCH_R`, `DRUM_R` | 12, 43.5, 56 | Drum layout |
| `TEXT_*` | see above | The engraved inscriptions |

## The interactive viewer

`viewer/index.html` is a complete, self-contained page: it needs only
`parts.json` beside it and loads three.js from a CDN.

- **On GitHub Pages:** it works as it is. With Pages publishing this
  repository, the viewer is at `/holy-shotgun/viewer/` under the site
  address, and this README, animation included, is the page at
  `/holy-shotgun/`. Pages serves the committed files and does not run the
  build, so rebuild and commit after changing the model.
- **Locally:** browsers will not load `parts.json` from a `file://` address,
  so serve the folder (`python -m http.server` inside `viewer/`) and open the
  address it prints.

To change the page, edit `viewer/page.html` and rebuild. That file is the
source: it is a fragment without a document shell, and `build.py` wraps it to
produce `index.html`.

## What the build checks

The model is code, so its checks run like tests. `model.py` declares how the
parts are meant to move, fit and go together, and `build.py` tests the
geometry against those declarations on every build.

| Check | What it proves |
|---|---|
| Parts | Every printed part is one valid solid and fits the bed |
| Interference | No two parts occupy the same space in the assembled prop |
| Motion | The drum hits nothing at three positions between one chamber and the next, and keeps at least 0.4 mm from everything it does not ride on |
| Fits | For each declared fit, the part is free to move just under its intended clearance and is stopped just beyond it, in each direction tested |
| Build order | For each step, the part can travel its insertion path, sampled every 4 mm, without passing through anything fitted before it; and every part is fitted by some step |

To change a fit or the order, edit `FITS` or `BUILD_ORDER` at the end of
`model.py`. The first run of these checks found three real faults in the
design, which are now fixed: the recoil shield could not be installed at all,
the Dragon's Breath tube could not pass its own saddle in the order given,
and the front sight sat against one wall of its slot.

What they do not cover:

- Paths are straight lines. A step that needs a twist or a wiggle is not
  modelled, and neither is room for fingers or a screwdriver.
- Screws and glue are not parts, so a joint held only by them (the pedestal
  on the barrel, for instance) has no fit to test.
- Fits are tested along the main axes, not for rocking or rotation.
- Nothing here is physical. The parts have not been run through a slicer or
  printed, and real clearances depend on the printer. Every STL was confirmed
  watertight and overhangs were measured by hand for this release, but
  neither is part of the build.

## Carrying it

It still looks like a firearm from a distance. Print the muzzle cap in blaze
orange or paint the tip, and keep it in a bag when it is outside the house.
