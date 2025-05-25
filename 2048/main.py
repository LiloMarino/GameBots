import threading
import time

import keyboard
import numpy as np
from core.act import Act
from core.sensor import Sensor
from core.think import Think
from logger_config import logger

# --- CONFIGURAÇÕES ---
KEY = "F8"
MAX_PARTIDAS = 20
MAX_MOVIMENTOS = 20
bot_ativo = False

# --- ESTATÍSTICAS ---
falhas_grid = 0
maiores_numeros = []
pontuacoes = []
ultimo_board = None


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
    ultimo_board = None

    while movimentos_realizados < MAX_MOVIMENTOS:
        if not bot_ativo:
            time.sleep(0.5)
            continue

        try:
            board = sensor.get_grid()
            ultimo_board = board
        except Exception as e:
            falhas_grid += 1
            logger.error(
                f"[Partida {partida}] Falha ao detectar grid. Total de falhas: {falhas_grid}"
            )
            logger.debug(str(e))

            if ultimo_board is not None:
                maior_num = int(np.max(board))
                maiores_numeros.append(maior_num)
                logger.info(f"Maior número do último board: {maior_num}")

            coords = sensor.match_template("new_game.png")
            if coords is not None:
                act.click(*coords)
                logger.info("Recomeçando partida")
            else:
                logger.warning("Botão 'New Game' não encontrado. Encerrando...")
                exit()
            break

        movimento, next_board = think.best_move(board)
        if movimento:
            act.executar_jogada(movimento)
            movimentos_realizados += 1
            logger.info(f"Movimento {movimentos_realizados}/{MAX_MOVIMENTOS}")
            time.sleep(0.2)
        else:
            logger.info(f"Fim de jogo detectado na partida {partida}")

            maior_num = int(np.max(board))
            maiores_numeros.append(maior_num)
            logger.info(f"Maior número alcançado nesta partida: {maior_num}")

            pontuacao = sensor.extrair_score()
            pontuacoes.append(pontuacao)

            coords = sensor.match_template("try_again.png")
            if coords is not None:
                act.click(*coords)
                logger.info("Recomeçando partida")
            else:
                logger.warning("Botão 'Try Again' não encontrado. Encerrando...")
                exit()
            break

logger.info(f"Limite de {MAX_PARTIDAS} partidas atingido.")

# --- RESUMO FINAL ---
logger.info("Resumo das estatísticas:")
logger.info(f"Total de falhas na detecção de grid: {falhas_grid}")
logger.info(f"Maiores números por partida: {maiores_numeros}")
logger.info(f"Pontuações detectadas: {pontuacoes}")
