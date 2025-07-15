import os
import sensor, image, time, lcd, json
import gc, sys
from Maix import GPIO
from fpioa_manager import fm

# gocan
lcd.init(freq=15000000, offset_w0=20, offset_h0=0, offset_w1=20, offset_h1=0, width=280, height=240, rst=39, dcx=38, ss=37, clk=36)
lcd.direction(lcd.YX_RLDU)

# Hello World Example
#
# Welcome to the MaixPy IDE!
# 1. Conenct board to computer
# 2. Select board at the top of MaixPy IDE: `tools->Select Board`
# 3. Click the connect buttion below to connect board
# 4. Click on the green run arrow button below to run the script!

sensor.set_vflip(3)
                                    # run automatically, call sensor.run(0) to stop
sensor.set_pixformat(sensor.RGB565) # Set pixel format to RGB565 (or GRAYSCALE)
sensor.set_framesize(sensor.QVGA)   # Set frame size to QVGA (320x240)
sensor.skip_frames(time = 2000)     # Wait for settings take effect.
clock = time.clock()                # Create a clock object to track the FPS.

while(True):
    clock.tick()                    # Update the FPS clock.
    img = sensor.snapshot()         # Take a picture and return the image.
    lcd.rotation(2)
    lcd.display(img)                # Display on LCD
    print(clock.fps())              # Note: MaixPy's Cam runs about half as fast when connected
                                    # to the IDE. The FPS should increase once disconnected.
