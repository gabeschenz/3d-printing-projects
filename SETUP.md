# Quick Setup for OpenSCAD Preview

This guide will help you set up a fast iteration workflow for previewing and testing your 3D designs.

## Option 1: Desktop OpenSCAD (Recommended)

### Installation

**Ubuntu/Debian:**
```bash
sudo apt-get install openscad
```

**macOS:**
```bash
brew install openscad
```

**Windows:**
Download from https://openscad.org/downloads.html

### Usage

1. Open OpenSCAD application
2. File → Open → Select `cpap-wall-mount.scad`
3. The design will automatically reload when you save changes
4. Press **F5** for quick preview (fast)
5. Press **F6** for full render (slower but accurate)
6. Rotate view: Right-click and drag
7. Export to STL: File → Export → Export as STL

### Quick Iteration Workflow

1. Edit parameters in the `.scad` file in your text editor
2. Save the file (Ctrl+S / Cmd+S)
3. OpenSCAD automatically reloads and shows changes
4. Adjust, save, preview - repeat!

## Option 2: Command-Line Workflow (Fastest for Validation)

Use the provided `preview.sh` script to quickly generate STL files and validate the design:

```bash
./preview.sh
```

This will:
- Validate the OpenSCAD syntax
- Generate an STL file
- Show file size and statistics
- Open the STL in your default viewer (if available)

### Generate STL manually:
```bash
openscad -o cpap-wall-mount.stl cpap-wall-mount.scad
```

### Check for errors only (fast):
```bash
openscad --check cpap-wall-mount.scad
```

## Option 3: Online Viewers

If you don't want to install anything, you can use online tools:

### For OpenSCAD files:
1. **OpenSCAD Cloud**: https://www.blockscad3d.com/
   - Can paste `.scad` code directly
   - Limited features compared to desktop

### For STL files (after exporting):
1. **ViewSTL**: https://www.viewstl.com/
   - Just drag and drop your STL file
   - Works in browser, no installation

2. **3D Viewer Online**: https://3dviewer.net/
   - Drag and drop STL files
   - Good visualization

## Recommended Workflow

**For fastest iteration:**
1. Keep OpenSCAD desktop app open with your `.scad` file loaded
2. Edit the parameters in your favorite text editor
3. Save → OpenSCAD auto-reloads → See changes immediately
4. When happy, press F6 to render and export to STL
5. Open STL in your slicer (Cura, PrusaSlicer, etc.) to verify printability

## Checking Printability

After you're happy with the design in OpenSCAD:

1. Export to STL (F6, then File → Export)
2. Open in your slicer software:
   - **Cura**: Free, easy to use - https://ultimaker.com/software/ultimaker-cura
   - **PrusaSlicer**: Excellent for validation - https://www.prusa3d.com/page/prusaslicer_424/
   - **Bambu Studio**: If you have Bambu printer
3. Check:
   - Does it need supports?
   - Are there any errors/non-manifold edges?
   - What's the estimated print time?
   - Does orientation look correct?

## Tips

- **Auto-reload**: OpenSCAD's auto-reload feature is your best friend
- **Preview vs Render**: Use F5 (preview) for quick checks, F6 (render) before exporting
- **Cross-section view**: Uncomment the `difference()` block at the bottom of the `.scad` file to see inside
- **Parameter tweaking**: All the important parameters are at the top of the file - no need to understand the code!

## Common Issues

**OpenSCAD shows errors:**
- Check the console at the bottom of OpenSCAD window
- Syntax errors will show line numbers
- Warnings are usually OK, errors must be fixed

**Design looks wrong:**
- Make sure you're using F6 (full render) not just F5 (preview)
- Some complex geometry only shows correctly after full render

**STL export is huge:**
- This is normal for complex curves
- File size doesn't affect print time, only slicing time
- Typical STL files are 1-10MB

Happy iterating!
