#!/usr/bin/env python3
"""
Preview and validate OpenSCAD designs.

This script checks your .scad files, generates STL files, and provides
helpful information about your 3D models.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import click


def find_openscad() -> str | None:
    """Find the OpenSCAD executable."""
    return shutil.which("openscad")


def check_syntax(scad_file: Path) -> bool:
    """Check OpenSCAD file syntax.

    Args:
        scad_file: Path to the .scad file

    Returns:
        True if syntax is valid, False otherwise
    """
    openscad = find_openscad()
    if not openscad:
        click.secho("✗ OpenSCAD not found!", fg="red")
        click.echo("\nInstall OpenSCAD:")
        click.echo("  Ubuntu/Debian: sudo apt-get install openscad")
        click.echo("  macOS: brew install openscad")
        click.echo("  Windows: https://openscad.org/downloads.html")
        return False

    click.echo("Checking syntax...")
    result = subprocess.run(
        [openscad, "--check", str(scad_file)],
        capture_output=True,
        text=True
    )

    if "ERROR" in result.stderr or result.returncode != 0:
        click.secho("✗ Syntax errors found!", fg="red")
        click.echo(result.stderr)
        return False

    click.secho("✓ Syntax OK", fg="green")
    return True


def render_stl(scad_file: Path, output_file: Path) -> bool:
    """Render STL file from OpenSCAD file.

    Args:
        scad_file: Path to the .scad file
        output_file: Path for the output .stl file

    Returns:
        True if rendering succeeded, False otherwise
    """
    openscad = find_openscad()
    if not openscad:
        return False

    click.echo(f"\nRendering {output_file.name}...")
    click.echo("(This may take 30-60 seconds for complex geometry)")

    result = subprocess.run(
        [openscad, "-o", str(output_file), str(scad_file)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        click.secho("✗ Failed to render STL", fg="red")
        click.echo(result.stderr)
        return False

    click.secho(f"✓ STL generated: {output_file}", fg="green")
    return True


def show_stl_info(stl_file: Path) -> None:
    """Display information about the STL file.

    Args:
        stl_file: Path to the .stl file
    """
    if not stl_file.exists():
        return

    # Get file size
    size_bytes = stl_file.stat().st_size
    size_mb = size_bytes / (1024 * 1024)

    # Count triangles (each "facet normal" line is one triangle)
    try:
        with open(stl_file, 'r') as f:
            triangles = sum(1 for line in f if line.strip().startswith("facet normal"))
    except Exception:
        triangles = "unknown"

    click.echo("\n" + "=" * 50)
    click.echo("  STL File Information")
    click.echo("=" * 50)
    click.echo(f"  File: {stl_file.name}")
    click.echo(f"  Size: {size_mb:.2f} MB")
    click.echo(f"  Triangles: {triangles}")
    click.echo()


@click.command()
@click.argument(
    "scad_file",
    type=click.Path(exists=True, path_type=Path),
    default="cpap-wall-mount.scad",
)
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    help="Output STL filename (default: same as input with .stl extension)",
)
@click.option(
    "--skip-render",
    is_flag=True,
    help="Only check syntax, don't render STL",
)
def main(scad_file: Path, output: Path | None, skip_render: bool) -> None:
    """Preview and validate OpenSCAD designs.

    SCAD_FILE: Path to the .scad file (default: cpap-wall-mount.scad)
    """
    click.echo("=" * 50)
    click.echo("  3D Printing Projects - Preview Tool")
    click.echo("=" * 50)
    click.echo()

    # Check if file exists
    if not scad_file.exists():
        click.secho(f"✗ File not found: {scad_file}", fg="red")
        sys.exit(1)

    # Determine output file
    if output is None:
        output = scad_file.with_suffix(".stl")

    # Check syntax
    if not check_syntax(scad_file):
        sys.exit(1)

    # Render STL if requested
    if not skip_render:
        if not render_stl(scad_file, output):
            sys.exit(1)

        show_stl_info(output)

        click.echo("Next steps:")
        click.echo(f"  1. Open {output} in your slicer (Cura, PrusaSlicer, etc.)")
        click.echo("  2. Or view online at: https://www.viewstl.com/")
        click.echo(f"  3. Or edit {scad_file} in OpenSCAD for interactive editing")

    click.echo()
    click.secho("Done!", fg="green")


@click.command()
@click.argument(
    "scad_file",
    type=click.Path(exists=True, path_type=Path),
    default="cpap-wall-mount.scad",
)
def check(scad_file: Path) -> None:
    """Quickly check OpenSCAD syntax without rendering."""
    if not check_syntax(scad_file):
        sys.exit(1)


if __name__ == "__main__":
    main()
