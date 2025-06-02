from __future__ import annotations

from typing import TYPE_CHECKING

import pyautogui

if TYPE_CHECKING:
    from core.sensor import Card


class Act:
    def __init__(self, region: dict[str, int]) -> None:
        # Obtém as coordenadas da janela para fazer os clicks
        self.x = region["left"]
        self.y = region["top"]

    def click(self, x: int, y: int):
        # Clique relativo a janela
        pyautogui.moveTo(self.x + x, self.y + y, duration=0.3)
        pyautogui.click(self.x + x, self.y + y)

    def click_center(self, card: Card):
        self.click(card.x + card.w // 2, card.y + card.h // 2)

    def match_pair(self, card1: Card, card2: Card):
        self.click_center(card1)
        self.click_center(card2)
