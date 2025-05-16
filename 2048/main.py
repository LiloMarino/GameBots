import time

from core.act import Act
from core.sensor import Sensor
from core.think import Think

sensor = Sensor("Google Chrome")
think = Think()
act = Act()
while True:
    board = sensor.get_grid()
    movimento = think.best_move(board)
    if movimento:
        act.executar_jogada(movimento)
    else:
        print("Fim de jogo")
        break
    time.sleep(0.5)
