import threading
import time

import keyboard
from core.act import Act
from core.sensor import Sensor
from core.think import Think

# Sistema de pause do bot
bot_ativo = False
KEY = "F8"


def toggle_bot():
    global bot_ativo
    bot_ativo = not bot_ativo
    estado = "ATIVADO" if bot_ativo else "PAUSADO"
    print(f"[BOT] {estado}")


threading.Thread(
    target=lambda: keyboard.add_hotkey(KEY, toggle_bot), daemon=True
).start()
print(f"Pressione {KEY} para pausar ou retomar o bot.")

# Inicia o bot
sensor = Sensor("Google Chrome")
think = Think()
act = Act()
while True:
    if not bot_ativo:
        time.sleep(0.5)
        continue

    board = sensor.get_grid()
    movimento = think.best_move(board)
    if movimento:
        act.executar_jogada(movimento)
    else:
        print("Fim de jogo")
        break
    time.sleep(0.2)
