import logging
import time
from pathlib import Path

import pandas as pd
import pyautogui
from bot import Bot, Difficulty
from core.sensor import CardDetection
from core.think import PairStrategy
from logger_config import logger

logger.setLevel(logging.DEBUG)

RESULTADOS_DIR = Path("../resultados")


def medir_tempos(
    bot: Bot, detection_method: CardDetection, difficulty: Difficulty, n=100
):
    pyautogui.hotkey("ctrl", "r")
    time.sleep(1)
    bot.start(difficulty)
    bot.sensor.set_difficulty(difficulty)
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


if __name__ == "__main__":
    bot = Bot(CardDetection.COR, PairStrategy.TEMPLATE_MATCHING)
    while not bot.is_active():
        time.sleep(1)
    bot.start(Difficulty.EASY)
    bot.run()

    # dfs = []
    # for metodo in CardDetection:
    #     for dificuldade in Difficulty:
    #         print(f"Executando: {metodo.name} + {dificuldade.name}")
    #         df_temp = medir_tempos(bot, metodo, dificuldade)
    #         dfs.append(df_temp)

    # df_final = pd.concat(dfs, ignore_index=True)
    # df_final.to_parquet(RESULTADOS_DIR / "resultados_distrocards.parquet", index=False)
    # df_final.head()
