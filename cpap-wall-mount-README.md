# CPAP Wall Mount Holder

A functional and elegant 3D-printable wall mount for organizing your CPAP hose and nasal mask. Designed to keep your equipment tidy and out of reach of curious pets!

## Features

- **Dual-purpose design**: Large curved hook for the CPAP hose and a vertical peg for the nasal mask
- **Cat-proof**: Mount it high on the wall where your cats can't reach
- **Wall-mounted**: Secure mounting with 4 screw holes and countersinks
- **Aesthetic**: Smooth curves and rounded edges for a clean, modern look
- **Parametric**: Easily customize dimensions in the OpenSCAD file

## Design Overview

The mount consists of three main components:
1. **Backplate** (80mm × 120mm): Rounded rectangle with 4 mounting holes
2. **Hose Hook** (upper): Large curved hook (40mm diameter) to cradle the CPAP hose
3. **Mask Peg** (lower): Vertical peg (12mm × 35mm) for hanging the nasal mask

## Printing Instructions

### Recommended Settings
- **Material**: PETG or PLA (PETG recommended for durability)
- **Layer Height**: 0.2mm
- **Infill**: 20-30%
- **Supports**: Not required (designed to print without supports)
- **Orientation**: Print with the backplate flat on the bed
- **Print Time**: Approximately 3-4 hours (depending on printer speed)

### File Generation
1. Open `cpap-wall-mount.scad` in OpenSCAD
2. Press F5 to preview, F6 to render
3. Export as STL: File → Export → Export as STL

Alternatively, use command line:
```bash
openscad -o cpap-wall-mount.stl cpap-wall-mount.scad
```

## Installation

### What You'll Need
- 4 × screws (size depends on your wall type)
- 4 × wall anchors (if mounting to drywall)
- Screwdriver or drill
- Level (optional, but recommended)

### Steps
1. Hold the mount against the wall at desired height (high enough to keep cats away!)
2. Mark the 4 mounting hole positions through the holes
3. Install wall anchors if needed
4. Align the mount and drive screws through the mounting holes
5. Hang your CPAP hose on the curved hook
6. Hang your nasal mask on the vertical peg

## Customization

All key dimensions are parameterized at the top of the `.scad` file. You can easily modify:

- **Backplate size**: Adjust `backplate_width` and `backplate_height`
- **Hook size**: Change `hook_diameter` and `hook_depth`
- **Peg dimensions**: Modify `peg_diameter` and `peg_length`
- **Mounting holes**: Adjust `mounting_hole_diameter` for different screw sizes
- **Aesthetics**: Change `corner_radius` for more/less rounded corners

## Tips

- **For heavier hoses**: Increase `hook_thickness` to 10-12mm for extra strength
- **For longer masks**: Increase `peg_length` to accommodate larger straps
- **For wider walls**: Increase `wall_clearance` if you have textured walls or baseboards

## License

See LICENSE file in the repository root.

## Questions or Issues?

Feel free to modify the design to suit your specific CPAP equipment and preferences!
