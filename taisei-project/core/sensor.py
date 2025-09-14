from __future__ import annotations

import itertools
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import NamedTuple

import cv2
import mss
import numpy as np
import pygetwindow as gw
from core import debug
from logger_config import logger
from ultralytics import YOLO


class Difficulty(Enum):
    EASY = auto()
    MEDIUM = auto()
    HARD = auto()
    LUNATIC = auto()


@dataclass(frozen=True)
class BoundingBox:
    x1: int
    y1: int
    x2: int
    y2: int

    def center(self) -> tuple[int, int]:
        """Retorna o centro (cx, cy) da bounding box."""
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

    def intersects(self, other: BoundingBox) -> bool:
        """Verifica se duas bounding boxes se intersectam."""
        return not (
            self.x2 <= other.x1  # completamente à esquerda
            or self.x1 >= other.x2  # completamente à direita
            or self.y2 <= other.y1  # completamente acima
            or self.y1 >= other.y2  # completamente abaixo
        )

    def contains(self, x: int, y: int) -> bool:
        """Verifica se um ponto (x, y) está dentro da bounding box."""
        return self.x1 <= x < self.x2 and self.y1 <= y < self.y2

    @classmethod
    def from_center(cls, cx: int, cy: int, w: int, h: int) -> BoundingBox:
        """Cria uma bounding box a partir do centro e dimensões (w, h)."""
        return cls(cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2)


class Detections(NamedTuple):
    bullets: list[BoundingBox]
    enemies: list[BoundingBox]
    players: list[BoundingBox]


class Sensor:
    TEMPLATES_DIR = Path("templates")
    MODEL_PATH = "../runs/detect/train/weights/best.pt"

    def __init__(
        self,
        window_name: str,
        difficulty: Difficulty = Difficulty.EASY,
    ) -> None:
        self.region = self.get_window(window_name)
        self.difficulty = difficulty
        self.sct = mss.mss()
        self.model = YOLO(self.MODEL_PATH)
        debug.debug_img = self.get_screenshot()
        debug.debug_show()
        logger.info("Janela aberta. Posicione no segundo monitor.")
        cv2.waitKey(1)

    def set_difficulty(self, difficulty: Difficulty):
        self.difficulty = difficulty

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
            cx = max_loc[0] + template_w // 2
            cy = max_loc[1] + template_h // 2

            # cv2.rectangle(
            #     screenshot,
            #     max_loc,
            #     (max_loc[0] + template_w, max_loc[1] + template_h),
            #     RED,
            #     2,
            # )
            # debug.save_image(screenshot, f"match_{template_name}")
            return (cx, cy)
        else:
            return None

    def get_objects(self) -> tuple[np.ndarray, Detections]:
        """
        Executa o YOLO na captura da tela e retorna listas separadas
        de bounding boxes para cada classe.
        Último frame do player é salvo se o player não for detectado.
        """
        screenshot = self.get_screenshot()
        results = self.model(screenshot, verbose=False)

        bullets: list[BoundingBox] = []
        enemies: list[BoundingBox] = []
        players: list[BoundingBox] = []

        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            cls_id = int(box.cls[0].item())

            bbox = BoundingBox(x1, y1, x2, y2)

            if cls_id == 0:  # Bullet
                bullets.append(bbox)
            elif cls_id == 1:  # Enemy
                enemies.append(bbox)
            elif cls_id == 2:  # Player
                players.append(bbox)

        # ==============================
        # Debug image (somente BBoxes)
        # ==============================
        debug_img = screenshot.copy()

        # Configurações
        colors = {
            "bullet": (0, 165, 255),  # laranja
            "enemy": (0, 0, 255),  # vermelho
            "player": (255, 0, 0),  # azul
        }
        thickness = 2

        # Desenha manualmente
        for b in bullets:
            cv2.rectangle(
                debug_img, (b.x1, b.y1), (b.x2, b.y2), colors["bullet"], thickness
            )
        for e in enemies:
            cv2.rectangle(
                debug_img, (e.x1, e.y1), (e.x2, e.y2), colors["enemy"], thickness
            )
        for p in players:
            cv2.rectangle(
                debug_img, (p.x1, p.y1), (p.x2, p.y2), colors["player"], thickness
            )

        # Atualiza a captura de tela para debug
        debug.debug_img = debug_img

        return (
            screenshot,
            Detections(bullets=bullets, enemies=enemies, players=players),
        )

    def __del__(self):
        self.sct.close()
        cv2.destroyAllWindows()
