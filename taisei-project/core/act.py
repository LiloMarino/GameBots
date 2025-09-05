import math
import time
from typing import Tuple

from logger_config import logger
from pynput.keyboard import Controller, Key


class Act:
    def __init__(self):
        self.kb = Controller()

    def desvia(self, vetor: Tuple[int, int], step_time: float = 0.05):
        """
        Converte um vetor (dx, dy) em movimento e executa a jogada.
        Suporta 8 direções: N, NE, E, SE, S, SW, W, NW.
        """
        dx, dy = vetor

        if dx == 0 and dy == 0:
            return

        # Ângulo do vetor (em graus, normalizado 0..360)
        angle = math.degrees(math.atan2(dy, dx))
        if angle < 0:
            angle += 360

        # Define a região (cada 45°) lembrando que o eixo y cresce para baixo
        if 337.5 <= angle or angle < 22.5:
            keys = [Key.right]  # E
        elif 22.5 <= angle < 67.5:
            keys = [Key.down, Key.right]  # SE
        elif 67.5 <= angle < 112.5:
            keys = [Key.down]  # S
        elif 112.5 <= angle < 157.5:
            keys = [Key.down, Key.left]  # SW
        elif 157.5 <= angle < 202.5:
            keys = [Key.left]  # W
        elif 202.5 <= angle < 247.5:
            keys = [Key.up, Key.left]  # NW
        elif 247.5 <= angle < 292.5:
            keys = [Key.up]  # N
        elif 292.5 <= angle < 337.5:
            keys = [Key.up, Key.right]  # NE

        # Pressiona as teclas correspondentes
        logger.info(f"Desvia ({dx}, {dy}) ângulo={angle:.1f}° -> {keys}")
        for k in keys:
            self.kb.press(k)
        time.sleep(step_time)
        for k in keys:
            self.kb.release(k)

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
