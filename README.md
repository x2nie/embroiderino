# Embroiderino 
Embroiderino is a test project which aims at providing all needed to turn an ordinary sewing machine into digital embroidery machine or at least to reuse any other embroidery machine with mainboard failure. Most of the mechanical parts are intended to be made on 3D printer.

As an electronics, arduio based 3D printer board is tested, with additional encoders connected to it. [This](https://gitlab.com/markol/XYprotoboard) will do job for now too. As a firmware
[teathimble](https://gitlab.com/markol/Teathimble_Firmware) is in development. For hoop positioning [this plotter](https://gitlab.com/markol/Simple_plotter) is adopted. All mechanics parts and sewing machine itself are mounted to chipboard. 

Client application is written in python3 and TK, it can open CSV's created by [Embroidermodder2](https://github.com/Embroidermodder/Embroidermodder).

## Work in progress
Note that this is early stage development. Machine, main DC motor speed controller is a next milestone. All the code is licensed under GPL v3.

