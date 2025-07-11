
import os
import sensor, image, time, lcd, json
import gc, sys

from gocan import protect, AnimationPlayer, EventContainer, Emocards, PriorityQueue, camera_ai_manager, PlayerState, DEBUG, Number

# cube
lcd.init(freq=15000000, type=2, invert=True, offset_w0=0, offset_h0=0, offset_w1=0, offset_h1=0, width=240, height=240, rst=37, dcx=38, ss=36, clk=39)
# lcd.rotation(1)

# gocan
# lcd.init(freq=15000000, offset_w0=20, offset_h0=0, offset_w1=20, offset_h1=0, width=280, height=240, rst=39, dcx=38, ss=37, clk=36)
# lcd.direction(lcd.YX_RLDU)

def app():

    for model_info in camera_ai_manager.model_list:
        if not model_info['initialized']:
            camera_ai_manager.load_model(model_info)
    camera_ai_manager.task_start = time.ticks_ms()
    camera_ai_manager.task_select = 0
    def robot_ai_callback(self):
        if self.state != PlayerState.PLAYING or time.ticks_ms() - camera_ai_manager.task_start > 250:
            # camera_ai_manager.task_select += 1
            img = sensor.snapshot()
            if len(camera_ai_manager.model_list) == 1:
                result, img = camera_ai_manager.detect_objects(img, camera_ai_manager.model_list[0])
            else:
                result, img = camera_ai_manager.detect_objects(img, camera_ai_manager.model_list[camera_ai_manager.task_select % 1])
            if DEBUG:
                lcd.display(img)
            del img
            camera_ai_manager.task_start = time.ticks_ms()
            if result['have_object']:
                del result['have_object']
                # print(result)
                camera_ai_manager.add_data(result)

    player = AnimationPlayer(prefix='', delay=125, callback=robot_ai_callback)  # 设置期望延时播放间隔为125ms

    # player.start(directory='/sd/03_base_jpgs', start_file=0, end_file=None, loop=False)

    player.queue = PriorityQueue()
    player.container = EventContainer()
    player.emocards = Emocards()

    def sensor_check(player):
        # 检查player的uart是否有数据
        if player.uart.any():
            read_data = player.uart.readline()
            print("recv = ", read_data)
            try:
                sensor_event = json.loads(read_data)
                # sensor_event = {
                #     "action": "battry_down",
                #     "priority": 2
                #     "value": "10"
                # }
                player.queue.push(sensor_event.get("priority", 2), sensor_event)
            except json.JSONDecodeError as e:
                print("Error parsing JSON: ", e)
    player.agent.event(500, sensor_check, player)

    def ai_check(player):
        player.container.decay_events() # 衰减事件
        if camera_ai_manager.have_data():
            result = camera_ai_manager.get_data()
            player.container.update_events(result['detections'])
    player.agent.event(500, ai_check, player)

    class robot_base:
        def __init__(self):
            # ==================== 01 事件定义区域 ====================

            self.event_effects = {
                "shake": {"arousal": 0.1, "pleasantness": -0.5},  # 摇晃
                "touch": {"arousal": 0.0, "pleasantness": 0.5},  # 触摸
                "sleep": {"arousal": -0.5, "pleasantness": 0.0},  # 触摸
                "Face": {"arousal": 0.5, "pleasantness": 0.5},  # 人脸
                "Disgust": {"arousal": -0.3, "pleasantness": -0.4},  # 厌恶
                "Sadness": {"arousal": -0.2, "pleasantness": -0.4},  # 悲伤
                "Fear": {"arousal": -0.4, "pleasantness": -0.4},  # 恐惧
                "Neutral": {"arousal": 0.0, "pleasantness": 0.0},  # 中性
                "Surprise": {"arousal": 0.3, "pleasantness": 0.2},  # 惊讶
                "Happiness": {"arousal": 0.2, "pleasantness": 0.5},  # 快乐
                "Anger": {"arousal": 0.5, "pleasantness": -0.5}  # 愤怒
            }

            self.base_path = "/sd/base"
            self.current_list = ["deep", "sleep", "awake", "bored", "express"]
            self.current = Number(0, 4, 2)  # 反馈状态，用于标记情绪表达的结果，以及唤醒或休眠的状态值，这样可以用作下一次的状态参考
            self.life   = Number(0, 10, 10) # 生命值，从 20 到 1，当生命小于 1 时，关机，刚醒来时，没有同步电量的情况下，会假定满电量
            self.social = Number(0, 10, 10) # 社交指数，从 0 到 10，当社交指数小于 1 时，准备睡觉，如果有人出现，社交指数会升到 5 ，如果到 10 则触发专属彩蛋动画。

            # 每当电量小于 2 会期望关机，大于 2 小于 5 则其值为强度 0.1*（n），触发饥饿事件，影响 激动 不愉悦 的倾向状态
            # 电量降低的时候，会发布电量降低，唤醒度下降，当 饥饿 事件 触发 的时候 处于 睡眠 ，那就进入 休眠 。

            # player.xyz = [0, 0, 0] # 摇晃强度，不需要把原始数据上传，只需要考虑触发事件
            # 当 IMU 没有剧烈变化则陆续发布睡眠事件，当调整到 "平静", "愉悦" 进入睡眠状态，从睡眠到，进一步走休眠。
            # 摇晃的强度变化会产生轻重事件，如 摇晃，剧烈摇晃，剧烈摇晃会触发 激动，不愉悦 的倾向状态，反正会走向愉悦的安抚状态。

            # player.social 需要社交值 0 - 10，没有朋友的时候，触发自娱自乐，随着强度的不同，不同程度不同动画效果。
            # 它的娱乐方式也不同，大于 5 可以不需要，朋友或人脸存在的时候，社交值跳进 5 持续增加，如果社交值掉到 1 以下了，就可以准备睡觉了。

        def get_path(self, obj=""):
            tmp = "{}/{}".format(self.base_path, obj)
            print("get_path", tmp)
            return tmp
            
        def get_current_path(self):
            return self.get_path(self.current_list[self.current.get()])

    robot = robot_base()

    def event_check(player):
        # kpu.memtest()
        protect.keep()

        # ==================== 02 AI 事件发布区域 ====================
        # print("time", time.time(), "Updated events:", player.container.get_events()) 
        for key, value in player.container.get_events().items():
            if value > 0.25: # 连续平均阈值
                ai_event = {
                    "action": key,
                    "value": value,
                }
                player.queue.push(ai_event.get("priority", 3), ai_event) # 事件优先级，默认为 3
            print(key, value, player.container.duration(key)) # 事件 概率 持续时间

        # ==================== 02 优先事件处理区域 ====================

        # 集中处理事件，事件一定会被处理完，串口事件优先 AI 事件，有利于先响应 
        if player.queue.size() > 0:
            event = player.queue.pop()
            if event: 
                print("event", event.data)
                if event.data["action"] == "Face" or event.data["action"] == "shake": # 区分走路和运动。
                    if player.state != PlayerState.PLAYING:
                        player.start(directory=robot.get_path('awake'), loop=False)
                    robot.social.add(2) # 强烈摇晃 或 看到人，社交值拉爆
                # 生理需求处理
                if event.data["action"] == "battry_down" or event.data["action"] == "battry_up":
                    robot.life.set(event.data["value"]) # 电量事件，直接设置电量
                # 情感需求处理
                player.emocards.update(robot.event_effects, event.data["action"])

                # 这一轮的情绪表达就符合预期了，可以进入下一轮了

    player.agent.event(1000, event_check, player)

    def robot_check(player):
        try:
            # ==================== 03 机身状态区域 ====================

            #### 状态主要有 current，life，social，emocards

            robot.social.sub(1) # 社交值会持续衰减，但可以通过 AI 事件来增加，当社交值低于 1 时，会进入睡眠
    
            if robot.current.get() == 0:
                if robot.social.get() < 1:
                    print("deep sleep")
                    player.start(directory=robot.get_path('deep'), loop=True)
                    # 串口发送关机指令
                elif robot.social.get() > 3:
                    robot.current.set(3) # 阻止进入睡眠
            elif robot.current.get() == 1:
                robot.social.set(3) # 进入睡眠时，还要再来一轮，才能正式进入睡眠
                robot.current.set(0)
                print("into sleep")
                ai_event = {
                    "action": "sleep",
                }
                player.queue.push(ai_event.get("priority", 3), ai_event)
            elif robot.life.get() < 1 or robot.social.get() < 1:
                robot.current.set(1) # 转睡眠状态，电量低，社交低
            elif robot.current.get():
                if robot.social.get() < 3:
                    robot.current.set(2) # 社交值=低 转去清醒状态，想独处
                elif robot.social.get() > 8:
                    robot.current.set(4) # 转去表达状态，社交值高，想表达
                else:
                    robot.current.set(3) # 转去无聊状态，社交值正常，想自娱自乐
            else:
                pass

            # 物理状态，温度冷热、湿度、电量、震动等基础安全感，

            # ==================== 04 机器人表达区域 ====================
            if robot.current.get() == 1:
                print("sleep")
                ai_event = {
                    "action": "sleep",
                }
                player.queue.push(ai_event.get("priority", 3), ai_event)
                player.start(directory=robot.get_path('sleep'), loop=False)
            # 社交值高的时候，可以打断播放，情绪表达之间是平级的。，社交值低的时候
            elif robot.current.get() == 4 and robot.current.old() != 4: # 社交强的专属动画效果，因宠物性格而定。
                robot.current.update()
                player.start(directory=robot.get_path('super'), loop=False)
                robot.social.sub(2) # 社交值消耗
            else:
                if player.state != PlayerState.PLAYING:
                    result = player.emocards.display()
                    print("[{}, {}, {}, {}.decode()]".format(player.emocards.current_arousal, player.emocards.current_pleasantness, result["state"], result["description"]))

                    # 如果情绪是中立情况，则根据社交值表达
                    if ('\u5e73\u9759', '\u4e2d\u6027') == result["state"]: # 中立
                        player.start(directory=robot.get_current_path(), loop=False)

                    # 其他情绪，目前没有那么多情绪动画，只能挑典型动画
                    # elif ('\u611f\u52a8', '\u611f\u52a8') == result["state"]:
                    #     print("emotion")
                
            # ==================== 05 反馈状态区域 ====================
            print("emocards : {} state : {}, life : {}, social : {}".format(player.emocards.current_mapped, robot.current.get(), robot.life.get(), robot.social.get()))
            
            player.emocards.reset() # 稳定情绪
            
        except Exception as e:
            sys.print_exception(e)
            print("Error: ", e)
    player.agent.event(3000, robot_check, player)

    while True:
        player.play()
        
if __name__ == "__main__":
    app()
