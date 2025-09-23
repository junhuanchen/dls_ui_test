Number = locals()['Number']
class Robot:
    def __init__(self):
        self.current = Number(0, 4, 2)  # 反馈状态，用于标记情绪表达的结果，以及唤醒或休眠的状态值，这样可以用作下一次的状态参考
        self.life   = Number(0, 10, 10) # 生命值，从 20 到 1，当生命小于 1 时，关机，刚醒来时，没有同步电量的情况下，会假定满电量
        self.social = Number(0, 10, 10) # 社交指数，从 0 到 10，当社交指数小于 1 时，准备睡觉，如果有人出现，社交指数会升到 5 ，如果到 10 则触发专属彩蛋动画。

        self.show_path = ["/sd/lottie", "/sd/audio_gocan"]
        self.show_base = ["jichu.json", ""]
        self.show_up = ["kaixin.json", "kaixin.wav"]
        self.show_shake = ["duanlian.json", "yongli.wav"]
        self.show_face = ["haixiu.json", ""]
        self.show_down = ["shuijiao.json", "diluo.wav"]
        self.show_charge = ["chongdian.json", "dianliangdi.wav"]
        self.show_touch0 = ["sajiao.json", "huanxing.wav"]
        self.show_touch1 = ["yumen.json", "pingchang.wav"]
        self.show_touch2 = ["zhenjing.json", "shengqi.wav"]

        self.show_fall = ["zhenjing.json", "shengqi.wav"]
        
    def get_path(self, obj=["", ""]):
        ret = ["", ""]
        if obj[0] != "":
            ret[0] = "{}/{}".format(self.show_path[0], obj[0])
        if obj[1] != "":
            ret[1] = "{}/{}".format(self.show_path[1], obj[1])
        return ret
        
    def trigger_all(self, player, show_type, loop=1):
        print("trigger_all", show_type)
        ret = self.get_path(show_type)
        player.start(file_path=ret[0], loop=loop)
        # from gocan import aplay
        aplay = locals()['gocan_aplay']
        if aplay.is_playing():
            aplay.stop()
        if ret[1]:
            print(ret[1])
            aplay.play(ret[1])