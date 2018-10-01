knoobHeight = 20;
rodDia = 3.5;

difference(){
union(){
for(i=[0:24:360])
    rotate([0,0,i]) translate([rodDia*0.8,0,0]) cylinder(r1=2, r2=1.2, h=knoobHeight, $fn = 3);

cylinder(r=rodDia-0.2,h=knoobHeight);
cylinder(r=rodDia*1.4,h=3);
}
cylinder(r=rodDia/2,h=knoobHeight);
cylinder(r=rodDia*0.95,h=3, $fn=6);
}