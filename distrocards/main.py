from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Type

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
    bot: Bot, pair_strategy: PairStrategy, difficulty: Difficulty, n=5
) -> pd.DataFrame:
    tempos = []

    for _ in range(n):
        pyautogui.hotkey("ctrl", "r")
        time.sleep(1)
        bot.start(difficulty)
        bot.think.set_pair_strategy(pair_strategy)
        bot.think.pair_times.clear()
        try:
            bot.run()
        except Exception as e:
            logger.error(e)

        tempos.extend(bot.think.pair_times)

    return pd.DataFrame(
        {
            "metodo": pair_strategy.name,
            "dificuldade": difficulty.name,
            "tempo": tempos,
        }
    )


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
    # bot.start(Difficulty.EASY)
    # bot.run()

    run_tests(
        bot, medir_tempos_pair, "resultados_think_distrocards.parquet", PairStrategy
    )
