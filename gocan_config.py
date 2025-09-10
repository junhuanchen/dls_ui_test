
class Robot:
    def __init__(self):
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