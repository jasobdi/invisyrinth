# INVISYRINTH
## Concept
INVISYRINTH is a playful physical-digital game developed by Janice, Oriana, and Sam for the Physical Computing course at OST – Ostschweizer Fachhochschule (Rapperswil) as part of the Bachelor in Digital Design. The goal was to create a fun, accessible experience that gets people moving, away from phones and laptops, and into a focused, embodied challenge.

The twist is simple: it’s a maze you can’t see. Instead of navigating with your eyes, you navigate with your body and your memory. This “invisible” setup turns a familiar game into an exercise in spatial orientation, attention, and patience. Players slowly build a mental map of the maze by learning from feedback after each step.

## Demo Video
Click the image to watch the demo on YouTube.  

[![Invisyrinth Demo](https://img.youtube.com/vi/8J3GefgU5Ao/0.jpg)](https://www.youtube.com/watch?v=8J3GefgU5Ao)

## How to play
The game is housed in a compact box with an integrated Modulino Movement sensor that tracks directional movement (left, right, forward, backward). Each movement is confirmed through a small screen that provides the essential outcome feedback:
 
- You’re safe (Keep going), or  
- You hit a wall/obstacle (You hit a Wall)

If the player hits a wall LEDs on each side of the box indicate the direction the wall is at.
 
Players advance step-by-step, using this feedback to reach the end, which triggers a clear congratulatory message, marking completion.

- goal reached (Congratulations, you won!)

## Requirements
If you would like to build INVISYRINTH yourself, you will need the following software and components.

### Software:
* [MicroPython](https://micropython.org/)
* [Arduino Lab for MicroPython](https://labs.arduino.cc/en/labs/micropython)
* [Arduino MicroPython Installer](https://labs.arduino.cc/en/labs/micropython-installer)

### Hardware:
*Controller*
* Arduino Nano ESP32
* Nano Grove Pad
* Modulino Movement
* 2x Grove LED red
* 2x Grove LED red attached to adapter cable (2 LEDs on one plug)
* Grove-LCD RGB Backlight 1602 Display
* Dual Button Unit
* USB-C cable and power supply (e.g. powerbank)

*Maze*
* Arduino Nano ESP32
* Nano Grove Pad
* HT16K33 LED Matrix green
* USB-C cable and power supply (e.g. laptop) 

## How to build
### Wiring
* 2 of the LEDs are connected to one cable beacuse of limited space on the board
* Plug in the UCB-C cables on each of the arduinos, not on the board itself
<img width="1920" height="1080" alt="wiring" src="https://github.com/user-attachments/assets/446869df-f5a6-458e-ba35-65d5cb131740" />

### Code
Copy the content of the folder 'src' to your computer and through the Arduino Lab onto your corresponding boards' main.py file (Controller & Maze)

## How it works
### ESPNow:
Both Arduino boards communicate wirelessly using ESP-Now.
The Controller Arduino sends each detected step as a direction (row_change, col_change) to the Maze Arduino.
The Maze Arduino processes the movement, updates the maze state, and sends feedback messages such as "wall", "ok", "goal", or "reset_ok" back to the controller.

This feedback determines if / which LEDs light up and which message is shown on the LCD display.

### LED Matrix:
The 8x8 Matrix visualizes the maze state, player and goal position so you can quickly check whether input is being read correctly or whether the program needs restarting. 
We mainly used it as a debugging tool, but it can also enable a multiplayer mode: One person navigates blindly while a “Maze Master” watches the display and guides them.

### Dual buttons: 
Two buttons are used for the main controls: pause/resume (blue) and reset (red). 

### LEDs:
These give immediate feedback if the player has hit a wall. Use one LED each for left, right, forward, and backward so the player can see where the wall is located.

### Modulino Movement Sensor:
This is the core input sensor, the logic is split in two parts:
* Step detection: peak in the acceleration indicates if a step was taken
* Direction detection: tilt/move direction determines in which direction the player moves
