import time

import numpy as np
from core.act import Act
from core.sensor import GradeMethod, OCRMethod, Sensor
from core.think import Think
from logger_config import logger

KEY = "F8"
bot_ativo = True  # Global control flag


def toggle_bot():
    global bot_ativo
    bot_ativo = not bot_ativo
    estado = "ATIVADO" if bot_ativo else "PAUSADO"
    logger.info(f"{estado}")


def reiniciar_partida(sensor: Sensor, act: Act) -> bool:
    coords = sensor.match_template("templates/new_game.png")
    if coords:
        act.click(*coords)
        logger.info("Clicou em New Game para reiniciar.")
        time.sleep(0.2)
        return True
    else:
        logger.warning("Botão 'New Game' não encontrado.")
        return False


def registrar_estatisticas(
    sensor: Sensor, board: np.ndarray | None, maiores_numeros: list, pontuacoes: list
):
    if board is not None:
        try:
            maior = int(np.max(board))
            maiores_numeros.append(maior)
            logger.info(f"Maior número alcançado: {maior}")
        except Exception as e:
            logger.error(f"Erro ao acessar board: {e}")
    try:
        time.sleep(0.2)
        score = sensor.extrair_score()
        pontuacoes.append(score)
        logger.info(f"Score extraído: {score}")
    except Exception as e:
        logger.error(f"Falha ao extrair score. {e}")


def executar_simulacao(
    ocr_method: OCRMethod,
    grade_method: GradeMethod,
    max_partidas: int,
    max_movimentos: int,
):
    falhas_grid = 0
    maiores_numeros = []
    pontuacoes = []
    tempos_partida = []
    ultimo_board = None

    logger.info(
        f"Testando combinação: OCR={ocr_method.name}, Grade={grade_method.name}"
    )

    sensor = Sensor("Google Chrome", ocr_method, grade_method)
    think = Think()
    act = Act()

    # Garante que começamos na tela inicial
    while True:
        if reiniciar_partida(sensor, act):
            break

    for partida in range(1, max_partidas + 1):
        while not bot_ativo:
            time.sleep(0.5)

        logger.info(f"Iniciando partida {partida}...")
        movimentos = 0
        ultimo_board = None
        inicio = time.time()

        while movimentos < max_movimentos:
            while not bot_ativo:
                time.sleep(0.5)

            try:
                board = sensor.get_grid()
            except Exception as e:
                falhas_grid += 1
                logger.error(
                    f"[Partida {partida}] Falha ao detectar grid ({falhas_grid}ª): {e}"
                )
                registrar_estatisticas(
                    sensor, ultimo_board, maiores_numeros, pontuacoes
                )
                break

            move, next_board = think.best_move(board)
            ultimo_board = next_board
            if move:
                act.executar_jogada(move)
                movimentos += 1
                logger.info(f"Movimento {movimentos}/{max_movimentos}")
                time.sleep(0.15)
            else:
                logger.info(f"Fim de jogo detectado na partida {partida}")
                registrar_estatisticas(sensor, board, maiores_numeros, pontuacoes)
                break
        else:
            logger.info(
                f"Partida {partida} atingiu o limite de {max_movimentos} movimentos."
            )
            registrar_estatisticas(sensor, ultimo_board, maiores_numeros, pontuacoes)

        duracao = time.time() - inicio
        tempos_partida.append(duracao)
        logger.info(f"Duração da partida {partida}: {duracao:.2f} segundos")

        if not reiniciar_partida(sensor, act):
            logger.critical("Impossível reiniciar partida. Encerrando.")
            exit(1)

    # Estatísticas finais
    logger.info(f"Limite de {max_partidas} partidas atingido. Encerrando bot.")
    logger.info(
        f"Fim dos testes para combinação: {ocr_method.name} + {grade_method.name}"
    )
    logger.info(f"Total de falhas de grid: {falhas_grid}")
    logger.info(f"Maiores números por partida: {maiores_numeros}")
    logger.info(f"Pontuações detectadas: {pontuacoes}")
    logger.info(f"Tempos por partida (s): {[f'{t:.2f}' for t in tempos_partida]}")

    return {
        "ocr": ocr_method.name,
        "grade": grade_method.name,
        "falhas_grid": falhas_grid,
        "maiores_numeros": maiores_numeros,
        "pontuacoes": pontuacoes,
        "tempos": tempos_partida,
    }
