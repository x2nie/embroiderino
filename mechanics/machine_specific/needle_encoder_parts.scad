needle_shaft_dia = 5;
mount_shaft_dia = 7.3;

//flag2();
sensor_mount();

module sensor_mount(){
holes_spacing = 15;
	difference(){
union(){
	translate([-(5+holes_spacing)/2,0,0]){ cube([holes_spacing+5, 13,2]); cube([holes_spacing+5, 8,mount_shaft_dia/2+1]);}
	
// mounting clamp
translate([-10,4,9]) rotate([180,0,0]) rotate([0,90,0])
difference(){
cylinder(r=mount_shaft_dia*0.9, h=20);
cylinder(r=mount_shaft_dia/2, h=20);
translate([-mount_shaft_dia/2+1,0,0]) cube([mount_shaft_dia-2,mount_shaft_dia,20]);
//holes
for(i=[0,7, 14])
translate([0,-mount_shaft_dia-0.5,3+i]) rotate([-90,0,0]) {cylinder(r=3.5,h=2); cylinder(r=1.5,h=8);}
}
}
//screws holes
 for (i=[holes_spacing/2,-holes_spacing/2])
	translate([i,4,0]) cylinder(r=1.2, h=5);
//keys holes
 for (i=[0,6])
	translate([0,4+i,0]) cylinder(r=1.5, h=2, $fn=8);
}

}


module flag2(){
	translate([-4,-7,-10]) {cube([8, 5, 10]); cube([16, 5, 1]);}
difference(){
union(){
	translate([-4,-7,0]) cube([8, 10, 1]);
	translate([-6,-7,0]) cube([12, 5, 5]);
}
	translate([-4,-7,1]) cube([8, 10, 5]);
	cylinder(r=1.2, h=2, $fn=8);
}
}


module flag1(){
difference(){
union(){
	translate([-needle_shaft_dia,0,0]) cube([10,needle_shaft_dia+1,4]);
	cylinder(r=needle_shaft_dia, h=4);
	//flag
	translate([needle_shaft_dia,0,0]) {cube([5,6,4]); translate([5,0,0]) cube([1,15,6]);}
}
	cylinder(r=needle_shaft_dia/2, h=4);
	translate([-2,0,0]) cube([4,needle_shaft_dia+5,4]);
	translate([-needle_shaft_dia,needle_shaft_dia/2+1.5,2]) rotate([0,90,0]) cylinder(r=1.0, h=15);
}
}