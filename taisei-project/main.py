import logging
import time
from pathlib import Path

from bot import Bot
from core.sensor import Difficulty
from core.think import DodgeStrategy
from logger_config import logger

logger.setLevel(logging.DEBUG)

RESULTADOS_DIR = Path("../resultados")

if __name__ == "__main__":
    bot = Bot(DodgeStrategy.MIX_DISTANCIA_DENSIDADE)
    while not bot.is_active():
        time.sleep(1)
    bot.start(Difficulty.EASY)
    bot.run()
