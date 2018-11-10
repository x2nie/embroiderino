use <hoop.scad>

// some of the coordinates were set in messy way
// be careful when changing area size and correct things when needed
workareaWidth = 160;
workareaHeight = 260;

frameHeight = 9;
innerFrameThickness = 5;
outerFrameThickness = 10;

// print all quarters from 0 to 3
// infill at least 50%
hoop_quarter(0);


//hoop_large();

module hoop_large()
{
    sizeOffset = 8;
    innerFrameWidth = workareaWidth+innerFrameThickness*2+sizeOffset;
    innerFrameHeight = workareaHeight+innerFrameThickness*2+sizeOffset;
    spacing = 0.5*2;
    outerFrameWidth = innerFrameWidth+outerFrameThickness*2+spacing;
    outerFrameHeight =  innerFrameHeight+outerFrameThickness*2+spacing;
    
    
    hoop(workareaWidth, workareaHeight, frameHeight, innerFrameThickness, outerFrameThickness, 
    roundness = 1.5, 
    tightenerSpace = 6, 
    sizeOffset = sizeOffset, 
    withHandle = false
  );
    
    // here connectors are placed
    // its offsets (bigger magic numbers) position is hardcoded by trial, messy way  
    for (pos = [[1,0],[-1,0],[0,1],[0,-1]])
        {
            // inner frame connectors
           translate([(outerFrameWidth/2 - outerFrameWidth/80)*pos[0],(outerFrameHeight/2 + 0)*pos[1],0])
           if(pos != [0,1]) rotate([0,0,90*pos[0]]) connector(0.5);
           else rotate([0,0,180]) connector(0.5);
               
            // outer frame connectors
           translate([(outerFrameWidth/2 + outerFrameWidth/28)*pos[0],(outerFrameHeight/2 + outerFrameHeight/26)*pos[1],0])
           if(pos != [0,1]) rotate([0,0,180+90*pos[0]]) connector();
        }
     
    // mounting handle
    translate([workareaWidth/2+workareaWidth/7, -40]) 
    {
        linear_extrude(height=2) polygon([[-10,-80],[40,-20],[0,0]]);
        linear_extrude(height=1.0) polygon([[0,0],[40,20],[-5,150]]);
        handle(frameHeight);
    }
}

module hoop_quarter(index)
{
    quarters = [[1,1],[-1,1],[-1,-1],[1,-1]];
    x = quarters[index][0];
    y = quarters[index][1];
    intersection(){
        scale([x,y,1]) cube([workareaWidth ,workareaHeight,frameHeight+10]);
        hoop_large();
    }
}

module connector(holeHoffset = 0)
{
    tightnWidth = 30;
    translate([-tightnWidth/2,0,0]) difference(){
        cube([tightnWidth ,12,frameHeight]);
        //screw hole
        translate([tightnWidth,8,frameHeight/2+holeHoffset]) rotate([0,-90,0]) 
        {        
            cylinder(r=1.8, h=tightnWidth+1); cylinder(r=3.5*0.95, h=3, $fn=6);
            translate([0,0,tightnWidth-3]) cylinder(r=3.5, h=3);
        }
    }
}