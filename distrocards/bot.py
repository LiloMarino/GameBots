import threading
import time
from enum import Enum, auto

import keyboard
import pyautogui
from core import debug
from core.act import Act
from core.sensor import CardDetection, Sensor
from core.think import Think
from logger_config import logger


class Difficulty(Enum):
    EASY = auto()
    MEDIUM = auto()
    HARD = auto()


class Bot:
    def __init__(self, card_detection, hotkey="F8"):
        self.hotkey = hotkey
        self.bot_ativo = False

        # Componentes principais
        self.sensor = Sensor("DistroCards", card_detection)
        self.think = Think()
        self.act = Act(self.sensor.region)

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
        self.sensor.set_difficulty(difficulty)
        coords = self.sensor.match_template("play")
        if coords is None:
            logger.error("Não foi possível iniciar o jogo")
            raise Exception("Não foi possivel iniciar o jogo")
        self.act.click(*coords)
        time.sleep(0.2)

        # Seleciona a dificuldade
        difficulty_template = f"{difficulty.name.lower()}"
        coords = self.sensor.match_template(difficulty_template)
        if coords is None:
            logger.error("Não foi possível selecionar a dificuldade")
            raise Exception("Não foi possivel selecionar a dificuldade")
        self.act.click(*coords)

        # Espera as cartas aparecerem
        # while self.sensor.match_template("card_verso") is None:
        #     logger.debug("Esperando cartas aparecerem...")
        time.sleep(2)

    def run(self):
        while not self.bot_ativo:
            time.sleep(1)

        # Obtém as cartas e inicializa o Think
        self.think.set_cards(self.sensor.get_cards())

        # Enquanto houver pares para serem encontrados
        while self.think.left_cards() > 0:
            while not self.bot_ativo:
                time.sleep(1)

            card1 = self.think.random_undiscovered()
            self.act.click_center(card1)

            # Aguarda um tempo para a carta virar (ajuste conforme necessário)
            # TODO
            time.sleep(0.5)

            # Captura a imagem da carta
            self.think.cards[card1] = self.sensor.capturar_carta(card1)

            # Tem par?
            card2 = self.think.get_pair(card1)
            if card2:
                # Faz o match
                self.act.match_pair(card1, card2)
                logger.info(f"Par encontrado: {card1} <-> {card2}")
                del self.think.cards[card1]
                del self.think.cards[card2]
            else:
                # Não tem par
                logger.info(f"Par não encontrado: {card1}")
                card2 = self.think.random_undiscovered()
                self.act.click_center(card2)

                # TODO
                time.sleep(0.5)
                self.think.cards[card2] = self.sensor.capturar_carta(card2)

                # Fez par?
                if self.think.is_pair(card1, card2):
                    logger.info(f"Par encontrado: {card1} <-> {card2}")
                    del self.think.cards[card1]
                    del self.think.cards[card2]

            # Existe algum par que foi descoberto?
            pair = self.think.get_discovered_pair()
            if pair:
                card1, card2 = pair
                self.act.match_pair(card1, card2)
                logger.info(f"Par encontrado: {card1} <-> {card2}")
                del self.think.cards[card1]
                del self.think.cards[card2]

    def is_active(self):
        return self.bot_ativo
