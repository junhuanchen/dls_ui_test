# This file is part of MaixUI
# Copyright (c) sipeed.com
#
# Licensed under the MIT license:
#   http://www.opensource.org/licenses/mit-license.php
#

try:
    from ui_canvas import ui
    from button import sipeed_button
    from shtxx import SHT3x, SHT3x_ADDR, SHT31_ADDR
    from core import agent
except ImportError:
    from lib.core import agent
    from ui.ui_canvas import ui
    from ui.ui_sample import sample_page
    from driver.shtxx import SHT3x, SHT3x_ADDR, SHT31_ADDR

from fpioa_manager import fm
from machine import I2C

class sample_shtxx():

    def __init__(self):
        self.is_load = False
        self.i2c = I2C(I2C.I2C0, freq=100*1000)
        self.isconnected = False
        self.agent = agent()
        self.agent.event(1000, self.check)

    def load(self):
        if self.is_load == False:
            # i2c init()
            fm.register(24, fm.fpioa.I2C0_SCLK, force=True)
            fm.register(25, fm.fpioa.I2C0_SDA, force=True)
            self.is_load = True

    def free(self):
        if self.is_load:
            # i2c deinit()
            self.is_load = False

    def check(self):
        if self.isconnected == False:
            if SHT3x_ADDR in self.i2c.scan():
                self.sht3x = SHT3x(self.i2c, SHT3x_ADDR)
                self.isconnected = True
            if SHT31_ADDR in self.i2c.scan():
                self.sht3x = SHT3x(self.i2c, SHT31_ADDR)
                self.isconnected = True

    def work(self):
        self.agent.cycle()
        ui.canvas.draw_string(30, 30, "Test SHT3X", (0, 255, 127), scale=3)
        ui.canvas.draw_string(30, 120, "isconnected: %s" % (
            str)(self.isconnected), (255, 127, 0), scale=2)
        if self.isconnected:
            ui.canvas.draw_string(20, 200, str(
                self.sht3x.read_temp_humd()), (127, 255, 255), scale=2)


if __name__ == "__main__":
    sample_page.add_sample(sample_shtxx())

    @ui.warp_template(ui.blank_draw)
    @ui.warp_template(sample_page.sample_draw)
    def unit_test():
      ui.display()

    import time
    while True:
        try:
            unit_test()
        except Exception as e:
            print(e)
