import threading
from enum import Enum, auto

import keyboard
from core import debug
from core.act import Act
from core.sensor import Sensor
from core.think import Think
from logger_config import logger


class Difficulty(Enum):
    EASY = auto()
    NORMAL = auto()
    HARD = auto()


class Bot:
    def __init__(self, hotkey="F8"):
        self.hotkey = hotkey
        self.bot_ativo = True

        # Componentes principais
        self.sensor = Sensor("DistroCards")
        self.think = Think()
        self.act = Act()

        # Inicia atalho de teclado em uma thread
        threading.Thread(
            target=lambda: keyboard.add_hotkey(self.hotkey, self.toggle), daemon=True
        ).start()
        logger.info(f"Pressione {self.hotkey} para pausar ou retomar o bot.")

    def toggle(self):
        self.bot_ativo = not self.bot_ativo
        estado = "ATIVADO" if self.bot_ativo else "PAUSADO"
        logger.info(f"{estado}")

    def start(self, difficulty: Difficulty) -> None:
        pass

    def is_active(self):
        return self.bot_ativo
