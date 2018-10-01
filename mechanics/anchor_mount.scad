screw_hole_dia = 3.5;
height = 12;

difference(){
    translate([-10,-5,0]) cube([20,10,height]); 
    cylinder(r=screw_hole_dia / 2, h = height); 
    translate([0,0,3]) cylinder(r=screw_hole_dia * 0.95, h = height);
}
for (i=[1:2:height])
translate([-10,4+i/10,i]) mirror([0,0,1]) rotate([0,90,0]) cylinder(r=1.8, h=20, $fn = 2);