#!/bin/bash
# Quick preview script for OpenSCAD designs

set -e

SCAD_FILE="cpap-wall-mount.scad"
STL_FILE="cpap-wall-mount.stl"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "================================================"
echo "  CPAP Wall Mount - Quick Preview"
echo "================================================"
echo ""

# Check if OpenSCAD is installed
if ! command -v openscad &> /dev/null; then
    echo -e "${RED}ERROR: OpenSCAD is not installed${NC}"
    echo ""
    echo "Please install OpenSCAD:"
    echo "  Ubuntu/Debian: sudo apt-get install openscad"
    echo "  macOS: brew install openscad"
    echo "  Windows: Download from https://openscad.org/"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓${NC} OpenSCAD found: $(openscad --version 2>&1 | head -1)"
echo ""

# Validate syntax
echo "Checking syntax..."
if openscad --check "$SCAD_FILE" 2>&1 | grep -q "ERROR"; then
    echo -e "${RED}✗ Syntax errors found!${NC}"
    openscad --check "$SCAD_FILE"
    exit 1
else
    echo -e "${GREEN}✓${NC} Syntax OK"
fi
echo ""

# Generate STL
echo "Generating STL file..."
echo "  (This may take 30-60 seconds for complex geometry)"
if openscad -o "$STL_FILE" "$SCAD_FILE" 2>&1; then
    echo -e "${GREEN}✓${NC} STL generated successfully"
else
    echo -e "${RED}✗ Failed to generate STL${NC}"
    exit 1
fi
echo ""

# Show file info
if [ -f "$STL_FILE" ]; then
    FILE_SIZE=$(du -h "$STL_FILE" | cut -f1)
    TRIANGLES=$(grep -c "facet normal" "$STL_FILE" || echo "unknown")

    echo "================================================"
    echo "  STL File Information"
    echo "================================================"
    echo "  File: $STL_FILE"
    echo "  Size: $FILE_SIZE"
    echo "  Triangles: $TRIANGLES"
    echo ""
fi

# Try to open in viewer
echo "Next steps:"
echo "  1. Open $STL_FILE in your slicer (Cura, PrusaSlicer, etc.)"
echo "  2. Or view online at: https://www.viewstl.com/"
echo "  3. Or open $SCAD_FILE in OpenSCAD desktop app for interactive editing"
echo ""

# Offer to open if on macOS or Linux with xdg-open
if [[ "$OSTYPE" == "darwin"* ]]; then
    read -p "Open STL file now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "$STL_FILE"
    fi
elif command -v xdg-open &> /dev/null; then
    read -p "Open STL file now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        xdg-open "$STL_FILE" &
    fi
fi

echo -e "${GREEN}Done!${NC}"
