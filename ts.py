
import time

# https://github.com/joosteto/ws2812-spi/blob/master/ws2812.py
# color range is 0 - 127, right is 0 255
def dls_write2812_pylist4(spi, data):
    tx=[]
    # dls debug find green need // 2 is right!
    for i in data:
        if i[0]:
            i[0] //= 4
        if i[1]:
            i[1] //= 2
        if i[2]:
            i[2] //= 2
    for rgb in data:
        for byte in rgb: 
            for ibit in range(3,-1,-1):
                #print ibit, byte, ((byte>>(2*ibit+1))&1), ((byte>>(2*ibit+0))&1), [hex(v) for v in tx]
                tx.append(((byte>>(2*ibit+1))&1)*0x60 + ((byte>>(2*ibit+0))&1)*0x06 + 0x88)
    print([hex(v) for v in tx])
    tx[0] = 0b1000000 # spi need clear head high level
    tx.append(0b1000000) # spi need clear end high level
    spi.xfer(tx, int(4/1.05e-6))

write2812=dls_write2812_pylist4

import spidev
spi = spidev.SpiDev()
spi.open(2, 0)
spi.mode = 3
spi.bits_per_word = 8
spi.max_speed_hz = 20000000

# while 1:
#     write2812(spi, [[4,0,0], [4,0,0]])
#     time.sleep(0.5)
#     write2812(spi, [[4,0,0], [4,0,0]])
#     time.sleep(0.5)

# # red
write2812(spi, [[0,255,0], [0,255,0]])
time.sleep(0.5)
write2812(spi, [[0,0,0], [0,0,0]])
time.sleep(0.5)

# # green
write2812(spi, [[255,0,0], [255,0,0]])
time.sleep(0.5)
write2812(spi, [[0,0,0], [0,0,0]])
time.sleep(0.5)

# blue
write2812(spi, [[0,0,255], [0,0,255]])
time.sleep(0.5)
write2812(spi, [[0,0,0], [0,0,0]])
time.sleep(0.5)

write2812(spi, [[255,255,255], [255,255,255]])
time.sleep(0.5)
write2812(spi, [[0,0,0], [0,0,0]])
time.sleep(0.5)


import os
import time

def test_r():
    
    for i in range(0, 255, 1):
        write2812(spi, [[0, i, 0], [0, i, 0]])
        time.sleep(0.005)
    
    for i in range(255, 0, -1):
        write2812(spi, [[0, i, 0], [0, i, 0]])
        time.sleep(0.005)

def test_g():
    
    for i in range(0, 255, 1):
        write2812(spi, [[i, 0, 0], [i, 0, 0]])
        time.sleep(0.005)
    
    for i in range(255, 0, -1):
        write2812(spi, [[i, 0, 0], [i, 0, 0]])
        time.sleep(0.005)

def test_b():
    
    for i in range(0, 255, 1):
        write2812(spi, [[0, 0, i], [0, 0, i]])
        time.sleep(0.005)
    
    for i in range(255, 0, -1):
        write2812(spi, [[0, 0, i], [0, 0, i]])
        time.sleep(0.005)


def test_rgb():
    
    for i in range(0, 255, 1):
        write2812(spi, [[i, i, i], [i, i, i]])
        time.sleep(0.005)
    
    for i in range(255, 0, -1):
        write2812(spi, [[i, i, i], [i, i, i]])
        time.sleep(0.005)


import time
import queue
import random

# 创建一个队列
light_queue = queue.Queue()

def generate_gradient(start_color, end_color, steps):
    """生成从 start_color 到 end_color 的渐变数据"""
    gradient = []
    for i in range(steps):
        r = int(start_color[0] + (end_color[0] - start_color[0]) * i / steps)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * i / steps)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * i / steps)
        gradient.append(bytes([r, g, b, r, g, b]))
    return gradient

def producer():
    """生产者：生成灯光数据并放入队列"""
    # 定义颜色
    colors = [
        (0, 0, 0),  # 黑色
        (255, 0, 0),  # 绿色
        (0, 255, 0),  # 红色
        (0, 0, 255),  # 蓝色
        (255, 255, 255),  # 白色
        (0, 0, 255),  # 蓝色
        (0, 255, 0),  # 红色
        (255, 0, 0),  # 绿色
        (0, 0, 0),  # 黑色
    ]
    
    colors *= 3
    
    # 生成渐变数据
    gradients = []
    for i in range(len(colors)):
        start_color = colors[i]
        end_color = colors[(i + 1) % len(colors)]
        gradient = generate_gradient(start_color, end_color, 255)
        gradients.extend(gradient)
    
    # 将渐变数据放入队列
    for data in gradients:
        light_queue.put(data)
    
    # 放入一个结束信号，表示生产者已经完成
    light_queue.put(None)

def consumer():
    """消费者：从队列中取出灯光数据并控制灯光"""
    # with open('/sys/class/ws2812/value', 'w') as f:
    while True:
        data = light_queue.get()
        if data is None:
            # 如果收到结束信号，退出循环
            break
        # f.write("{},{},{},{},{},{}".format(*data))
        # f.flush()
        # print(data)
        write2812(spi, [[data[0], data[1], data[2]], [data[3], data[4], data[5]]])
        time.sleep(0.005)  # 控制渐变的速度
        light_queue.task_done()

test_r()

while True:

    test_r()

    test_g()

    test_b()

    test_rgb()

    # # 单线程运行
    producer()  # 先运行生产者
    consumer()  # 再运行消费者

# write2812(spi, [[255, 255, 255], [255, 255, 255]])