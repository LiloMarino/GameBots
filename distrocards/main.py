from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Type

import numpy as np
import pandas as pd
import pyautogui
from bot import Bot, Difficulty
from core.sensor import CardDetection
from core.think import PairStrategy
from logger_config import logger

if TYPE_CHECKING:
    from enum import Enum
    from types import FunctionType

logger.setLevel(logging.DEBUG)

RESULTADOS_DIR = Path("../resultados")


def medir_tempos_detection(
    bot: Bot, detection_method: CardDetection, difficulty: Difficulty, n=100
) -> pd.DataFrame:
    pyautogui.hotkey("ctrl", "r")
    time.sleep(1)
    bot.start(difficulty)
    bot.sensor.set_card_detection(detection_method)

    tempos = []
    for _ in range(n):
        time.sleep(0.2)
        inicio = time.time()
        bot.sensor.get_cards()
        duracao = time.time() - inicio
        tempos.append(duracao)

    return pd.DataFrame(
        {
            "metodo": detection_method.name,
            "dificuldade": difficulty.name,
            "tempo": tempos,
        }
    )


def medir_tempos_pair(
    bot: Bot,
    pair_strategy: PairStrategy,
    difficulty: Difficulty,
    threshold: float,
    n: int = 1,
) -> pd.DataFrame:
    dados = []

    for _ in range(n):
        pyautogui.hotkey("ctrl", "r")
        time.sleep(1)

        bot.start(difficulty)
        bot.think.set_pair_strategy(pair_strategy)
        bot.think.set_threshold(threshold)
        bot.think.pair_times.clear()
        bot.think.pair_hits = 0
        bot.think.pair_errors = 0

        try:
            bot.run()
        except Exception as e:
            logger.error(e)

        total_calls = len(bot.think.pair_times)
        media_tempo = np.mean(bot.think.pair_times) if bot.think.pair_times else 0
        acertos = bot.think.pair_hits
        erros = bot.think.pair_errors

        dados.append(
            {
                "metodo": pair_strategy.name,
                "dificuldade": difficulty.name,
                "tempo_medio_chamada": media_tempo,
                "chamadas": total_calls,
                "acertos": acertos,
                "erros": erros,
            }
        )

    return pd.DataFrame(dados)


def run_tests(
    bot: Bot,
    func: FunctionType,
    file_name: str,
    enum: Type[Enum],
):
    dfs = []
    for metodo in enum:
        for dificuldade in Difficulty:
            print(f"Executando: {metodo.name} + {dificuldade.name}")
            df_temp = func(bot, metodo, dificuldade)
            dfs.append(df_temp)

    df_final = pd.concat(dfs, ignore_index=True)
    df_final.to_parquet(RESULTADOS_DIR / file_name, index=False)
    df_final.head()


if __name__ == "__main__":
    bot = Bot(CardDetection.COR, PairStrategy.TEMPLATE_MATCHING)
    while not bot.is_active():
        time.sleep(1)
    # bot.start(Difficulty.HARD)
    # bot.run()

    run_tests(
        bot,
        lambda b, m, d: medir_tempos_pair(b, m, d, threshold=0.8),
        "resultados_think_distrocards_quality_80.parquet",
        PairStrategy,
    )
    run_tests(
        bot,
        lambda b, m, d: medir_tempos_pair(b, m, d, threshold=0.9),
        "resultados_think_distrocards_quality_90.parquet",
        PairStrategy,
    )
    run_tests(
        bot,
        lambda b, m, d: medir_tempos_pair(b, m, d, threshold=0.95),
        "resultados_think_distrocards_quality_95.parquet",
        PairStrategy,
    )
