import time, threading, re
from queue import PriorityQueue

class MyPriorityQueue(PriorityQueue):
    def __init__(self):
        PriorityQueue.__init__(self)
        self.counter = 0

    def put(self, item, priority = 1):
        PriorityQueue.put(self, (priority, self.counter, item))
        self.counter += 1

    def get(self, *args, **kwargs):
        _, _, item = PriorityQueue.get(self, *args, **kwargs)
        return item
    
    def clear(self):
        while not PriorityQueue.empty(self):
            try:
                PriorityQueue.get(self, False)
            except Empty:
                continue
            PriorityQueue.task_done(self)

worker = None
last_pos = [0.0,0.0]
gcode_regexX = re.compile("X(\-?\d+\.?\d+)")
gcode_regexY = re.compile("Y(\-?\d+\.?\d+)")
queue = MyPriorityQueue()

def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    return ["/dev/ttyUSB0"]

def open_serial(port, baud, responseCallback = None):
    print(port, baud)
    if responseCallback:
        responseCallback("Connection establish")
        
    global worker
    worker = SendingThread(None)
    worker.start()
    return True
     

def close_serial():
    global worker
    if worker:
        worker.terminate()

def send_serial(msg, responseCallback = None):
    print(msg)
    time.sleep(0.1)
    global last_pos
    response = "ok\n"
    if "M114" in msg:
        response = "X:%f,Y:%f\nok\n" % (last_pos[0],last_pos[1])
    if "G0" in msg or "G1" in msg:
        regex_result = gcode_regexX.search(msg)
        if regex_result:
            last_pos[0] = float(regex_result.group(1))
        regex_result = gcode_regexY.search(msg)
        if regex_result:
            last_pos[1] = float(regex_result.group(1))
    if responseCallback:
        responseCallback(response)
    return True

def read_serial():
    return "OK"

def queue_command_list(msgs):
    pass
    
def queue_command(msg, responseCallback = None, priority = None):
    global queue
    new_entry = (msg, responseCallback)
    if priority:
        queue.put(new_entry, priority)
    else:
        queue.put(new_entry)

if __name__ == '__main__':
    print(serial_ports())
    
    
class SendingThread(threading.Thread):
    def __init__(self, parent):
        """
        @param parent: The gui object that should recieve the value
        @param value: deque object list of tuples commands strings to send with callbacks
        """
        threading.Thread.__init__(self)
        self._parent = parent
        self.running = True

    def run(self):
        while self.running:
            try:
                # do not wait infinity, use timeout
                msg = queue.get(True, 2)
            except:
                # timeout on empty queue rises exception
                continue
            
            send_serial(msg[0], msg[1])
            queue.task_done()
        
    def terminate(self):
        self.running = False
