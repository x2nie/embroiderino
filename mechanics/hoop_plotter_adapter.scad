mountingHolesSpacing = 40;
mountingHolesDia = 3.5;
width = mountingHolesSpacing+10;
totalSpacing = 20;

// print with support material, 30-50% infill 
rotate([90,0,0])
difference(){
    union(){
        translate([totalSpacing-8,-width/2,15]) cube([8,width,8]);
        translate([0,-width/4,15]) cube([16,width/2,8]);
        translate([0,-width/2,11]) cube([totalSpacing,width,4]);
        translate([0,-width/2,0]) cube([8,width,15]);
    }
    
    for(i=[1,-1])
        translate([0,i*mountingHolesSpacing/2,19]) rotate([0,90,0]){ 
                cylinder(r=6.5, h=totalSpacing-4); cylinder(r=mountingHolesDia/2, h=totalSpacing);
    }
    // tool holder holes
    for(i=[1,-1])
        translate([8,i*mountingHolesSpacing/2,6]) rotate([0,-90,0]){cylinder(r=mountingHolesDia/2, h=41); cylinder(r=mountingHolesDia*0.95, h=3, $fn = 6);}
}
