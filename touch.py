# This file is part of MaixUI
# Copyright (c) sipeed.com
#
# Licensed under the MIT license:
#   http://www.opensource.org/licenses/mit-license.php
#

import time
from fpioa_manager import fm
from Maix import GPIO

FT_DEVIDE_MODE = 0x00
FT_ID_G_MODE = 0xA4
FT_ID_G_THGROUP = 0x80
FT_ID_G_PERIODACTIVE = 0x88

FT6X36_ADDR = 0x38

class TouchLow:
  i2c3 = None
  addr = 0x0

  def config(i2c3, addr=FT6X36_ADDR):
    TouchLow.i2c3 = i2c3
    TouchLow.addr = addr

  def write_reg(reg_addr, buf):
    try:
        TouchLow.i2c3.writeto_mem(0x38, reg_addr, buf, mem_size=8)
    except OSError as e:
        print(e)
        tmp = fm.fpioa.get_Pin_num(fm.fpioa.I2C0_SDA)
        print(tmp)
        fm.register(tmp, fm.fpioa.GPIOHS11, force=True)
        sda = GPIO(GPIO.GPIOHS11, GPIO.OUT)
        sda.value(0)
        fm.register(tmp, fm.fpioa.I2C0_SDA, force=True)

  def read_reg(reg_addr, buf_len):
        try:
            return TouchLow.i2c3.readfrom_mem(0x38, reg_addr, buf_len, mem_size=8)
        except OSError as e:
            print("dls")
            print(e)
            tmp = fm.fpioa.get_Pin_num(fm.fpioa.I2C0_SDA)
            print(tmp)
            fm.register(tmp, fm.fpioa.GPIOHS11, force=True)
            sda = GPIO(GPIO.GPIOHS11, GPIO.OUT)
            sda.value(0)
            fm.register(tmp, fm.fpioa.I2C0_SDA, force=True)
            return None

  def config_ft6x36():
    TouchLow.write_reg(0x00, 0x0)
    TouchLow.write_reg(0x80, 0xC)
    TouchLow.write_reg(0x88, 0xC)

  def get_point():
    if TouchLow.i2c3 != None:
      #data = self.read_reg(0x01, 1)
      #print("get_gesture:" + str(data))
      data = TouchLow.read_reg(0x02, 1)
      #print("get_points:" + str(data))
      if (data != None and data[0] == 0x1):
        data_buf = TouchLow.read_reg(0x03, 4)
        if data_buf:
            y = ((data_buf[0] & 0x0f) << 8) | (data_buf[1])
            x = ((data_buf[2] & 0x0f) << 8) | (data_buf[3])
            x = 320 - x
            y = 240 - y
            #print("1 point[{}:{}]".format(x,y))
            #   if ((data_buf[0] & 0xc0) == 0x80):
                #print("2 point[({},{}):({},{})]".format(
                    #x, y,  self.width - x, self.height - y))
            return (y, x)
    return None

class Touch:

  idle, press, release = 0, 1, 2

  def __init__(self, w, h, cycle=1000, invert_y=False):
    self.cycle = cycle
    self.last_time = 0
    self.points = [(0, 0, 0), (0, 0, 0)]
    self.state = Touch.idle
    self.width, self.height = w, h
    self.invert_y = invert_y

  def event(self):
    tmp = TouchLow.get_point()
    if tmp != None:
      x, y = tmp

      if self.invert_y:
          y = self.height - y
          if x < 0: x = 0
          if y < 0: y = 0

      self.last_time = time.ticks_ms()
      if self.state != Touch.press:
          self.state = Touch.press
          self.points[0] = (x, y, time.ticks_ms())
      self.points[1] = (x, y, time.ticks_ms())

    # timeout return ilde.
    if time.ticks_ms() > self.last_time + self.cycle:
        if self.state == Touch.release:
            self.state = Touch.idle
            self.points = [(0, 0, 0), (0, 0, 0)]
            return
        if self.state == Touch.press:
            self.state = Touch.release
            return

if __name__ == "__main__":

  import lcd
  from machine import I2C

  i2c = I2C(I2C.I2C0, freq=400*1000, scl=15, sda=10)
  devices = i2c.scan()
  print(devices)
  TouchLow.config(i2c)
  tmp = Touch(480, 320, 200)
  while 1:
    tmp.event()
    print(tmp.state, tmp.points)
