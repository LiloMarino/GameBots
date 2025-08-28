import threading
import time

import keyboard
from core.act import Act
from core.sensor import Difficulty, Sensor
from core.think import DodgeStrategy, Think
from logger_config import logger


class Bot:
    def __init__(self, dodge_strategy: DodgeStrategy, hotkey="F8"):
        self.hotkey = hotkey
        self.bot_ativo = False

        # Componentes principais
        self.sensor = Sensor("Taisei Project v1.4.4")
        self.think = Think(dodge_strategy)
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
        self.sensor.set_difficulty(difficulty)

        # Seleciona o start
        coords = self.sensor.match_template("start_game")
        if coords is None:
            logger.error("Não foi possível iniciar o jogo")
            raise Exception("Não foi possivel iniciar o jogo")
        self.act.fire()
        time.sleep(1)

        # Seleciona a dificuldade
        difficulty_template = f"{difficulty.name.lower()}"
        coords = self.sensor.match_template(difficulty_template)
        if coords is None:
            logger.error("Não foi possível selecionar a dificuldade")
            raise Exception("Não foi possivel selecionar a dificuldade")
        self.act.fire()
        time.sleep(1)

        # Seleciona a personagem Reimu
        coords = self.sensor.match_template("reimu")
        if coords is None:
            logger.error("Não foi possível selecionar a dificuldade")
            raise Exception("Não foi possivel selecionar a dificuldade")
        self.act.fire()
        time.sleep(1)

        # Espera o jogo iniciar
        time.sleep(2)

    def run(self):
        while not self.bot_ativo:
            time.sleep(1)

    def is_active(self):
        return self.bot_ativo
