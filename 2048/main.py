import threading
import time

import cv2
import keyboard
import numpy as np
import pyautogui
from core.act import Act
from core.sensor import Sensor
from core.think import Think

# --- CONFIGURAÇÕES ---
KEY = "F8"
MAX_PARTIDAS = 20
bot_ativo = False


def toggle_bot():
    global bot_ativo
    bot_ativo = not bot_ativo
    estado = "ATIVADO" if bot_ativo else "PAUSADO"
    print(f"[BOT] {estado}")


threading.Thread(
    target=lambda: keyboard.add_hotkey(KEY, toggle_bot), daemon=True
).start()
print(f"Pressione {KEY} para pausar ou retomar o bot.")


# --- FUNÇÃO DE TEMPLATE MATCHING ---
def clicar_try_again(template_path="try_again.png", threshold=0.8):
    screenshot = pyautogui.screenshot()
    screen_np = np.array(screenshot)
    screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

    result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    if max_val >= threshold:
        h, w = template.shape
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        pyautogui.moveTo(center_x, center_y, duration=0.2)
        pyautogui.click()
        print("[BOT] Clicou no Try Again")
        time.sleep(2)  # Espera carregar nova partida
        return True
    return False


# --- LOOP PRINCIPAL DO BOT ---
sensor = Sensor("Google Chrome")
think = Think()
act = Act()
partidas = 0

while partidas < MAX_PARTIDAS:
    if not bot_ativo:
        time.sleep(0.5)
        continue

    board = sensor.get_grid()
    movimento = think.best_move(board)

    if movimento:
        act.executar_jogada(movimento)
        time.sleep(0.2)
    else:
        print(f"[BOT] Fim de jogo da partida {partidas + 1}")
        clicou = clicar_try_again()
        if clicou:
            partidas += 1
        else:
            print("[BOT] Botão 'Try Again' não encontrado.")
            time.sleep(1)
