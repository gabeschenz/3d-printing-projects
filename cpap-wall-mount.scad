/*
 * CPAP Hose Wall Mount - Arc Design
 *
 * A simple, elegant arc-shaped holder that extends from the wall.
 * The hose rests in a groove along the arc, allowing it to drape
 * naturally in loops. Keeps hose organized and away from cats!
 *
 * Features:
 * - Wall-mounted backplate (prints flat, mounts vertically)
 * - Curved arc extending from wall
 * - Groove sized for standard CPAP hose (19-22mm)
 * - Deep enough to hold 2 loops of hose
 */

// ===== PARAMETERS =====

// Wall mounting backplate
backplate_width = 60;           // Width of backplate
backplate_height = 80;          // Height of backplate
backplate_thickness = 5;        // Thickness of backplate

// Mounting holes
mounting_hole_diameter = 5;     // Diameter for mounting screws
mounting_hole_spacing = 50;     // Vertical spacing between holes

// Arc dimensions
arc_radius = 80;                // Radius of the arc curve
arc_thickness = 12;             // Thickness of the arc arm
arc_width = 50;                 // Width of the arc (front to back)
arc_angle = 180;                // Degrees of arc (180 = semicircle)

// Hose groove
groove_width = 25;              // Width of groove (for 19-22mm hose)
groove_depth = 15;              // Depth of groove (how deep hose sits)

// Aesthetics
corner_radius = 3;              // Rounded corners
$fn = 64;                       // Smoothness

// ===== MODULES =====

// Wall mounting backplate
module backplate() {
    difference() {
        // Main plate with rounded corners
        translate([-backplate_width/2, 0, 0])
        linear_extrude(height = backplate_height)
        offset(r = corner_radius)
        offset(r = -corner_radius)
        square([backplate_width, backplate_thickness]);

        // Mounting holes
        for (i = [-1, 1]) {
            translate([0, backplate_thickness + 1, backplate_height/2 + i * mounting_hole_spacing/2])
            rotate([90, 0, 0])
            cylinder(d = mounting_hole_diameter, h = backplate_thickness + 2);
        }

        // Countersink for screw heads
        for (i = [-1, 1]) {
            translate([0, backplate_thickness - 1, backplate_height/2 + i * mounting_hole_spacing/2])
            rotate([90, 0, 0])
            cylinder(d = mounting_hole_diameter * 2, h = 2);
        }
    }
}

// Arc arm with groove for hose
module arc_with_groove() {
    translate([0, backplate_thickness, backplate_height/2]) {
        difference() {
            // Main arc body
            rotate([0, 90, 0])
            rotate_extrude(angle = arc_angle)
            translate([arc_radius, 0, 0])
            hull() {
                translate([0, -arc_width/2, 0])
                circle(d = arc_thickness);
                translate([0, arc_width/2, 0])
                circle(d = arc_thickness);
            }

            // Groove for hose - U-shaped channel along top of arc
            rotate([0, 90, 0])
            rotate_extrude(angle = arc_angle)
            translate([arc_radius, 0, 0])
            translate([0, 0, arc_thickness/2 - groove_depth/2])
            hull() {
                translate([0, -groove_width/2, 0])
                circle(d = groove_depth);
                translate([0, groove_width/2, 0])
                circle(d = groove_depth);
            }
        }
    }
}

// Reinforcement where arc meets backplate
module reinforcement() {
    translate([0, backplate_thickness, backplate_height/2]) {
        rotate([0, 90, 0])
        cylinder(d = arc_thickness + 8, h = arc_width, center = true);
    }
}

// ===== ASSEMBLY =====

module cpap_wall_mount() {
    // Backplate (will be vertical on wall, prints flat on bed)
    backplate();

    // Reinforcement
    reinforcement();

    // Arc with groove
    arc_with_groove();
}

// ===== RENDER =====

// Print orientation: lay the backplate flat on the print bed
// The arc will extend upward during printing
cpap_wall_mount();

// Uncomment for cross-section view:
// difference() {
//     cpap_wall_mount();
//     translate([0, -100, -50])
//     cube([200, 200, 200]);
// }
