import threading
import time

import keyboard
from core.act import Act
from core.sensor import Sensor
from core.think import Think
from logger_config import logger

# --- CONFIGURAÇÕES ---
KEY = "F8"
MAX_PARTIDAS = 20
MAX_MOVIMENTOS = 20
bot_ativo = False


def toggle_bot():
    global bot_ativo
    bot_ativo = not bot_ativo
    estado = "ATIVADO" if bot_ativo else "PAUSADO"
    logger.info(f"{estado}")


# Hotkey
threading.Thread(
    target=lambda: keyboard.add_hotkey(KEY, toggle_bot), daemon=True
).start()
logger.info(f"Pressione {KEY} para pausar ou retomar o bot.")

# --- LOOP PRINCIPAL DO BOT ---
sensor = Sensor("Google Chrome")
think = Think()
act = Act()
partida = 0

while partida < MAX_PARTIDAS:
    if not bot_ativo:
        time.sleep(0.5)
        continue

    partida += 1
    logger.info(f"Iniciando partida {partida}...")
    movimentos_realizados = 0

    while movimentos_realizados < MAX_MOVIMENTOS:
        if not bot_ativo:
            time.sleep(0.5)
            continue
        try:
            board = sensor.get_grid()
        except Exception as e:
            logger.error(f"Erro na partida {partida}")
            logger.error(str(e))
            coords = sensor.match_template("new_game.png")
            if coords is not None:
                act.click(*coords)
                logger.info("Recomeçando partida")
            else:
                logger.warning("Botão 'New Game' não encontrado. Encerrando...")
                exit()
            break

        movimento = think.best_move(board)
        if movimento:
            act.executar_jogada(movimento)
            movimentos_realizados += 1
            logger.info(f"Movimento {movimentos_realizados}/{MAX_MOVIMENTOS}")
            time.sleep(0.2)
        else:
            logger.info(f"Fim de jogo detectado na partida {partida}")
            coords = sensor.match_template("try_again.png")
            if coords is not None:
                act.click(*coords)
                logger.info("Recomeçando partida")
            else:
                logger.warning("Botão 'Try Again' não encontrado. Encerrando...")
                exit()
            break

logger.info(f"Limite de {MAX_PARTIDAS} partidas atingido. Encerrando bot.")
