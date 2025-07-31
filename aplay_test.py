
import aplay as player

while True:
        
    player.play('/sd/2.wav')

    while player.is_playing():
        player.tick()
        
    player.play('/sd/3.wav')

    while player.is_playing():
        player.tick()
        
    player.play('/sd/4.wav')

    while player.is_playing():
        player.tick()
