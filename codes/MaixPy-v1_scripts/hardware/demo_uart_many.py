from fpioa_manager import fm
from machine import UART
from board import board_info
from fpioa_manager import fm

# maixduino board_info PIN10/PIN11/PIN12/PIN13 or other hardware IO 12/11/10/3
fm.register(24, fm.fpioa.UART2_TX, force=True)
fm.register(25, fm.fpioa.UART2_RX, force=True)

uart_B = UART(UART.UART2, 115200, 8, 0, 0, timeout=1000, read_buf_len=4096)

for i in range(20):
    uart_B.write(b'hello world')
    if uart_B.any():
        read_data = uart_B.read()
        if read_data:
            print("write_bytes = ", write_bytes)
            if read_data == write_bytes:
                print("baudrate:115200 bits:8 parity:0 stop:0 ---check Successfully")
