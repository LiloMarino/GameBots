import logging
import time

from bot import Bot, Difficulty
from core.sensor import CardDetection
from logger_config import logger

logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    bot = Bot(CardDetection.COR)
    while not bot.is_active():
        time.sleep(1)
    bot.start(Difficulty.MEDIUM)
    bot.run()
