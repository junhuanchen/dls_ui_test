import json
import serial
import time

json_dict = {
    "action": "emoji",
    "priority": 2,
    "value": "10",
    "loop": "3"
}

# 把 dict 转成紧凑 JSON 字符串
payload = json.dumps(json_dict, separators=(',', ':'))   # → {"action":"emoji","priority":2,"value":"10","loop":"3"}

def send_data(ser, data: bytes, gap=0.002, chunk=20):
    for i in range(0, len(data), chunk):
        ser.write(data[i:i + chunk].encode("iso-8859-1"))
        time.sleep(gap)
            
with serial.Serial('COM33', 115200, timeout=1) as ser:
    while True:
        send_data(ser, payload, gap=0.002, chunk=20)
        time.sleep(0.1)
