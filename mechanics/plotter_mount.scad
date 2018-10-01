// distance from end to rod beginning (contact)
distance = 47;
// default value 20 is fine
column_height = 20;

// print both parts with 40-50% infill
mount_plotter();
//translate ([52,0,0]) 
translate ([52,5,0]) 
mount_clamp();

module screw_hole(d=3.5, fn=10, pocket = false)
{
    cylinder(r=d/2, h = 20);
    translate([0,0,-7]){
        cylinder(r=d*0.95, h = 10, $fn=fn);
        if (pocket)
        {
            translate([-d,-20,0]) cube([2*d,20,8]);
        }
    }
}
rod_r = 10.5 / 2;
module mount_clamp()
{
    //translate([0,0,0]) cylinder(r=rod_r, h=column_height);
    translate([-8,11.5,0]) difference(){ 
        cube([10, 6, column_height]);
        translate([3,-2.5,0]) rotate([0,0,8]) cube([5, 5, column_height]);
    }
    
    difference(){
        translate([2,-12,0]) cube([8, 29.5, column_height]);
        // rod hole
        translate([0,0,0]) cylinder(r=rod_r*sqrt(2), h=column_height, $fn = 4);
        // screw hole
        translate([8,-8,column_height/2]) rotate([0,-90,0]) screw_hole();
    }
}

module mount_plotter()
{
    difference(){
        mount_column();
        translate([10,0,column_height+4]) hull(){ sphere(r=8); translate([distance-22,0,0]) sphere(r=8); };
    }
}
module mount_column(){
    base_width = 40;
    difference() {
        // base
        translate([0,-base_width/2,0]) hull(){
            cube([5, base_width,column_height ]);
            translate([10,base_width/4,0]) cube([5, base_width/2 ,column_height ]);
        }
        // base screw holes
        for( i = [1,-1])
            translate([7,i*(base_width-10)/2, column_height/2]) rotate([180,90,0]) screw_hole();
    }
    difference(){
        union(){
            // column
            translate([0,-11,0]) cube([distance+rod_r-sqrt(2), 22,column_height]); 
            // tooth
            translate([distance+1,0,0]) rotate([0,0,5]) cube([3.5, 14,column_height]);
            translate([distance-1.5,-column_height/6,column_height/2]) rotate([0,90,0]) cylinder(r=column_height/2, h = 5);
            
        }
    // rod hole
    translate([distance+rod_r,0,0]) cylinder(r=rod_r, h=column_height, $fn=8);
    
     translate([distance-3,-8,column_height/2]) rotate([0,90,0]) screw_hole(fn=6, pocket = true);   
    }
    
}