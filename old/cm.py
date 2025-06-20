# NewGo - By: Echo - 周三 5月 13 2020
'''
新 Go 触摸屏测试程序
触摸 IC: FT6X36
测试硬件: MaixBit
硬件连接
FT6X36 <-> 转接板 <-> MaixBit
1:VCC <-> VCC (3.3V)
2:SDA <-> 25
3:SCL <-> 24
4:INT <-> 22
5:RST <-> 23
6:GND <-> GND
--
初始化时序
    RST 拉低 50ms
    RST 拉高 100ms

'''
'''
/*********************IO操作函数*********************/
#define	FT6236_RST			PGout(6)	//用在输出模式
#define FT6236_SCL 			PCout(7)	//用在输出模式
#define FT6236_SDA 			PGout(8)	//用在输出模式
#define FT6236_SDA_Read 	PGin(8)		//用在输入模式
#define FT6236_INT 			PGin(6)		//用在输入模式

//I2C读写命令
#define FT_CMD_WR 				0X70    	//写命令
#define FT_CMD_RD 				0X71		//读命令
//FT6236 部分寄存器定义
#define FT_DEVIDE_MODE 			0x00   		//FT6236模式控制寄存器
#define FT_REG_NUM_FINGER       0x02		//触摸状态寄存器

#define FT_TP1_REG 				0X03	  	//第一个触摸点数据地址
#define FT_TP2_REG 				0X09		//第二个触摸点数据地址
#define FT_TP3_REG 				0X0F		//第三个触摸点数据地址
#define FT_TP4_REG 				0X15		//第四个触摸点数据地址
#define FT_TP5_REG 				0X1B		//第五个触摸点数据地址


#define	FT_ID_G_LIB_VERSION		0xA1		//版本
#define FT_ID_G_MODE 			0xA4   		//FT6236中断模式控制寄存器
#define FT_ID_G_THGROUP			0x80   		//触摸有效值设置寄存器
#define FT_ID_G_PERIODACTIVE	0x88   		//激活状态周期设置寄存器
#define Chip_Vendor_ID          0xA3        //芯片ID(0x36)
#define ID_G_FT6236ID			0xA8		//0x11
'''

from machine import I2C
import time
from Maix import GPIO
from fpioa_manager import fm
import lcd, image

#fm.register(23, fm.fpioa.GPIOHS23)
#rst = GPIO(GPIO.GPIOHS23, GPIO.OUT)
#rst.value(0)
#time.sleep_ms(50)
#rst.value(1)
#time.sleep_ms(100)

lcd.init()
lcd.direction(0xA8)#修改颜色模式
# lcd.direction(0xe8)#修改颜色模式

i2c = I2C(I2C.I2C0, freq=400*1000, scl=15, sda=10)
devices = i2c.scan()
print(devices)

def ft6x36_write_reg(reg_addr, buf):
    try:
        i2c.writeto_mem(0x38, reg_addr, buf, mem_size=8)
    except OSError as e:
        print(e)
        tmp = fm.fpioa.get_Pin_num(fm.fpioa.I2C0_SDA)
        print(tmp)
        fm.register(tmp, fm.fpioa.GPIOHS11, force=True)
        sda = GPIO(GPIO.GPIOHS11, GPIO.OUT)
        sda.value(0)
        fm.register(tmp, fm.fpioa.I2C0_SDA, force=True)

def ft6x36_read_reg(reg_addr, buf_len):
    try:
        return i2c.readfrom_mem(0x38, reg_addr, buf_len, mem_size=8)
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

ft6x36_write_reg(0x00, 0x0)
ft6x36_write_reg(0x80, 0xC)
ft6x36_write_reg(0x88, 0xC)
data = 0
data_buf = 0
x = 0
y = 0
img = image.Image(size=(lcd.width(), lcd.height()))
lcd.display(img)
while 1:
    #time.sleep_ms(10)
    data = ft6x36_read_reg(0x02, 1)
    #print("reg:" + str(data))
    #if sta & 0x0f: # 读取触摸点的状态
    if data and (data[0] == 0x1): # 读取触摸点 1 的状态
        data_buf =  ft6x36_read_reg(0x03, 4)
        if data_buf:
            y = ((data_buf[0]&0x0f)<<8) | (data_buf[1])
            x = ((data_buf[2]&0x0f)<<8) | (data_buf[3])
            #if ((data_buf[0]&0xc0) == 0x80): # 松开
            print("point[{}:{}]".format(y,x))
            #img.draw_rectangle(x + 1, y + 1, x, y, fill=True, color=(0x00, 0x00, 0xff))
            img.draw_circle(320-x, y, 5, fill=True, color=(0x00, 0x00, 0xff))
            lcd.display(img)


