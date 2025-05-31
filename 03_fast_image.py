import os
import sensor, image, time, lcd
import gc, sys

lcd.init(freq=15000000)
# lcd.register(0x21, None) # invert=True
# lcd.register(0x36, 0x20)
# lcd.register(0x36, 0x60)
lcd.rotation(1)
# lcd.register(0x21, None) # invert=True

def show_images(directory):
    try:
        # 遍历目录中的所有文件
        files = os.listdir(directory)
        # print(files)
        # 显示图像
        for file_name in files:
            run_tim = time.ticks_ms()
            image_path = directory + '/' + file_name
            snapshot = image.Image(image_path)
            lcd.display(snapshot)
            print("display time: %d" % (time.ticks_ms() - run_tim))

    except Exception as e:
        sys.print_exception(e)
    finally:
        gc.collect()

def process_images(directory):
    try:
        # 遍历目录中的所有文件
        files = os.listdir(directory)
        # print(files)
        for file_name in files:
            if file_name.endswith(".jpg"):
                image_path = directory + '/' + file_name
                # print("try: %s" % image_path)

                # 打开图像
                snapshot = image.Image(image_path)
                lcd.display(snapshot)

                # 保存图像
                snapshot.save(image_path, quality=99)
                print("saved: %s" % image_path)
    except Exception as e:
        sys.print_exception(e)
    finally:
        gc.collect()

if __name__ == "__main__":
    directory = "/sd/03_base_jpgs"  # 指定目录
    # process_images(directory)
    show_images(directory)
    print("finished")
