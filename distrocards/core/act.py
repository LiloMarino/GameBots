from typing import TYPE_CHECKING

import pyautogui

if TYPE_CHECKING:
    from core.sensor import Card


class Act:
    def click(self, x: int, y: int):
        pyautogui.click(x, y)

    def click_center(self, card: Card):
        pyautogui.click(card.x + card.w // 2, card.y + card.h // 2)

    def match_pair(self, card1: Card, card2: Card):
        self.click_center(card1)
        self.click_center(card2)
