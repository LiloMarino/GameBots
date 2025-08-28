import time
from typing import Tuple

from logger_config import logger
from pynput.keyboard import Controller, Key


class Act:
    def __init__(self, step_time: float = 0.05):
        self.kb = Controller()
        self.step_time = step_time

    def desvia(self, vetor: Tuple[int, int]):
        """
        Converte um vetor (dx, dy) em movimento e executa a jogada.
        Pressiona a tecla correspondente por step_time segundos.
        """
        dx, dy = vetor

        # Nada pra fazer
        if dx == 0 and dy == 0:
            return

        # Decide direção
        if abs(dx) > abs(dy):
            key_to_press = Key.right if dx > 0 else Key.left
        else:
            key_to_press = Key.down if dy > 0 else Key.up

        # Envia o comando curto
        logger.info(f"Desvia ({dx}, {dy}) -> {key_to_press}")
        self.kb.press(key_to_press)
        time.sleep(self.step_time)
        self.kb.release(key_to_press)

    def fire(self):
        """Disparo único (Z)."""
        self.kb.press("z")
        self.kb.release("z")

    def continuous_fire(self, enable: bool):
        """Liga ou desliga disparo contínuo (Z pressionado)."""
        if enable:
            self.kb.press("z")
        else:
            self.kb.release("z")

    def focused_mode(self, enable: bool):
        """Liga ou desliga modo focado (Shift pressionado)."""
        if enable:
            self.kb.press(Key.shift)
        else:
            self.kb.release(Key.shift)

    def bomb(self):
        """Usa bomba (X)."""
        self.kb.press("x")
        self.kb.release("x")

    def speedup_dialog(self, enable: bool = True):
        """Liga ou desliga aceleração de diálogos (Ctrl pressionado)."""
        if enable:
            self.kb.press(Key.ctrl)
        else:
            self.kb.release(Key.ctrl)
