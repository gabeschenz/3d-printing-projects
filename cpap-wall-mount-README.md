# CPAP Hose Wall Mount - Arc Design

A simple, elegant wall-mounted holder for organizing your CPAP hose. The arc design allows the hose to drape naturally in loops, keeping it tidy and out of reach of curious pets!

## Design Concept

The holder features a graceful arc extending from the wall with a groove along its length. Your CPAP hose rests in this groove and can loop around the arc naturally. Think of it like a towel ring, but specifically sized for CPAP hoses.

## Features

- **Arc-shaped design**: Smooth 180° semicircular arc extending from wall
- **Hose groove**: 25mm wide channel sized for standard CPAP hoses (19-22mm diameter)
- **Holds 2 loops**: Arc radius of 80mm provides ~160mm depth for multiple hose loops
- **Simple and elegant**: Minimalist design that looks clean on any wall
- **Cat-proof**: Mount high on the wall where pets can't reach
- **Parametric**: Fully customizable in OpenSCAD

## Dimensions

- **Backplate**: 60mm wide × 80mm tall × 5mm thick
- **Arc**: 180° semicircle with 80mm radius
- **Arc depth**: 50mm (front to back)
- **Groove**: 25mm wide × 15mm deep
- **Print size**: Approximately 60mm × 85mm × 165mm

## Printing Instructions

### Recommended Settings
- **Material**: PETG or PLA (PETG recommended for durability)
- **Layer Height**: 0.2mm or 0.3mm
- **Infill**: 20-30%
- **Supports**: YES - needed for the arc overhang
- **Support angle**: 50-60° (supports needed where arc curves over)
- **Orientation**: Print with backplate flat on bed, arc extending upward
- **Print Time**: Approximately 4-5 hours

### Support Strategy
- Enable supports for the arc
- Use tree supports or regular supports from build plate only
- Support interface layers recommended for cleaner finish in the groove

### File Generation
1. Open `cpap-wall-mount.scad` in OpenSCAD
2. Press F5 to preview
3. Press F6 to render (may take a minute)
4. Export as STL: File → Export → Export as STL

Or use command line:
```bash
openscad -o cpap-wall-mount.stl cpap-wall-mount.scad
```

## Installation

### What You'll Need
- 2 × screws (size depends on your wall type - #8 or #10 work well)
- 2 × wall anchors (if mounting to drywall)
- Screwdriver or drill
- Level (optional)

### Steps
1. Hold the mount against the wall at desired height (high enough for cat protection!)
2. Mark the 2 mounting hole positions
3. Install wall anchors if needed
4. Align the mount and drive screws through the holes
5. Drape your CPAP hose into the groove along the arc

## Usage Tips

- The hose naturally rests in the groove and loops around the arc
- You can adjust how many loops based on your hose length
- The groove keeps the hose from sliding off
- For longer hoses, you might want two mounts on opposite walls

## Customization

All dimensions are parameterized at the top of the `.scad` file:

- **`arc_radius`**: Make it larger (100-120mm) for more loops or smaller (60-70mm) for compact spaces
- **`arc_angle`**: Change from 180° to 270° for ¾ circle, or 90° for minimal design
- **`groove_width`**: Adjust if you have a larger/smaller diameter hose
- **`groove_depth`**: Make deeper (18-20mm) for more secure hose retention
- **`arc_width`**: Increase (60-70mm) for wider hoses or decrease (40mm) for minimal material
- **`backplate_height`**: Adjust for different mounting hole spacing

## Common Modifications

**For a smaller/more compact mount:**
```scad
arc_radius = 60;
arc_angle = 120;
```

**For holding more hose loops:**
```scad
arc_radius = 100;
arc_angle = 270;
```

**For a thicker/heavier hose:**
```scad
groove_width = 30;
groove_depth = 18;
arc_thickness = 15;
```

## Troubleshooting

**Hose falls out of groove:** Increase `groove_depth` to 18-20mm
**Arc too deep for space:** Reduce `arc_radius` to 60-70mm
**Not enough hose capacity:** Increase `arc_radius` or `arc_angle`
**Supports hard to remove:** Use tree supports or reduce support density to 10-15%

## License

See LICENSE file in the repository root.

Enjoy your organized, cat-proof CPAP setup!
