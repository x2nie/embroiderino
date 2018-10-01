use <polyround.scad>;

// NOTE: consider losses on round corners when setting workarea dimensions
workareaWidth = 130;
workareaHeight = 150;
frameHeight = 8;
innerFrameThickness = 5;
outerFrameThickness = 9;
innerOuterFramesSpacing = 0.5;
mountingHolesSpacing = 40;

// print with infill above 50% for better stiffness
// this default workarea 130x150 needes 200x200 printer platform space
hoop();

module hoop(){
    // inner frame
    innerFrameWidth = workareaWidth+innerFrameThickness;
    innerFrameHeight = workareaHeight+innerFrameThickness;
    linear_extrude(height = 1.5) difference(){
        roundRectangle(innerFrameWidth, innerFrameHeight, center=true);
        intersection(){
            roundRectangle(workareaWidth, workareaHeight, center=true);
            square(size=[workareaWidth, workareaHeight], center=true);
        }
    }
    linear_extrude(height = frameHeight) difference(){
        roundRectangle(innerFrameWidth, innerFrameHeight, center=true);
        roundRectangle(workareaWidth, workareaHeight, center=true);
    }

    // outer frame
    spacing = innerOuterFramesSpacing*2;
    outerFrameWidth = innerFrameWidth+outerFrameThickness+spacing;
    outerFrameHeight =  innerFrameHeight+outerFrameThickness+spacing;
    difference(){
    union(){
        linear_extrude(height = frameHeight) difference(){
            roundRectangle(outerFrameWidth , outerFrameHeight, center=true);
            roundRectangle(innerFrameWidth+spacing, innerFrameHeight+spacing,   center=true);
    }
    // tightening handle
        // adjust magic number divider to elminate gap between frame and handle
        translate([-8,outerFrameHeight/28+outerFrameHeight/2,0]) 
        difference(){
        cube([20,12,frameHeight]);
        //screw hole
        translate([20,8,frameHeight/2]) rotate([0,-90,0]) {cylinder(r=1.8, h=20); cylinder(r=3.5*0.95, h=3, $fn=6);}
        }
    }
    translate([-1,0,0]) cube([2,innerFrameHeight,frameHeight]);
    }
    // outer frame handle
    translate([outerFrameWidth/15+ innerFrameWidth/2,0,0]) {
    difference(){
        union(){
            translate([0,-20,0]) cube([40,40,frameHeight/2]);
            
            translate([36,-(mountingHolesSpacing+10)/2,0]) hull(){
                cube([4,mountingHolesSpacing+10,6+frameHeight/2]);
                translate([-10,0,0])cube([10,mountingHolesSpacing+10,1]);
            }
        }
        // mounting holes
        for(i=[1,-1])
            translate([0,i*mountingHolesSpacing/2,3+frameHeight/2]) rotate([0,90,0]){ 
            cylinder(r=5.5, h=36); cylinder(r=1.8, h=41);
            }
        }
    }
}

module roundRectangle(width=20, height=25, center = false)
{
  // those two values bellow affects roundness of the frames
  divider = 15;
  cornerR = min([width,height])/5;
  
  points=[
    [0,                    0,                      cornerR],
    [-width/divider,       height/2,               height*2],
    [0,                    height,                 cornerR],
    [width/2,              height+height/divider,  width*2],
    [width,                height,                 cornerR],
    [width+width/divider,  height/2,               height*2],
    [width,                0,                      cornerR],
    [width/2,              -height/divider,        width*2]
  ];
  
  if(center){
     translate([-width/2, -height/2,0])  polygon(polyRound(points,5));
   }
   else{
       polygon(polyRound(points,5));
   }
      
     
 }
