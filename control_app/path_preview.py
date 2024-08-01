from tkinter import Canvas, ALL
from operator import itemgetter
import copy, math, re

# a subclass of Canvas for dealing with resizing of windows
class ResizingCanvas(Canvas):
    def __init__(self,parent, area_width=100, area_height=100, **kwargs):
        Canvas.__init__(self,parent,**kwargs)
        parent.bind("<Configure>", self.on_resize)
        self.parent = parent
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()
        self.setArea(area_width, area_height)
        self.pointer = self.create_oval(0, 0, 4, 4)
        self.origin_x = 0
        self.origin_y = 0
        
    def setArea(self, area_width, area_height):
        self.aspect_ratio = area_width / area_height
        # these vars are for work area setup for machine, in mm's
        self.area_height = area_height
        self.area_width = area_width
        self.height_ratio = self.height / self.area_height
        self.width_ratio = self.width / self.area_width
        
    def setOrigin(self, origin_x, origin_y):    
        self.origin_x = origin_x
        self.origin_y = origin_y

    def on_resize(self,event):
        # start by using the width as the controlling dimension
        desired_width = event.width
        desired_height = int(event.width / self.aspect_ratio)

        # if the window is too tall to fit, use the height as
        # the controlling dimension
        if desired_height > event.height:
            desired_height = event.height
            desired_width = int(event.height * self.aspect_ratio)
        # determine the ratio of old width/height to new width/height
        wscale = float(desired_width)/self.width
        hscale = float(desired_height)/self.height
        
        self.width = desired_width
        self.height = desired_height
        self.height_ratio = self.height / self.area_height
        self.width_ratio = self.width / self.area_width
        
        # resize the canvas 
        self.config(width=self.width, height=self.height)
        #self.parent.config(width=self.width, height=self.height)
        # rescale all the objects tagged with the "all" tag
        self.scale("all",0,0,wscale,hscale)
        # print(self.width, self.height)
    
    def clear(self):
        self.delete(ALL)
        self.pointer = self.create_oval(0, 0, 4, 4)
        
    # gcode coordinates into canvas coords
    # takes tuple (x1, y1, x2, y2)
    def calc_coords(self, coords):
        x1 = (coords[0] - self.origin_x) * self.width_ratio
        y1 = self.height - (coords[1] - self.origin_y)*self.height_ratio
        x2 = (coords[2] - self.origin_x) * self.width_ratio
        y2 = self.height - (coords[3] - self.origin_y) * self.height_ratio
        return int(x1), int(y1), int(x2), int(y2)
    
    def canvas_vector_to_machine(self, point):
        return (-point[0]/self.width_ratio, point[1]/self.height_ratio)
    def canvas_point_to_machine(self, point):
        return (point[0]/self.width_ratio + self.origin_x, (self.height - point[1])/self.height_ratio + self.origin_y)
    
    def machine_point_to_canvas(self, point):
        return ((point[0]-self.origin_x) * self.width_ratio, self.height - (point[1] - self.origin_y) * self.height_ratio)
    
    def move_pointer(self, point):
        ''' Moves the circle which indicates current machine position.
            Coords is a 2 element tuple (x1, y1)'''
        x1, y1 = self.machine_point_to_canvas(point)
        self.coords(self.pointer, (x1-2, y1-2, x1+2, y1+2)) # change coordinates
        
    def draw_toolpath(self, points):
        ''' Takes a list of points as tuples: (text_command, x,y) '''
        self.clear()
        if(len(points) < 2):
            return
        last_point = points[0]
        current_color = "black"
        color = current_color
        for point in points:
            if "G0" == point[0]:
                color = "snow2"
            elif "M6" == point[0]:
                current_color = _from_rgb((point[1], point[2], point[3]))
                color = current_color
                continue
            # commands other than G0, G1, G28 or M6 are ignored for drawing a preview
            elif "G1" != point[0] and "G28" != point[0]:
                continue
            coord = (last_point[1], last_point[2], point[1], point[2])
            last_point = point
            line = self.create_line(self.calc_coords(coord), fill=color)
            self.lift(self.pointer, line)
            color = current_color
        #self.move_pointer((0,0,0,0))

# moves list of commands (points) along vector
def translate_toolpath(points, translate=(0,0)):
    #new_points = copy.deepcopy(points)
    for point in points:
        if not ("G0" == point[0] or "G1" == point[0]):
            continue
        point[1] += translate[0]
        point[2] += translate[1]
    return points

def rotate_toolpath(points, origin, theta):
    for point in points:
        if not ("G0" == point[0] or "G1" == point[0]):
            continue
        point[1], point[2] = rotate(point[1:3], origin, theta)
    return points

def rotate(point, origin, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.

    The angle should be given in radians.
    """
    ox, oy = origin
    px, py = point

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return qx, qy

def reflect_toolpath(points, d):
    for point in points:
        if not ("G0" == point[0] or "G1" == point[0]):
            continue
        point[1] = 2*d - point[1]
    return points
    
def scale_toolpath(points, f):
    for point in points:
        if not ("G0" == point[0] or "G1" == point[0]):
            continue
        point[1] += point[1]*f 
        point[2] += point[2]*f
    return points

def toolpath_border_points(points):
    points = [elem for elem in points if "G0" == elem[0] or "G1" == elem[0]]
    x_max = max(points,key=itemgetter(1))[1]
    x_min = min(points,key=itemgetter(1))[1]
    y_max = max(points,key=itemgetter(2))[2]
    y_min = min(points,key=itemgetter(2))[2]
    return ((x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max), (x_min, y_min))

def toolpath_info(points):
    ''' returns info such as total number of tool points, number of tool changes, tool distances between tool changes'''
    last_point = None
    total_distance = 0
    tool_changes = 0
    distances = []
    for point in points:
        if not ("G0" == point[0] or "G1" == point[0]):
            if "M6" == point[0]:
                tool_changes += 1
                distances.append(total_distance)
            continue
        if last_point and "G1" == point[0]:
            total_distance += math.hypot(point[1] - last_point[1], point[2] - last_point[2])
        last_point = point
    distances.append(total_distance)
    return sum(el[0] == "G1" for el in points), tool_changes, distances

def load_csv_file(csvfile, offset=(0,0)):
    ''' loads csv textfile, takes opended file handler and toolpath offset
    returns list of commands for machine'''
    import csv
    
    #dialect = csv.Sniffer().sniff(csvfile.read(1024))
    #csvfile.seek(0)
    #reader = csv.reader(csvfile, dialect)
    reader = csv.reader(csvfile, delimiter=',')
    command = "G0"
    commands = []
    colors = []
    last_color = None
    current_color = None

    # we can use both CSV generated by EmbroiderModder or PyEmbroidery,
    # but they have different colomns order
    #   pyembrodery csv:
    #       |"#","[STITCH_INDEX]","[STITCH_TYPE]","[X]","[Y]"
    #       |"*","0","JUMP","-24","69"
    #   embroider-modder csv:
    #       |"*","JUMP","-5.385269","-8.848681"
    #   embird csv:
    #       |#*STITCH,XX,YY,DX,DY,LENGTH,ANGLE,dANGLE
    #       |*JUMP,-12.500000,-3.100000,-12.500000,-3.100000,12.878665,-999.000000,-999.000000
    format_detected = False
    MULTIPLY = 1.0/10 #? pyembroidery give 1mm, 
    FLAG,IOFFSET,CMD,X,Y = range(5) #? pyembrodery csv:
    
    # load each point into commands list
    for row in reader:
        # empyt row
        if len(row) <= 0:
            continue
        if '*' == row[FLAG][0]:
            if not format_detected:
                if len(row[FLAG])>1:
                    CMD,X,Y = range(3) #? embird csv
                    MULTIPLY = 1
                else:
                    try:
                        float(row[1])
                    except:
                        FLAG,CMD,X,Y = range(4) #? embroider-modder csv:
                format_detected = True

            if 'JUMP' in row[CMD]:
                command = "G0"
            elif 'STITCH' in row[CMD]:
                command = "G1"
            elif 'COLOR' in row[CMD]:
                command = "M6"
                if len(colors) > 0:
                    current_color = colors.pop(0)
                else:
                    current_color = (0,0,0)
                # colors are truly different
                if current_color != last_color:
                    commands.append([command, *current_color])
                last_color = current_color
                continue
            elif 'TRIM' in row[CMD]:
                command = "G12"
                commands.append([command, ])
                continue
            elif 'END' in row[CMD]:
                continue
            print('ROW:',repr(row))
            commands.append([command, 
                             float(row[X].replace(",","."))*MULTIPLY+offset[0], 
                             float(row[Y].replace(",","."))*MULTIPLY+offset[1]])
        elif '$' == row[FLAG]:
            if row[2].startswith('#'):
                rgb = hex_to_rgb(row[2])
            else:
                rgb = (int(row[2]), int(row[3]), int(row[4]))
            # colors.append((int(row[2]), int(row[3]), int(row[4])))
            colors.append(rgb)
            #print(', '.join(row))
    csvfile.close()
    #return [("G28", 0,0),("G0",100,100),("G1", 110,150)]
    return commands
def save_csv_file(f, commands):
    pass

def hex_to_rgb(hex_color):
    # Menghapus tanda #
    hex_color = hex_color.lstrip('#')
    # Memecah menjadi komponen RGB
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return list(rgb)
   
def load_gcode_file(f):
    result = []
    regexNumber = re.compile("(\-?\d+\.?\d+)")
    regexGcode = re.compile("([G,M]\d+)\s+?([X,Y,F,R,G,B]\-?\d+\.?\d+)?\s+?([X,Y,F,R,G,B,F]\-?\d+\.?\d+)?\s+?([X,Y,F,R,G,B]\-?\d+\.?\d+)?")
    
    line = f.readline()
    while line:
        line = line.upper()
        regexResult = regexGcode.search(line)
        if regexResult:
            params = (regexResult.group(2), regexResult.group(3), regexResult.group(4))
            command = [regexResult.group(1), 0, 0]
            for param in params:
                if not param:
                    continue
                if "X" in param:
                    command[1] = float(regexNumber.search(param).group(1))
                if "Y" in param:
                    command[2] = float(regexNumber.search(param).group(1))
                if "F" in param:
                    command.append(float(regexNumber.search(param).group(1)))
                if "R" in param:
                    command[1] = int(regexNumber.search(param).group(1))
                if "G" in param:
                    command[2] = int(regexNumber.search(param).group(1))
                if "B" in param:
                    command.append(int(regexNumber.search(param).group(1)))
            
            result.append(command)
        line = f.readline()
    
    return result

def save_gcode_file(f, commands):
    for command in commands:
        if "M6" == command[0]:
            command = "%s R%d G%d B%d\n" % (command[0], command[1], command[2], command[3])
        elif "G0" == command[0] or "G1" == command[0]:
            if len(command) > 3:
                command = "%s X%f Y%f F%f\n" % (command[0], command[1], command[2], command[3])
            else:
                command = "%s X%f Y%f\n" % (command[0], command[1], command[2])
        else:
            command = "%s\n" % command[0]
        f.write(command)
    f.close()

def _from_rgb(rgb):
    """Translates an rgb tuple of int to a tkinter friendly color code """
    return "#%02x%02x%02x" % rgb   
