import sys
import glob
import serial 
import time, threading
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

    def peek(self):
        if not self.empty():
            return self.queue[0][2]
        else:
            return None


ser = serial.Serial()
lock = threading.Lock()
worker = None

queue = MyPriorityQueue()

def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

def open_serial(port, baud, responseCallback = None):
    #initialization and open the port
    #possible timeout values:
    #    1. None: wait forever, block call
    #    2. 0: non-blocking mode, return immediately
    #    3. x, x is bigger than 0, float allowed, timeout block call
    ser.port = port
    ser.baudrate = baud
    ser.bytesize = serial.EIGHTBITS #number of bits per bytes
    ser.parity = serial.PARITY_NONE #set parity check: no parity
    ser.stopbits = serial.STOPBITS_ONE #number of stop bits
    ser.timeout = None          #block read
    #ser.timeout = 1            #non-block read
    #ser.timeout = 2              #timeout block read
    ser.xonxoff = True     #disable software flow control
    ser.rtscts = False     #disable hardware (RTS/CTS) flow control
    ser.dsrdtr = False       #disable hardware (DSR/DTR) flow control
    ser.writeTimeout = 2     #timeout for write

    try: 
        ser.open()
        if responseCallback:
            responseCallback(read_serial())
            
        global worker
        worker = SendingThread(None)
        worker.start()
        return True
    
    except Exception as e:
        msg = "error open serial port: " + str(e)
        print(msg)
        if responseCallback:
            responseCallback(msg)
        return False
     

def close_serial():
    if ser.isOpen():
        global worker
        worker.terminate()
        ser.close()

def send_serial(msg, responseCallback = None):
    #print('sending %s \n' % msg)
    if not ser.isOpen():
        return False;
    
    # when there is data in read buffer when nothing waits for it, read that
    bytes_to_read = ser.inWaiting()
    if not lock.locked() and bytes_to_read > 0:
        junk = ser.read(bytes_to_read)
        #print(junk)

    # critical section
    with lock:    
        ser.write(msg)
        response = read_serial()
        if responseCallback:
            responseCallback(response)
        print("response for %s : %s" % (msg, response))
        if "err" in response:
            return False
        return True

def read_serial():
    if not ser.isOpen():
        return
    
    response = bytes()
    bytes_to_read = ser.inWaiting()
    # wait for response to be send from device
    while bytes_to_read < 2:
        time.sleep(0.05)
        bytes_to_read = ser.inWaiting()
    response += ser.read()
    
    responseStr = response.decode("ascii")
    if not ("ok" in responseStr or "err" in responseStr or "\n" in responseStr):
        time.sleep(0.05)
        # make sure there is no data left, 
        #readline or substring check may lock program when response is corrupted
        bytes_to_read = ser.inWaiting()
    
        while bytes_to_read > 0:
            response += ser.read()
            bytes_to_read = ser.in_waiting
            # for low bauds only, make sure there are no more bytes processing
            if(bytes_to_read <= 0 and ser.baudrate < 38400):
                time.sleep(0.2) 
                bytes_to_read = ser.inWaiting()

    response = response.decode("ascii")
    return response 

def queue_command_list(msgs):
    for msg in msgs:
        queue_command(msg)
    
def queue_command(msg, responseCallback = None, priority = None):
    new_entry = ((msg.encode()), responseCallback)
    if priority:
        if priority < 0:
            peek_item = queue.peek()
            # don't queue high priority same command again
            if peek_item and peek_item[0] == new_entry[0]:
                return
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
