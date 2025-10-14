import json
import time
import uuid
from datetime import datetime
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from bot import Bot
from core.sensor import GradeMethod, OCRMethod
from logger_config import logger

# ---------- FASE 1: Testes de desempenho (OCR + GRID) ----------
MAX_PARTIDAS = 20
MAX_MOVIMENTOS = 50

resultados_fase1 = []
combinacoes = list(product(OCRMethod, GradeMethod))

# Diretórios de resultados (padrão parecido com outros projetos)
RESULTADOS_DIR = Path("resultados")
TEMP_BATCH_DIR = RESULTADOS_DIR / "temp_batches"
RESULTADOS_DIR.mkdir(exist_ok=True)
TEMP_BATCH_DIR.mkdir(exist_ok=True)


def save_batch_temp(df: pd.DataFrame, tag: str | None = None) -> Path:
    """Salva um dataframe como parquet temporário identificado por tag+uuid."""
    if tag is None:
        tag = "batch"
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    uid = uuid.uuid4().hex[:8]
    fname = f"{tag}_{timestamp}_{uid}.parquet"
    path = TEMP_BATCH_DIR / fname
    df.to_parquet(path, index=False)
    logger.info(f"Batch temporário salvo: {path.name} ({len(df)} linhas)")
    return path


for ocr_method, grade_method in combinacoes:
    bot = Bot(ocr_method, grade_method)
    bot.start()
    bot.bot_ativo = True

    while not bot.is_active():
        time.sleep(1)

    falhas_grid = 0
    maiores_numeros = []
    pontuacoes = []
    tempos_partida = []
    logger.info("Testando combinação: %s", (ocr_method.name, grade_method.name))

    for partida in range(1, MAX_PARTIDAS + 1):
        while retry:
            retry = False
            logger.info(f"Partida {partida}/{MAX_PARTIDAS}")
            board_final, falha, duracao = bot.run(MAX_MOVIMENTOS)
            falhas_grid += falha
            tempos_partida.append(duracao)

            if board_final is not None:
                try:
                    maiores_numeros.append(int(np.max(board_final)))
                    logger.info("Maior número alcançado: %d", maiores_numeros[-1])
                except Exception as e:
                    retry = True
                    logger.error(f"Erro ao acessar board: {e}")
            else:
                retry = True
                logger.error(f"Erro ao acessar board")

            try:
                pontuacoes.append(bot.sensor.extrair_score())
                logger.info("Pontuação: %d", pontuacoes[-1])
            except Exception as e:
                retry = True
                logger.error(f"Erro ao extrair pontuação: {e}")

            # tenta resetar para próxima partida
            if not bot.reset():
                logger.critical("Impossível reiniciar partida. Encerrando.")
                exit(1)

    # Monta dataframe e salva como batch temporário
    df = pd.DataFrame(
        {
            "ocr": [ocr_method.name] * len(maiores_numeros),
            "grade": [grade_method.name] * len(maiores_numeros),
            "run_index": list(range(len(maiores_numeros))),
            "maior_numero": maiores_numeros,
            "pontuacao": pontuacoes,
            "duracao": tempos_partida,
        }
    )
    save_batch_temp(df, tag=f"ocr_{ocr_method.name}_grade_{grade_method.name}")
    resultados_fase1.append(df)

# ---------- FASE 2: Teste heurística (100 partidas sem limite) ----------
MAX_PARTIDAS = 100
MAX_MOVIMENTOS = 9999

bot = Bot(OCRMethod.EASYOCR_THREAD, GradeMethod.COR_FIXED)
bot.start()
bot.bot_ativo = True

while not bot.is_active():
    time.sleep(1)

falhas_grid = 0
maiores_numeros = []
pontuacoes = []
tempos_partida = []

for partida in range(1, MAX_PARTIDAS + 1):
    while retry:
        retry = False
        logger.info(f"Partida {partida}/{MAX_PARTIDAS}")
        board_final, falha, duracao = bot.run(MAX_MOVIMENTOS)
        falhas_grid += falha
        tempos_partida.append(duracao)

        if board_final is not None:
            try:
                maiores_numeros.append(int(np.max(board_final)))
                logger.info("Maior número alcançado: %d", maiores_numeros[-1])
            except Exception as e:
                retry = True
                logger.error(f"Erro ao acessar board: {e}")
        else:
            retry = True
            logger.error(f"Erro ao acessar board")

        try:
            pontuacoes.append(bot.sensor.extrair_score())
            logger.info("Pontuação: %d", pontuacoes[-1])
        except Exception as e:
            retry = True
            logger.error(f"Erro ao extrair pontuação: {e}")

        if not bot.reset():
            logger.critical("Impossível reiniciar partida. Encerrando.")
            exit(1)

df2 = pd.DataFrame(
    {
        "ocr": [OCRMethod.EASYOCR_THREAD.name] * len(maiores_numeros),
        "grade": [GradeMethod.COR_FIXED.name] * len(maiores_numeros),
        "run_index": list(range(len(maiores_numeros))),
        "maior_numero": maiores_numeros,
        "pontuacao": pontuacoes,
        "duracao": tempos_partida,
    }
)
save_batch_temp(df2, tag="think_phase")
