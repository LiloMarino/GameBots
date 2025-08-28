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

    def fire(self):
        """Disparo único (Z)."""
        pyautogui.press("z")

    def continuous_fire(self, enable: bool):
        """Liga ou desliga disparo contínuo (Z pressionado)."""
        if enable:
            pyautogui.keyDown("z")
        else:
            pyautogui.keyUp("z")

    def focused_mode(self, enable: bool):
        """Liga ou desliga modo focado (Shift pressionado)."""
        if enable:
            pyautogui.keyDown("shift")
        else:
            pyautogui.keyUp("shift")

    def bomb(self):
        """Usa bomba (X)."""
        pyautogui.press("x")

    def speedup_dialog(self, enable: bool = True):
        """Liga ou desliga aceleração de diálogos (Ctrl pressionado)."""
        if enable:
            pyautogui.keyDown("ctrl")
        else:
            pyautogui.keyUp("ctrl")

    def click(self, x: int, y: int):
        """Clique na tela (menu, etc)."""
        pyautogui.click(x, y)
