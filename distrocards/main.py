import logging

from bot import Bot, Difficulty
from logger_config import logger

logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    bot = Bot()
    bot.start(Difficulty.EASY)
    bot.run()
