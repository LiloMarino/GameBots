from enum import Enum, auto
from pathlib import Path
from typing import NamedTuple

import cv2
import mss
import numpy as np
import pygetwindow as gw
from core import debug
from core.constants import GREEN, RED


# Tipos
class CardDetection(Enum):
    COR = auto()


class Card(NamedTuple):
    x: int
    y: int
    w: int
    h: int


# Classe Principal
class Sensor:
    TEMPLATES_DIR = Path("templates")

    def __init__(
        self, window_name: str, card_detection: CardDetection = CardDetection.COR
    ) -> None:
        self.region = self.get_window(window_name)
        self.sct = mss.mss()
        self.set_card_detection(card_detection)

    def set_card_detection(self, card_detection: CardDetection):
        self.card_detection = {
            CardDetection.COR: self._detectar_cards_cor,
        }.get(card_detection, self._detectar_cards_cor)

    def get_window(self, window_name: str) -> dict[str, int]:
        """Retorna a região da janela

        Args:
            window_name (str): Nome da janela/processo

        Raises:
            ValueError: Janela não encontrada

        Returns:
            dict[str, int]: Região da janela
        """
        window = gw.getWindowsWithTitle(window_name)
        if window:
            win = window[0]
            return {
                "top": win.top,
                "left": win.left,
                "width": win.width,
                "height": win.height,
            }
        else:
            raise ValueError(f"Janela {window_name} não encontrada")

    def get_screenshot(
        self, region: dict[str, int] | None = None
    ) -> cv2.typing.MatLike:
        """Retorna uma captura de tela

        Args:
            region (dict[str, int] | None, optional): Região de captura. Defaults to None.

        Returns:
            cv2.typing.MatLike: Imagem
        """
        img = np.array(self.sct.grab(region if region else self.region))
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def match_template(
        self, template_name: str, threshold: float = 0.8
    ) -> tuple[int, int] | None:
        """Procura por um template na janela do jogo e retorna as coordenadas

        Args:
            template_name (str): Nome da imagem do template.
            threshold (float): Limite mínimo de similaridade. Defaults to 0.8.

        Returns:
            tuple[int, int] | None: Coordenadas ou None se não encontrado.
        """
        screenshot = self.get_screenshot()
        template = cv2.imread(
            str(self.TEMPLATES_DIR / f"{template_name}.png"), cv2.IMREAD_COLOR
        )

        if template is None:
            raise FileNotFoundError(f"Template não encontrado: {template_name}")

        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            template_h, template_w = template.shape[:2]
            click_x = self.region["left"] + max_loc[0] + template_w // 2
            click_y = self.region["top"] + max_loc[1] + template_h // 2

            # cv2.rectangle(
            #     screenshot,
            #     max_loc,
            #     (max_loc[0] + template_w, max_loc[1] + template_h),
            #     RED,
            #     2,
            # )
            # debug.save_image(screenshot, f"match_{template_name}")
            return (click_x, click_y)
        else:
            return None

    def get_cards(self) -> list[Card]:
        return self.card_detection()

    def capturar_carta(self, card: Card):
        screenshot = self.get_screenshot()
        cropped = screenshot[card.y : card.y + card.h, card.x : card.x + card.w]
        debug.save_image(cropped, f"carta {card}")
        return cropped

    def _detectar_cards_cor(self) -> list[Card]:
        screenshot = self.get_screenshot()
        debug.save_image(screenshot, "screenshot")

        # Converte para HSV para segmentação por cor
        hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)

        # Define o intervalo da cor predominante do fundo (ajuste conforme necessário)
        lower_color = np.array([0, 0, 30])
        upper_color = np.array([0, 0, 33])

        # Obtém a máscara invertida para pegar as cartas
        mask = cv2.inRange(hsv, lower_color, upper_color)
        debug.save_image(mask, "mask_cards")

        # Detecta contornos
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        img_contorns = cv2.drawContours(screenshot.copy(), contours, -1, GREEN, 2)
        debug.save_image(img_contorns, "screenshot contornos")

        # Filtra os contornos para pegar apenas as cartas
        cartas_detectadas: list[Card] = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area_cnt = cv2.contourArea(cnt)
            area_box = w * h

            # Critérios de filtragem
            aspect_ratio = w / h
            solidity = area_cnt / area_box

            if 0.6 < aspect_ratio < 1.8 and solidity > 0.85:
                cartas_detectadas.append(Card(x, y, w, h))
                cv2.rectangle(screenshot, (x, y), (x + w, y + h), GREEN, 2)

        debug.save_image(screenshot, "contornos filtrados")

        return cartas_detectadas

    def __del__(self):
        self.sct.close()
