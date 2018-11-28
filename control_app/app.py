#!/usr/bin/python3

from tkinter import Tk, Label, Button, Checkbutton, Entry, Menu, filedialog, messagebox, colorchooser, Canvas, Frame, LabelFrame, Scale, Toplevel, PhotoImage, IntVar
from tkinter.font import Font
import tkinter.ttk as ttk
from tkinter import LEFT, TOP, BOTTOM, N, YES, W,SUNKEN,X, HORIZONTAL, DISABLED, NORMAL, RAISED, FLAT, RIDGE, END
from path_preview import ResizingCanvas, load_gcode_file, save_gcode_file, load_csv_file, translate_toolpath, rotate_toolpath, reflect_toolpath, scale_toolpath, toolpath_border_points, toolpath_info, _from_rgb
from collections import namedtuple
import copy, re, math, time, pickle, sys

if len(sys.argv) > 1 and sys.argv[1] == "debug":
    import control_serial_mockup as serial
else:
    import control_serial as serial

class ControlAppGUI:
    def __init__(self, master):
        self.master = master
        # GUI layout setup
        self.menu = Menu(self.master)

        self.master.config(menu=self.menu)
        master.grid_rowconfigure(0, weight=1)
        master.grid_columnconfigure(0, weight=1)
        filemenu = Menu(self.menu)
        self.menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="New", command=self.NewFile)
        openmenu = Menu(self.menu)
        openmenu.add_command(label="Gcode", command=self.OpenGcodeFile)
        openmenu.add_command(label="CSV", command=self.OpenCsvFile)
        savemenu = Menu(self.menu)
        savemenu.add_command(label="Gcode", command=self.SaveGcodeFile)
        savemenu.add_command(label="CSV", command=self.SaveCsvFile)
        filemenu.add_cascade(label='Open...', menu=openmenu, underline=0)
        filemenu.add_cascade(label="Save...", menu=savemenu, underline=0)
        #filemenu.add_command(label="Reload current file", command=None)
        filemenu.add_command(label="Set color", command=self.AskColor)
        filemenu.add_separator()
        def updatePortList():
            ports = serial.serial_ports()
            self.portCombo['values'] = ports
            if len(ports) > 0:
                self.portCombo.current(0)
        filemenu.add_command(label="Refresh port list", command=updatePortList)
        filemenu.add_command(label="Exit", command=self.Quit)

        editmenu = Menu(self.menu)
        self.menu.add_cascade(label="Edit", menu=editmenu)
        editmenu.add_command(label="Settings", command=self.Settings)
        
        helpmenu = Menu(self.menu)
        self.menu.add_cascade(label="Help", menu=helpmenu)
        helpmenu.add_command(label="About...", command=self.About)
        master.title("Embroiderino frontend")
        
        self.controls = ttk.Notebook(master)
        tab1 = Frame(self.controls)
        tab2 = Frame(self.controls)
        self.controls.add(tab1, text = "Machine control")
        self.controls.add(tab2, text = "Path manipulation")
        self.controls.grid(row=0,column=1, sticky=N)
        self.controls.grid_rowconfigure(0, weight=1)
        self.controls.grid_columnconfigure(0, weight=1)
        
        # MACHINE TAB
        ports = serial.serial_ports()
        self.portCombo = ttk.Combobox(tab1,  values=ports)
        if len(ports) > 0:
            self.portCombo.current(0)
        self.portCombo.grid(row=1,column=0)
        self.baudCombo = ttk.Combobox(tab1,state='readonly',  values=("115200", "9600"), width=10)
        self.baudCombo.current(0)
        self.baudCombo.grid(row=1,column=1)
        self.connectButton = Button(tab1, text="Connect", command=self.ToggleConnect, width=10)
        self.connectButton.grid(row=1,column=2)

        self.startButton = Button(tab1, text="Start job", command=self.ToggleStart, state=DISABLED)
        self.startButton.grid(row=2,column=1)
        self.homeButton = Button(tab1, text="Home machine", command=lambda: serial.queue_command("G28\n"), state=DISABLED)
        self.homeButton.grid(row=2,column=0)
        
        testNavigation = Frame(tab1)
        leftButton = Button(testNavigation, text="<", command=lambda: serial.queue_command("G91\nG0 X-2\nG90\n"), state=DISABLED)
        leftButton.grid(row=1,column=0)
        rightButton = Button(testNavigation, text=">", command=lambda: serial.queue_command("G91\nG0 X2\nG90\n"), state=DISABLED)
        rightButton.grid(row=1,column=2)
        upButton = Button(testNavigation, text="/\\", command=lambda: serial.queue_command("G91\nG0 Y2\nG90\n"), state=DISABLED)
        upButton.grid(row=0,column=1)
        downButton = Button(testNavigation, text="\\/", command=lambda: serial.queue_command("G91\nG0 Y-2\nG90\n"), state=DISABLED)
        downButton.grid(row=2,column=1)
        testNavigation.grid(row=3,column=0)
        self.navigationButtons = [leftButton, rightButton, upButton, downButton]
        
        self.testButton = Button(tab1, text="Test border path", command=self.TestBorder, state=DISABLED)
        self.testButton.grid(row=3,column=1)
        
        self.gotoButton = Button(tab1, text="Go to", command=self.GoTo, state=DISABLED, relief=RAISED)
        self.gotoButton.grid(row=3,column=2)
        
        self.stopButton = Button(tab1, text="STOP", command=self.StopAll, state=DISABLED)
        self.stopButton.grid(row=4,column=0)
        
        self.pauseOnToolChange = IntVar()
        self.pauseOnTrim = IntVar()
        self.toolChangeCheck = Checkbutton(tab1, variable=self.pauseOnToolChange, onvalue=1, offvalue=0, text="Pause on tool change")
        self.toolChangeCheck.grid(row=4,column=1)
        self.toolChangeCheck.select()
        self.trimCheck = Checkbutton(tab1, variable=self.pauseOnTrim, onvalue=1, offvalue=0, text="Pause on trim")
        self.trimCheck.grid(row=4,column=2)
        self.trimCheck.select()
                
        progressFrame = Frame(tab1)
        Label(progressFrame, text="Tool changes: ", bd=1).grid(row=0,column=0, pady = (10, 1))
        self.toolChangesLabel = Label(progressFrame, text="0/0", bd=1, relief=SUNKEN)
        self.toolChangesLabel.grid(row=1,column=0)
        
        Label(progressFrame, text="Tool points: ", bd=1).grid(row=0,column=2, pady = (10, 1))
        self.toolPointsLabel = Label(progressFrame, text="0/0", bd=1, relief=SUNKEN)
        self.toolPointsLabel.grid(row=1,column=2)
        
        Label(progressFrame, text="Estimated endtime: ", bd=1).grid(row=0,column=4, pady = (10, 1))
        self.timeLabel = Label(progressFrame, text="0/0", bd=1, relief=SUNKEN)
        self.timeLabel.grid(row=1,column=4)
        progressFrame.grid(row=5,column=0, columnspan=3)
        
        colorsFrame = Frame(tab1, bd=1)
        colorsFrame.grid(row=6, column=0, columnspan=3, pady = (10, 1))
        Label(colorsFrame, text="Current color: ", bd=1).pack(side=LEFT)
        self.currentColorIndicator = Label(colorsFrame, text="    ", relief=RAISED, bd=1)
        self.currentColorIndicator.pack(side=LEFT, padx=(1,40))
        Label(colorsFrame, text="Next color: ", bd=1).pack(side=LEFT, padx=2)
        self.nextColorIndicator = Label(colorsFrame, text="    ", relief=RAISED, bd=1)
        self.nextColorIndicator.pack(side=LEFT)
        
        Label(tab1, text="SPM speed limit: ", bd=1).grid(row=7, column=0)
        self.speedSlider = Scale(tab1, from_=80, to=800, command=None, orient=HORIZONTAL,length=200)
        self.speedSlider.set(400)
        self.speedSlider.bind("<ButtonRelease-1>", lambda _: serial.queue_command("M222 S%d\n" % self.speedSlider.get(), priority = -1))
        self.speedSlider.grid(row=7, column=1, columnspan=2)
        

        # PATH TAB
        tab2.grid_columnconfigure(0, weight=1)
        Label(tab2, text="Display progress: ", bd=1).grid(row=0)
        self.slider = Scale(tab2, from_=0, to=0, command=self.UpdatePath, orient=HORIZONTAL,length=300)
        self.slider.grid(row=1)

        toolbar = Frame(tab2, bd=1, relief=RAISED)
        toolbar.grid(row=2)
        self.panButton = Button(toolbar, relief=RAISED, command=self.TogglePan, text="Move path")
        self.panButton.pack(side=LEFT, padx=2, pady=2)
        
        self.rotateButton = Button(toolbar, relief=RAISED, command=self.ToggleRotate, text="Rotate path")
        self.rotateButton.pack(side=LEFT, padx=2, pady=2)
        
        self.mirrorButton = Button(toolbar, relief=RAISED, command=self.ToggleMirror, text="Mirror path")
        self.mirrorButton.pack(side=LEFT, padx=2, pady=2)
        
        self.scaleButton = Button(toolbar, relief=RAISED, command=self.ToggleScale, text="Scale path")
        self.scaleButton.pack(side=LEFT, padx=2, pady=2)
        
        # CANVAS
        canvasFrame = Frame(master)
        canvasFrame.grid(row=0, column=0, sticky='NWES')
        self.canvas = ResizingCanvas(canvasFrame,width=400, height=400, bg="white", highlightthickness=0)
        self.canvas.bind("<B1-Motion>", self.CanvasDrag)
        self.canvas.bind("<Button-1>", self.CanvasClick)
        self.canvas.bind("<ButtonRelease-1>", self.CanvasRelease)
        self.canvas.pack(expand=YES, anchor=N+W)
        
        #STATUS BAR
        self.status = Label(master, text="Not connected", bd=1, relief=SUNKEN, anchor=W)
        self.status.grid(row=2, columnspan=2, sticky='WE')
        
        # PROGRAM VARIABLES
        self.SETTINGSFNAME = "settings.pickle"
        self.commands = []
        self.transform = (0,0)
        self.isConnected = False
        self.isJobRunning = False
        self.isJobPaused = False
        self.lastSendCommandIndex = -1
        self.lastMove = None
        self.currentColor = 'black'
        self.currentToolChange = 0
        self.toolChangesTotal = 0
        self.currentToolPoint = 0
        self.toolPointsTotal = 0
        self.distancesList = []
        self.distanceTraveled = 0
        self.positionResponseRegex = re.compile("X:(\-?\d+\.\d+),Y:(\-?\d+\.\d+)")
        self.machineSetups = {}
        self.currentSetupName = None
        self.workAreaSize = [100,100]
        self.workAreaOrigin = [0,0]
        
        # LOAD SOME SETTIGS
        self.loadSettings()
        self.canvas.setArea(self.workAreaSize[0], self.workAreaSize[1])
        self.canvas.setOrigin(self.workAreaOrigin[0], self.workAreaOrigin[1])
        
    # UI LOGIC
    def Quit(self):
        if messagebox.askyesno('Confirm', 'Really quit?'):
            self.master.quit()
            return True
        return False
    def AskColor(self):
        color = colorchooser.askcolor(title = "Colour Chooser")
    def NewFile(self):
        if self.isJobRunning:
            return
        self.toolChangesTotal = 0
        self.toolPointsTotal = 0
        self.distancesList = []
        self.lastSendCommandIndex = -1
        self.lastMove = None
        self.commands = []
        self.canvas.clear()
        self.slider.config(to=0)
    def OpenGcodeFile(self):
        if self.isJobRunning:
            return
        with filedialog.askopenfile(filetypes = (("Machine G-code","*.gcode"),)) as f:
            self.commands = load_gcode_file(f)
            self.FinishLoading()
    def SaveGcodeFile(self):
        if not self.commands:
            return
        with filedialog.asksaveasfile(filetypes = (("Machine G-code","*.gcode"),), defaultextension='.gcode') as f:
            save_gcode_file(f, self.commands)
    def OpenCsvFile(self):
        if self.isJobRunning:
            return
        with filedialog.askopenfile(filetypes = (("Comma separated values","*.csv"),) ) as f:
            self.commands = load_csv_file(f)
            self.FinishLoading()
    def SaveCsvFile(self):
        pass
    def FinishLoading(self):
        points_count = len(self.commands)
        # file loaded
        if points_count > 2:
            self.testButton.config(state=NORMAL)
            self.startButton.config(state=NORMAL)
            # prepare color indicators
            self.currentColorIndicator.configure(background=self.currentColor)
            self.currentColorIndicator.configure(background=None)
            # center loaded path
            rectangle = toolpath_border_points(self.commands)
            rwidth = rectangle[2][0] - rectangle[0][0]
            rheight = rectangle[2][1] - rectangle[0][1]
            center = (rectangle[2][0] - (rwidth)/2, rectangle[2][1] - (rheight)/2)
            transform = (self.workAreaSize[0]/2 - center[0] + self.workAreaOrigin[0], self.workAreaSize[1]/2 - center[1] + self.workAreaOrigin[1])
            self.commands = translate_toolpath(self.commands, transform)        
            # check if  design is bigger than available workarea
            if(rwidth > self.workAreaSize[0] or rheight > self.workAreaSize[1]):
                messagebox.showinfo('Size Warning!', "Looks like this design is bigger than available work area.")
                
        self.slider.config(to=points_count)
        self.slider.set(points_count)
        self.toolPointsTotal, self.toolChangesTotal, self.distancesList = toolpath_info(self.commands)
        self.toolPointsLabel.config(text="%d/%d" % (self.currentToolPoint, self.toolPointsTotal))
        self.toolChangesLabel.config(text="%d/%d" % (self.currentToolChange, self.toolChangesTotal))
        self.UpdateTimeEstLabel()
        self.canvas.draw_toolpath(self.commands)
    
    def About(self):
        #self.PausePopup()
        messagebox.showinfo('About this software', 'This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.\n\nThis program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.\n\nWritten in 2018 by markol.')
    def Settings(self):
        tl = Toplevel(root)
        tl.title("Global settings")

        frame = Frame(tl)
        frame.grid()

        machineFrame = LabelFrame(frame, text="Machine hoop workarea (mm)", relief=RIDGE)
        machineFrame.grid()
        Label(machineFrame, text="width " ).grid(row=0, column=0, sticky=N)
        workareaWidth = Entry(machineFrame, text="1")
        workareaWidth.grid(row=0,column=1)
        Label(machineFrame, text="height " ).grid(row=2, column=0, sticky=N)
        workareaHeight = Entry(machineFrame, text="2")
        workareaHeight.grid(row=2,column=1)
        hoopFrame = LabelFrame(frame, text="Machine hoop origin (mm)", relief=RIDGE)
        hoopFrame.grid()
        Label(hoopFrame, text="X " ).grid(row=0, column=0, sticky=N)
        workareaOriginX = Entry(hoopFrame, text="3")
        workareaOriginX.grid(row=0,column=1)
        Label(hoopFrame, text="Y " ).grid(row=2, column=0, sticky=N)
        workareaOriginY = Entry(hoopFrame, text="4")
        workareaOriginY.grid(row=2,column=1)
        Label(hoopFrame, text="Setup name " ).grid(row=3, column=0, sticky=N)
        setupName = Entry(hoopFrame, text="Setup1")
        setupName.grid(row=3,column=1)
        
        def setupSelected(event = None):
            if event:
                selectedSetupName = setupsCombo.get()
            else:
                selectedSetupName = self.currentSetupName
                
            workareaWidth.delete(0, END)
            workareaWidth.insert(0, str(self.machineSetups[selectedSetupName]["workAreaSize"][0]))
            workareaHeight.delete(0, END)
            workareaHeight.insert(0, str(self.machineSetups[selectedSetupName]["workAreaSize"][1]))
            workareaOriginX.delete(0, END)
            workareaOriginX.insert(0, str(self.machineSetups[selectedSetupName]["workAreaOrigin"][0]))
            workareaOriginY.delete(0, END)
            workareaOriginY.insert(0, str(self.machineSetups[selectedSetupName]["workAreaOrigin"][1]))
            setupName.delete(0, END)
            setupName.insert(0, selectedSetupName)
        setupSelected()
            
        setupsCombo = ttk.Combobox(frame, values=list(self.machineSetups.keys()), state="readonly")
        setupsCombo.grid(row=2, column=0)
        setupsCombo.current(setupsCombo['values'].index(self.currentSetupName))
        setupsCombo.bind("<<ComboboxSelected>>", setupSelected)
        def addSettings():
            newSetupName = setupName.get()
            
            if newSetupName in self.machineSetups.keys():
                if not messagebox.askyesno("Machine setup exists","Machine setup with this name exists. Overwrite?"):
                    return
            newSetup = {
                        "workAreaSize": (int(workareaWidth.get()), int(workareaHeight.get())), 
                        "workAreaOrigin": (int(workareaOriginX.get()), int(workareaOriginY.get()))
                       }
            self.machineSetups[newSetupName] = newSetup
            setupsCombo['values'] =  list(self.machineSetups.keys())
                
            
        Button(frame, relief=RAISED, command=addSettings, text="Add setup").grid(row=2, column=1)
        def removeSetup():
            self.machineSetups.pop(setupsCombo.get(), None)
            options = list(self.machineSetups.keys())
            setupsCombo['values'] =  options
            if len(options) > 0:
                self.currentSetupName = list(self.machineSetups.keys())[0]
                setupsCombo.current(0)
                setupSelected(1)
        Button(frame, relief=RAISED, command=removeSetup, text="Remove setup").grid(row=2, column=2)
        
        def saveSettings():
            try:
                if len(setupsCombo.get()) > 0:
                    self.workAreaSize = (int(workareaWidth.get()), int(workareaHeight.get()))
                    self.workAreaOrigin = (int(workareaOriginX.get()), int(workareaOriginY.get()))
                    self.currentSetupName = setupsCombo.get()
            except:
                messagebox.showerror("Invalid numeric values","Please provide correct workarea values!")
                return
                
            self.canvas.setArea(self.workAreaSize[0], self.workAreaSize[1])
            self.canvas.setOrigin(self.workAreaOrigin[0], self.workAreaOrigin[1])
            self.storeSettings()
            TmpDim = namedtuple('TmpDim', 'width height')
            tmp = TmpDim(self.canvas.width, self.canvas.height)
            self.canvas.on_resize(tmp)
            
        Button(frame, text="Save", command=saveSettings, width=10).grid(row=3, column=3)
        Button(frame, text="Close", command=lambda: tl.destroy(), width=10).grid(row=3, column=2)
        
    def loadSettings(self):
        try:
            with open(self.SETTINGSFNAME, "rb") as f:
                data = pickle.load(f)
            self.machineSetups = data["machineSetups"]
            self.currentSetupName = data["currentSetupName"]
            self.workAreaSize = self.machineSetups[self.currentSetupName]["workAreaSize"]
            self.workAreaOrigin = self.machineSetups[self.currentSetupName]["workAreaOrigin"]
        except Exception as e:
            print ("Unable to restore program settings:", str(e))
        
    def storeSettings(self):
        with open(self.SETTINGSFNAME, "wb") as f:
            try:
                data = {"machineSetups": self.machineSetups, "currentSetupName": self.currentSetupName}
                pickle.dump(data, f)
            except Exception as e:
                print ("Error while saving settings:", str(e))
            
    def ToggleConnect(self):
        if self.isConnected:
            serial.close_serial()
            self.connectButton.config(text="Connect")
            self.status.config(text="Not connected")
            self.homeButton.config(state=DISABLED)
            self.stopButton.config(state=DISABLED)
            self.gotoButton.config(state=DISABLED)
            self.SetNavButtonsState(False)
            self.isConnected = False
        else:
            if serial.open_serial(self.portCombo.get(), self.baudCombo.get()):
                self.connectButton.config(text="Disconnect")
                self.status.config(text="Connected")
                self.homeButton.config(state=NORMAL)
                self.stopButton.config(state=NORMAL)
                self.gotoButton.config(state=NORMAL)
                self.SetNavButtonsState(True)
                self.isConnected = True
                self.GetPositionTimerTaks()

    def TestBorder(self):
        rectangle = toolpath_border_points(self.commands)
        for point in rectangle:
            serial.queue_command("G0 X%f Y%f F5000\n" % point)
    
    def ToggleStart(self):
        if self.isJobPaused:
            serial.queue.clear()
            self.startButton.config(text="Resume job")
            self.status.config(text="Job paused")
        else:
            self.startButton.config(text="Pause job")
            self.status.config(text="Job in progress")
            startInstructionIndex = self.lastSendCommandIndex + 1
            # job launch
            if not self.isJobRunning:
                self.canvas.clear()
                startInstructionIndex = 0
                self.start = time.time()
                serial.queue_command("G0 F15000\n")
                
            self.isJobRunning = True
            self.QueueCommandsBlock(startInstructionIndex)
            
        self.isJobPaused = not self.isJobPaused
            
    def QueueCommandsBlock(self, startInstructionIndex):
        commandsCount = len(self.commands)
            
        def progressCallback(instruction_index):
            ''' after every move G0 or G1 or G28 command being sent, this callback is executed '''
            point = self.commands[instruction_index]
            if self.lastMove:                       
                coord = (self.lastMove[1], self.lastMove[2], point[1], point[2])
                color = self.currentColor
                # set color for jump move
                if "G0" == point[0] or "G28" == point[0]:
                    color = "snow2"
                else:
                    self.currentToolPoint += 1
                    self.toolPointsLabel.config(text="%d/%d" % (self.currentToolPoint, self.toolPointsTotal))
                    # calculate distance for material usage
                    self.distanceTraveled += math.hypot(coord[0] - coord[2], coord[1] - coord[3])
                # draw new line on canvas
                line = self.canvas.create_line(self.canvas.calc_coords(coord), fill=color)
                self.canvas.lift(self.canvas.pointer, line)
                self.UpdateTimeEstLabel()
            # store next start point and instruction index 
            self.lastSendCommandIndex = instruction_index
            self.lastMove = point
            
            # update status bar
            if self.currentToolPoint % 10 == 0:
                progress = instruction_index / commandsCount * 100
                self.status.config(text="Job in progress %.1f%%" % progress)
        
        def progressPauseCallback(instruction_index, trim = False):
            ''' this callback pauses the job '''
            point = self.commands[instruction_index]
            self.lastSendCommandIndex = instruction_index
            # pause on color change
            if not trim:
                self.currentColor = _from_rgb((point[1], point[2], point[3]))
                self.currentToolChange += 1
                self.currentColorIndicator.configure(background=self.currentColor)
                self.toolChangesLabel.config(text="%d/%d" % (self.currentToolChange, self.toolChangesTotal))
                # pause enabled or not
                if self.pauseOnToolChange.get() == 1:
                    self.ToggleStart()
                    self.PausePopup(self.currentColor)
                else:
                    self.QueueCommandsBlock(self.lastSendCommandIndex + 1)
            # pause on trim
            else:
                # pause enabled or not
                if self.pauseOnTrim.get() == 1:
                    self.ToggleStart()
                    self.PausePopup(self.currentColor, trim)
                else:
                    self.QueueCommandsBlock(self.lastSendCommandIndex + 1)
        
        # all the commands until next tool change command, are queued at once
        # unsupported commands are ignored
        for i in range(startInstructionIndex, commandsCount):
            point = self.commands[i]
            # pause on color change
            if "M6" == point[0]:
                serial.queue_command("M6\n", lambda _, index = i: progressPauseCallback(index))
                self.nextColorIndicator.configure(background=_from_rgb((point[1], point[2], point[3])))
                break
            # pause on trim
            elif "G12" == point[0]:
                # if next command is a color change, there is no need to pause now
                if i < commandsCount + 1 and self.commands[i+1][0] == "M6" and self.pauseOnToolChange.get() == 1:
                    serial.queue_command("G12\n")
                else:
                    serial.queue_command("G12\n", lambda _, index = i: progressPauseCallback(index, trim = True))
                    break
            elif "G1" == point[0] or "G0" == point[0] or "G28" == point[0]:
                serial.queue_command("%s X%f Y%f\n" % (point[0],point[1], point[2]), lambda _, index = i: progressCallback(index))
        # queue job finish callback
        if i + 1 >= commandsCount:
            serial.queue_command("M114\n", self.JobFinished)
        
    def SetNavButtonsState(self, enabled = False):
        newState = NORMAL if enabled else DISABLED
        for b in self.navigationButtons:
            b.config(state=newState)
    def TogglePan(self):
        self.rotateButton.config(relief=RAISED)
        self.scaleButton.config(relief=RAISED)
        if self.isJobRunning:
            return
        if self.panButton.config('relief')[-1] == SUNKEN:
            self.panButton.config(relief=RAISED)
        else:
            self.panButton.config(relief=SUNKEN)
    def ToggleRotate(self):
        self.panButton.config(relief=RAISED)
        self.scaleButton.config(relief=RAISED)
        if self.isJobRunning:
            return
        if self.rotateButton.config('relief')[-1] == SUNKEN:
            self.rotateButton.config(relief=RAISED)
        else:
            self.rotateButton.config(relief=SUNKEN)
    def ToggleMirror(self):
        self.panButton.config(relief=RAISED)
        self.rotateButton.config(relief=RAISED)
        self.scaleButton.config(relief=RAISED)
        if self.isJobRunning:
            return
        self.commands = reflect_toolpath(self.commands, self.workAreaSize[0]/2 + self.workAreaOrigin[0])
        self.canvas.draw_toolpath(self.commands[0:int(self.slider.get())])
    def ToggleScale(self):
        self.panButton.config(relief=RAISED)
        self.rotateButton.config(relief=RAISED)
        self.mirrorButton.config(relief=RAISED)
        if self.isJobRunning:
            return
        if self.scaleButton.config('relief')[-1] == SUNKEN:
            self.scaleButton.config(relief=RAISED)
        else:
            self.scaleButton.config(relief=SUNKEN)
    def GoTo(self):
        if self.isJobRunning:
            return
        if self.gotoButton.config('relief')[-1] == SUNKEN:
            self.gotoButton.config(relief=RAISED)
        else:
            self.gotoButton.config(relief=SUNKEN)
    def StopAll(self):
        serial.queue.clear()
        self.JobFinished(False)
        self.status.config(text="Job stopped on user demand")
        
    def JobFinished(self, messagePopup = True):
        self.isJobRunning = False
        self.isJobPaused = False
        self.lastSendCommandIndex = -1
        self.lastMove = None
        self.distanceTraveled = 0
        self.currentToolChange = 0
        self.currentToolPoint = 0
        self.currentColor = 'black'
        self.toolPointsLabel.config(text="%d/%d" % (self.currentToolPoint, self.toolPointsTotal))
        self.toolChangesLabel.config(text="%d/%d" % (self.currentToolChange, self.toolChangesTotal))
        self.UpdateTimeEstLabel()
        self.startButton.config(text="Start job")
        self.status.config(text="Job finished")
        timeTaken = time.time() - self.start
        # non blocking popup messagebox
        if messagePopup:
            tl = Toplevel(root)
            # this pop-up is always on top and other windows are deactivated
            tl.attributes('-topmost', 'true')
            tl.title("Job finished")
            tl.grab_set()
            frame = Frame(tl)
            frame.grid()
            Label(frame, text='Current job is finished and took %s.' % time.strftime("%H hours, %M minutes, %S seconds", time.gmtime(timeTaken)) ).grid(row=0, column=0, sticky=N)
            Button(frame, text="OK", command=lambda: tl.destroy(), width=10).grid(row=1, column=0)
            
        
    def CanvasClick(self, event):
        if self.isJobRunning:
            return
        self.dragStart = [event.x, event.y]
        #self.transform = math.atan2(event.x, event.y)
        self.transform = 0
        # go to
        if self.gotoButton.config('relief')[-1] == SUNKEN:
            point = self.canvas.canvas_point_to_machine(self.dragStart)
            serial.queue_command("G0 X%f Y%f\n" % point)
        #print("Clicked at: ", self.dragStart)
    def CanvasRelease(self, event):
        if self.isJobRunning:
            return
            
        print ("Applied transform", self.transform)
    def CanvasDrag(self, event):
        if self.isJobRunning:
            return
        vect = (self.dragStart[0]-event.x, self.dragStart[1]-event.y)
        # move event
        if self.panButton.config('relief')[-1] == SUNKEN:
            self.transform = self.canvas.canvas_vector_to_machine(vect)
            self.commands = translate_toolpath(self.commands, self.transform)
            self.canvas.draw_toolpath(self.commands[0:int(self.slider.get())])
            self.dragStart[0] = event.x
            self.dragStart[1] = event.y
        # rotate event
        if self.rotateButton.config('relief')[-1] == SUNKEN:
            angle = math.atan2(vect[0], vect[1]) # atan2(y, x) or atan2(sin, cos)
            self.commands = rotate_toolpath(self.commands, (self.workAreaSize[0]/2 + self.workAreaOrigin[0],self.workAreaSize[1]/2 + self.workAreaOrigin[1]), -(self.transform-angle))
            self.canvas.draw_toolpath(self.commands[0:int(self.slider.get())])
            self.transform = angle
        # scale event
        if self.scaleButton.config('relief')[-1] == SUNKEN:
            factor = math.sqrt((vect[0])**2 + (vect[1])**2) / 500 
            f = factor - self.transform
            if vect[0] < 0:
                f = -f
            self.commands = scale_toolpath(self.commands, f)
            self.canvas.draw_toolpath(self.commands[0:int(self.slider.get())])
            self.transform = factor
    def UpdatePath(self, val):
        if self.isJobRunning:
            return
        self.canvas.draw_toolpath(self.commands[0:int(val)])
    def UpdateTimeEstLabel(self):
        # avg milimeters per second factor
        factor = 11.0
        time_to_toolchange = (self.distancesList[self.currentToolChange]- self.distanceTraveled) / factor
        time_total = (self.distancesList[-1]-self.distanceTraveled) / factor
        self.timeLabel.config(text="%d m %d s/%d m %d s" % (time_to_toolchange / 60, time_to_toolchange % 60, time_total / 60, time_total % 60))
    def GetPositionTimerTaks(self):
        if self.isConnected:
           def TimerCallback(response):
               response = self.positionResponseRegex.search(response)
               if response:
                   pos = (float(response.group(1)), float(response.group(2)))
                   self.canvas.move_pointer(pos)
               
           serial.queue_command("M114\n", TimerCallback,  priority = -1)
           self.master.after(2000, self.GetPositionTimerTaks)
    
    def CleanUp(self):
        serial.close_serial()
        
    def PausePopup(self, newColor = "black", trim = False):
        tl = Toplevel(root)
        tl.attributes('-topmost', 'true')
        tl.grab_set()
        
        tl.title("Tool change")
        msg = "change the tool for a next color"
        if trim:
            tl.title("Thread trim")
            msg = "cut the thread"

        frame = Frame(tl)
        frame.grid()

        canvas = Canvas(frame, width=64, height=64)
        canvas.grid(row=2, column=0)
        canvas.create_rectangle(0, 0, 65, 65, fill=newColor)
        msgbody = Label(frame, text="There is the moment to %s. Resume the current job after change." % msg)
        msgbody.grid(row=1, column=0, sticky=N)

        okbttn = Button(frame, text="OK", command=lambda: tl.destroy(), width=10)
        okbttn.grid(row=2, column=2)

root = Tk()
my_gui = ControlAppGUI(root)
def on_closing():
    if my_gui.Quit():
        my_gui.CleanUp()
        root.destroy()
    
root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()

