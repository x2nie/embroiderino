encoder_wheel_axial_hole_dia = 9.6;
encoder_blades_no = 10;
encoder_wheel_dia = encoder_wheel_axial_hole_dia*1.6 + 10;

encoder_mount_screw_dia = 5;
encoder_wheel();
//encoder_mount();

// this part was designed to fit into particular machine model, probably you need to redesign this
module encoder_mount()
{
    rotate([0,-90,45]) linear_extrude(height=2) polygon([[0,4],[0,28],[13,28]]);
    difference(){
        translate([-22,18,0]) cube([5,4,31]);
        // holes
        translate([-20,22,18]) rotate([90,0,0]) { 
            cylinder(r=1.0, h=20);
            translate([0,11,0]) cylinder(r=1.0, h=20);
        }
    }
    difference(){
        hull(){
            for (i = [1,-1])
            translate([i*2,0,0]) cylinder(r=encoder_mount_screw_dia, h=2);
            translate([-22,16,0]) cube([5,6,2]);
        }
        hull(){
            for (i = [1,-1])
            translate([i*2,0,0]) cylinder(r=encoder_mount_screw_dia/2, h=2);
        }
    }
}

module encoder_wheel(){
    blade_angle = 360 / encoder_blades_no/2;
    
    difference(){
        union(){
            for(i=[0:blade_angle:360])
                rotate([0,0,i*2]) encoder_blade(blade_angle);            
                
            cylinder(r=encoder_wheel_axial_hole_dia*0.8, h = 8);
        }
        cylinder(r=encoder_wheel_axial_hole_dia/2, h = 10);
        translate([encoder_wheel_axial_hole_dia-7.5,-3,0]) cube([4,6,10]);
    }
}

module encoder_blade(angle = 10)
intersection(){
    difference(){
        cylinder(r=encoder_wheel_dia/2, h = 2);
        translate([0,-encoder_wheel_dia,0]) cube([encoder_wheel_dia, encoder_wheel_dia*2, 2]);
    }
    rotate([0,0,angle]) cube([encoder_wheel_dia, encoder_wheel_dia, 2]);
};