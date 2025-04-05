import sensor, lcd
import image, time

from Maix import freq
if freq.get_cpu() != 598:
  freq.set(cpu = 600)

lcd.init(freq=20000000)
# lcd.register(0x36, 0x20)
# lcd.register(0x36, 0x60)
lcd.rotation(3)
# lcd.register(0x21, None) # invert=True

path="/sd/color.jpg"
img_read = image.Image(path)
print(img_read)
lcd.display(img_read)

for i in range(499):
  run_tim = time.ticks_ms()
  snapshot = image.Image("/sd/aaaa/%03d.jpg" % i)
  # print(snapshot)
  lcd.display(snapshot)
  print("time: %d" % (time.ticks_ms() - run_tim))

# try:
#     sensor.reset()
# except Exception as e:
#     raise Exception("sensor reset fail, please check hardware connection, or hardware damaged! err: {}".format(e))
# sensor.set_pixformat(sensor.RGB565)
# sensor.set_framesize(sensor.QVGA)
# # sensor.set_hmirror(1) # cube & amigo
# # sensor.set_vflip(1) # cube & amigo
# sensor.run(1)
# sensor.skip_frames()

# while(True):
#     lcd.display(sensor.snapshot())

