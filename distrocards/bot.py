import threading
import time
from enum import Enum, auto

import keyboard
import pyautogui
from core import debug
from core.act import Act
from core.sensor import Sensor
from core.think import Think
from logger_config import logger


class Difficulty(Enum):
    EASY = auto()
    MEDIUM = auto()
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
        # Clica no play
        coords = self.sensor.match_template("play")
        if coords is None:
            logger.error("Não foi possível iniciar o jogo")
            raise Exception("Não foi possivel iniciar o jogo")
        self.act.click(*coords)
        time.sleep(0.2)

        # Seleciona a dificuldade
        for difficulty in Difficulty:
            difficulty_template = f"{difficulty.name.lower()}"
            coords = self.sensor.match_template(difficulty_template)
            if coords is None:
                logger.error("Não foi possível selecionar a dificuldade")
                raise Exception("Não foi possivel selecionar a dificuldade")
            pyautogui.moveTo(*coords)

    def is_active(self):
        return self.bot_ativo
