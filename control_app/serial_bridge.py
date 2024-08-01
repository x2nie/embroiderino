import asyncio
import serial
import websockets

PORT = '/dev/ttyUSB0'
PORT = '/dev/pts/8'

async def bridge(websocket, path):
    ser = serial.Serial(PORT, 9600)  # Sesuaikan dengan port Anda
    while True:
        # data = ser.read(ser.in_waiting or 1)
        data = ser.read(ser.in_waiting)
        if data:
            await websocket.send(data.decode('utf-8'))
        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
            ser.write(message.encode('utf-8'))
        except asyncio.TimeoutError:
            continue

start_server = websockets.serve(bridge, 'localhost', 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
