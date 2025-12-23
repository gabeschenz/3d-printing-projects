/*
 * CPAP Hose and Nasal Mask Wall Mount
 *
 * A functional and elegant wall-mounted holder for CPAP equipment.
 * Keeps hose and mask organized and out of reach of curious cats!
 *
 * Features:
 * - Wall-mounted backplate with mounting holes
 * - Large curved hook for CPAP hose
 * - Vertical peg for hanging nasal mask
 * - Smooth, rounded edges for visual appeal
 * - Parametric design for easy customization
 */

// ===== PARAMETERS =====

// Main dimensions
backplate_height = 120;      // Height of the backplate
backplate_width = 80;        // Width of the backplate
backplate_thickness = 4;     // Thickness of the backplate
wall_clearance = 3;          // Space between wall and backplate

// Mounting holes
mounting_hole_diameter = 5;  // Diameter for mounting screws
mounting_hole_inset = 10;    // Distance from edges

// Hose hook dimensions
hook_diameter = 40;          // Outer diameter of the hose hook
hook_thickness = 8;          // Thickness of the hook arm
hook_depth = 45;             // How far the hook extends from wall
hook_offset_y = 30;          // Position from top

// Mask peg dimensions
peg_diameter = 12;           // Diameter of the mask peg
peg_length = 35;             // Length of the peg
peg_offset_y = -25;          // Position from center (negative = lower)

// Aesthetics
corner_radius = 8;           // Radius for rounded corners
$fn = 64;                    // Smoothness of curves

// ===== MODULES =====

// Rounded rectangle for the backplate
module rounded_rectangle(w, h, r, thickness) {
    linear_extrude(height = thickness)
    offset(r = r)
    offset(r = -r)
    square([w, h], center = true);
}

// Backplate with mounting holes
module backplate() {
    difference() {
        // Main backplate with rounded corners
        rounded_rectangle(backplate_width, backplate_height, corner_radius, backplate_thickness);

        // Mounting holes (4 corners)
        for (x = [-1, 1], y = [-1, 1]) {
            translate([
                x * (backplate_width/2 - mounting_hole_inset),
                y * (backplate_height/2 - mounting_hole_inset),
                -1
            ])
            cylinder(d = mounting_hole_diameter, h = backplate_thickness + 2);
        }

        // Countersink for screw heads
        for (x = [-1, 1], y = [-1, 1]) {
            translate([
                x * (backplate_width/2 - mounting_hole_inset),
                y * (backplate_height/2 - mounting_hole_inset),
                backplate_thickness - 2
            ])
            cylinder(d = mounting_hole_diameter * 2, h = 3);
        }
    }
}

// Large curved hook for CPAP hose
module hose_hook() {
    translate([0, hook_offset_y, backplate_thickness/2 + wall_clearance]) {
        rotate([0, 90, 0]) {
            difference() {
                // Outer curve
                union() {
                    // Main hook curve
                    rotate_extrude(angle = 200, $fn = 64)
                    translate([hook_diameter/2, 0, 0])
                    circle(d = hook_thickness);

                    // Base reinforcement
                    translate([0, 0, -hook_thickness/2])
                    cylinder(d = hook_diameter + hook_thickness, h = hook_thickness);
                }

                // Remove bottom half to make it a hook
                translate([0, -hook_diameter, -hook_depth])
                cube([hook_diameter * 2, hook_diameter * 2, hook_depth * 2], center = true);
            }

            // End cap for smooth finish
            rotate([0, 0, 200])
            translate([hook_diameter/2, 0, 0])
            sphere(d = hook_thickness);

            // Start cap
            translate([hook_diameter/2, 0, 0])
            sphere(d = hook_thickness);
        }
    }
}

// Vertical peg for nasal mask
module mask_peg() {
    translate([0, peg_offset_y, backplate_thickness/2 + wall_clearance]) {
        rotate([0, 90, 0]) {
            // Main peg shaft
            cylinder(d = peg_diameter, h = peg_length);

            // Rounded end
            translate([0, 0, peg_length])
            sphere(d = peg_diameter);

            // Base reinforcement
            cylinder(d1 = peg_diameter + 6, d2 = peg_diameter, h = 8);
        }
    }
}

// Decorative accent line (optional detail)
module accent_line() {
    translate([0, 0, backplate_thickness - 0.5])
    linear_extrude(height = 0.6)
    offset(r = -3)
    offset(r = 3)
    offset(r = -corner_radius - 2)
    offset(r = corner_radius + 2)
    square([backplate_width, backplate_height], center = true);
}

// ===== ASSEMBLY =====

module cpap_wall_mount() {
    // Main backplate
    backplate();

    // Hose hook (top portion)
    hose_hook();

    // Mask peg (lower portion)
    mask_peg();

    // Optional accent (comment out if you prefer simpler look)
    // accent_line();
}

// ===== RENDER =====

cpap_wall_mount();

// Uncomment to see cross-section view for debugging:
// difference() {
//     cpap_wall_mount();
//     translate([-100, 0, -50])
//     cube([200, 200, 200]);
// }
