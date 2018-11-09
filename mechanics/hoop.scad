use <polyround.scad>;

// NOTE: consider losses (presser foot size) on corners when setting workarea dimensions
// print with infill above 60% for better stiffness
// this default workarea 130x150 needes 200x200 printer platform space
hoop(workareaWidth = 130, workareaHeight = 150);

// smaller hoops
//hoop(workareaWidth = 80, workareaHeight = 100);
//hoop(workareaWidth = 60, workareaHeight = 80);


innerOuterFramesSpacing = 0.5;
mountingHolesSpacing = 40;

module hoop(workareaWidth = 130, workareaHeight = 150, frameHeight = 8, innerFrameThickness = 3, outerFrameThickness = 5, roundness = 5, tightenerSpace = 3, sizeOffset = 0, withHandle = true){
    // inner frame
    innerFrameWidth = workareaWidth+innerFrameThickness*2+sizeOffset;
    innerFrameHeight = workareaHeight+innerFrameThickness*2+sizeOffset;
    linear_extrude(height = 1.5) difference(){
        roundRectangle(innerFrameWidth, innerFrameHeight, roundness, center=true);
        intersection(){
            roundRectangle(workareaWidth+sizeOffset, workareaHeight+sizeOffset, roundness, center=true);
            square(size=[workareaWidth, workareaHeight], center=true);
        }
    }
    linear_extrude(height = frameHeight) difference(){
        roundRectangle(innerFrameWidth, innerFrameHeight, roundness, center=true);
        roundRectangle(workareaWidth+sizeOffset, workareaHeight+sizeOffset, roundness, center=true);
    }

    // outer frame
    spacing = innerOuterFramesSpacing*2;
    outerFrameWidth = innerFrameWidth+outerFrameThickness*2+spacing;
    outerFrameHeight =  innerFrameHeight+outerFrameThickness*2+spacing;
    difference(){
    union(){
        linear_extrude(height = frameHeight) difference(){
            roundRectangle(outerFrameWidth , outerFrameHeight, roundness, center=true);
            roundRectangle(innerFrameWidth+spacing, innerFrameHeight+spacing, roundness,  center=true);
    }
    // tightening handle
        // adjust magic number divider to elminate gap between frame and handle
        translate([-9,outerFrameHeight/28+3/roundness+outerFrameHeight/2,0]) 
        difference(){
            tightnWidth = 20+tightenerSpace;
            cube([tightnWidth ,12,frameHeight]);
            //screw hole
            translate([tightnWidth,8,frameHeight/2]) rotate([0,-90,0]) {cylinder(r=1.8, h=tightnWidth+1); cylinder(r=3.5*0.95, h=3, $fn=6);}
            }
        }
        translate([-1,0,0]) cube([tightenerSpace,innerFrameHeight,frameHeight]);
    }
    // outer frame handle
    if (withHandle)
        translate([outerFrameWidth/15+ innerFrameWidth/2,0,0]) {
            handle(frameHeight);
        }
}

module handle(frameHeight)
{
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

module roundRectangle(width=20, height=25, roundness = 5, center = false)
{
  // those two values bellow affects roundness of the frames
  divider = 15;
  cornerR = min([width,height])/roundness;
  
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
     translate([-width/2, -height/2,0])  polygon(polyRound(points,10));
   }
   else{
       polygon(polyRound(points,10));
   }
      
     
 }
