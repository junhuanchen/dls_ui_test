
import aplay as player

while True:
    player.play('/sd/audio/1.wav')

    while player.is_playing():
        player.tick()
        
    player.play('/sd/audio/2.wav')

    while player.is_playing():
        player.tick()
        
    player.play('/sd/audio/3.wav')

    while player.is_playing():
        player.tick()
        
    player.play('/sd/audio/4.wav')

    while player.is_playing():
        player.tick()
