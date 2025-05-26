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
MAX_PARTIDAS = 5
MAX_MOVIMENTOS = 20
bot_ativo = True

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


def reiniciar_partida():
    coords = sensor.match_template("new_game.png")
    if coords:
        act.click(*coords)
        logger.info("Clicou em New Game para reiniciar.")
        time.sleep(0.2)
        return True
    else:
        logger.error("Botão 'New Game' não encontrado. Encerrando...")
        return False


def registrar_estatisticas(board: np.ndarray | None):
    if board is not None:
        try:
            maior = int(np.max(board))
            maiores_numeros.append(maior)
            logger.info(f"Maior número alcançado: {maior}")
        except Exception as e:
            logger.warning(f"Erro ao acessar board: {e}")
    try:
        time.sleep(0.2)
        score = sensor.extrair_score()
        pontuacoes.append(score)
        logger.info(f"Score extraído: {score}")
    except Exception as e:
        logger.warning(f"Falha ao extrair score. {e}")


# --- INICIALIZAÇÃO ---
sensor = Sensor("Google Chrome")
think = Think()
act = Act()
partida = 0

# Garante que começamos na tela inicial
while True:
    if reiniciar_partida():
        break

# --- LOOP DE PARTIDAS ---
for partida in range(1, MAX_PARTIDAS + 1):
    while not bot_ativo:
        time.sleep(0.5)

    logger.info(f"Iniciando partida {partida}...")
    movimentos = 0
    ultimo_board = None

    while movimentos < MAX_MOVIMENTOS:
        while not bot_ativo:
            time.sleep(0.5)

        try:
            board = sensor.get_grid()
        except Exception as e:
            falhas_grid += 1
            logger.error(
                f"[Partida {partida}] Falha ao detectar grid ({falhas_grid}ª): {e}"
            )
            registrar_estatisticas(ultimo_board)
            break

        move, next_board = think.best_move(board)
        ultimo_board = next_board
        if move:
            act.executar_jogada(move)
            movimentos += 1
            logger.info(f"Movimento {movimentos}/{MAX_MOVIMENTOS}")
            time.sleep(0.2)
        else:
            logger.info(f"Fim de jogo detectado na partida {partida}")
            registrar_estatisticas(board)
            break
    else:
        # Se o loop terminou sem break, atingimos o limite de movimentos
        logger.info(
            f"Partida {partida} atingiu o limite de {MAX_MOVIMENTOS} movimentos."
        )
        registrar_estatisticas(ultimo_board)

    if not reiniciar_partida():
        logger.critical("Impossível reiniciar partida. Encerrando.")
        exit(1)

logger.info(f"Limite de {MAX_PARTIDAS} partidas atingido. Encerrando bot.")
logger.info(f"Total de falhas de grid: {falhas_grid}")
logger.info(f"Maiores números por partida: {maiores_numeros}")
logger.info(f"Pontuações detectadas: {pontuacoes}")
