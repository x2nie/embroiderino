**Client application** uses serial port to communicate with microcontroller and is written in python3 and TK. This app can open CSV's embroidery designs created by [Embroidermodder2](https://github.com/Embroidermodder/Embroidermodder) or G-code specific. Embroidermodder2 can load plenty of available file formats, so you can use it for conversion or your own design.
To launch an application: `python3 app.py`, to start with serial port machine simulator: `python3 app.py debug`.

## Features

- Path preview.
- Basic transforms (move, rotate, mirror, scale).
- Some statistics (stitches no, tool changes, path length).

## List of supported G-codes

- **G0** - liner move, jump
- **G1** - linear move, stitch
- **G28** - home axes
- **G90** - set to absolute positioning
- **G91** - set to relative positioning
- **M114** - get current pos
- **M6** - tool change, color change
- **G12** - clean tool or trim thread
- **M116** - wait
