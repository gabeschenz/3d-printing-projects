# 3D Printing Projects

A collection of useful 3D printable designs.

## Projects

### CPAP Wall Mount Holder
A functional and elegant wall-mounted organizer for CPAP hose. The arc design with groove allows the hose to drape naturally in loops, keeping it tidy and out of reach of pets.

- **File**: `cpap-wall-mount.scad`
- **Documentation**: See `cpap-wall-mount-README.md`
- **Features**: Arc-style design with hose groove, wall-mounted, parametric
- **Preview Tools**: See `SETUP.md` for local preview setup

## Getting Started

Each project includes:
- OpenSCAD source file (`.scad`) for easy customization
- Detailed README with printing and installation instructions
- Parameterized designs that you can adjust to your needs

## Tools Required

- [OpenSCAD](https://openscad.org/) - Free 3D CAD software for viewing and exporting designs
- 3D Printer or access to 3D printing service
- [uv](https://docs.astral.sh/uv/) (optional) - Fast Python package manager for automation tools

## Quick Start

### Using Python tools (recommended)
```bash
# Install dependencies
uv sync

# Preview and generate STL
uv run preview
```

See [QUICKSTART.md](QUICKSTART.md) for detailed Python/uv setup.

### Using OpenSCAD directly
1. Open the `.scad` file in OpenSCAD
2. Customize parameters as needed
3. Export as STL file
4. Slice and print with your preferred slicer software

See [SETUP.md](SETUP.md) for OpenSCAD setup and workflow details.