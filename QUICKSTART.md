# Quick Start with UV

This project uses `uv` for fast Python dependency management and task running.

## Prerequisites

1. **Install uv** (if you haven't already):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # Or on Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Install OpenSCAD** (system dependency):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install openscad

   # macOS
   brew install openscad

   # Windows
   # Download from https://openscad.org/downloads.html
   ```

## Getting Started

### 1. Install Python dependencies

```bash
# Install base dependencies
uv sync

# Or install with all optional features
uv sync --all-extras
```

### 2. Use the preview tool

```bash
# Check syntax and generate STL
uv run preview

# Check syntax only (fast)
uv run preview --skip-render

# Preview a specific file
uv run preview path/to/your-design.scad
```

### 3. Using task runner (optional)

For even simpler commands, install poe the poet:

```bash
uv add --dev poethepoet
```

Then you can use:

```bash
uv run poe preview    # Generate and preview STL
uv run poe check      # Check OpenSCAD syntax
uv run poe render     # Render STL file
uv run poe lint       # Lint Python code
uv run poe all        # Run all checks
```

## Project Structure

```
.
├── cpap-wall-mount.scad           # OpenSCAD design file
├── cpap-wall-mount-README.md      # Design-specific documentation
├── scripts/
│   └── preview.py                 # Python preview tool
├── pyproject.toml                 # Python project config
└── SETUP.md                       # Detailed OpenSCAD setup guide
```

## Common Workflows

### Iterating on a design

**Option A: Interactive (recommended)**
1. Open `cpap-wall-mount.scad` in OpenSCAD desktop app
2. Edit parameters in your text editor
3. Save → OpenSCAD auto-reloads
4. See changes instantly!

**Option B: Command-line**
```bash
# Edit the .scad file
vim cpap-wall-mount.scad

# Check syntax
uv run preview --skip-render

# Generate STL when ready
uv run preview
```

### Creating variations

Edit parameters at the top of the `.scad` file:

```scad
// Make the arc bigger for more hose capacity
arc_radius = 100;

// Make it a 3/4 circle instead of semicircle
arc_angle = 270;

// Adjust groove for your specific hose
groove_width = 30;
groove_depth = 18;
```

Then regenerate:
```bash
uv run preview
```

## Adding Python Tools

The project is set up with optional dependency groups:

```bash
# For generating OpenSCAD code from Python (advanced)
uv sync --extra generate

# For analyzing STL files
uv sync --extra analyze

# Development tools (ruff, pytest)
uv sync --extra dev

# Everything
uv sync --all-extras
```

## Next Steps

- See `SETUP.md` for detailed OpenSCAD setup instructions
- See `cpap-wall-mount-README.md` for printing and installation guide
- Check `pyproject.toml` to see available dependencies and tasks

## Tips

- **Speed**: `uv` is extremely fast - dependency resolution in seconds
- **Isolation**: Each project gets its own virtual environment automatically
- **No conflicts**: Won't interfere with your system Python or other projects
- **Easy updates**: `uv sync` keeps everything in sync with `pyproject.toml`

Happy printing! 🎉
