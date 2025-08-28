from typing import Tuple

import pyautogui


class Act:
    def desvia(self, vetor: Tuple[int, int]):
        """
        Converte um vetor (dx, dy) em movimento e executa a jogada.
        Se o vetor for (0,0), não faz nada.
        """
        dx, dy = vetor

        if dx == 0 and dy == 0:
            return  # Nada a fazer

        if abs(dx) > abs(dy):
            movimento = "right" if dx > 0 else "left"
        else:
            movimento = "down" if dy > 0 else "up"

        pyautogui.press(movimento)
