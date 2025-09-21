import threading
import time

import keyboard
from core import debug
from core.act import Act
from core.sensor import Difficulty, Sensor
from core.think import DodgeStrategy, Think
from logger_config import logger
from pynput.keyboard import Key


class Bot:
    def __init__(self, dodge_strategy: DodgeStrategy, hotkey="F8"):
        self.hotkey = hotkey
        self.bot_ativo = False

        # Componentes principais
        self.sensor = Sensor("Taisei Project v1.4.4")
        self.think = Think(self.sensor.region, dodge_strategy)
        self.act = Act()

        # Dados
        self.bombs_used = 0

        # Inicia atalho de teclado em uma thread
        threading.Thread(
            target=lambda: keyboard.add_hotkey(self.hotkey, self.toggle), daemon=True
        ).start()
        logger.info(f"Pressione {self.hotkey} para pausar ou retomar o bot.")

    def toggle(self):
        self.bot_ativo = not self.bot_ativo
        estado = "ATIVADO" if self.bot_ativo else "PAUSADO"
        logger.info(f"{estado}")

    def start(self, difficulty: Difficulty = Difficulty.EASY) -> None:
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

    def run(self, use_bombs=False):
        while not self.bot_ativo:
            time.sleep(1)

        # Alterar para enquanto estiver vidas
        self.act.continuous_fire(True)
        player_not_detected = 0
        while player_not_detected < 200:
            while not self.bot_ativo:
                self.act.continuous_fire(False)
                time.sleep(1)

            screenshot, detections = self.sensor.get_objects()
            if not detections.players:
                player_not_detected += 1
                logger.info(f"Jogador nao detectado ({player_not_detected})")
                if player_not_detected == 100:
                    self.act.speedup_dialog(True)
                    time.sleep(0.5)
                    self.act.speedup_dialog(False)
                    if self.sensor.match_template("win"):
                        self.win_restart()
                self.act.continuous_fire(False)
                continue
            else:
                player_not_detected = 0
                self.act.continuous_fire(True)

            if use_bombs:
                if self.think.is_player_in_danger(detections):
                    # Usa o bomb para preservar a sobrevivência
                    self.act.continuous_fire(False)
                    self.act.bomb()
                    self.bombs_used += 1
                    logger.info(f"Usou bomba ({self.bombs_used})")
                    self.act.continuous_fire(True)

            vector, step = self.think.think(screenshot, detections)
            debug.debug_show()
            self.act.dodge(vector, step)

    def restart(self):
        # MÉTODO INSEGURO DE RESTART
        logger.info("Reiniciando partida...")
        self.act.press_key(Key.down)
        time.sleep(0.5)
        self.act.press_key(Key.down)
        time.sleep(0.5)
        self.act.fire()
        time.sleep(0.5)
        self.act.press_key(Key.right)
        time.sleep(0.5)
        self.act.fire()
        time.sleep(0.5)

    def win_restart(self):
        logger.info("Vitoria! Reiniciando...")

    def is_active(self):
        return self.bot_ativo
