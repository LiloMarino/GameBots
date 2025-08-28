import math
import random
from enum import Enum, auto
from typing import Tuple

import cv2
from core.sensor import BoundingBox, Detections


class DodgeStrategy(Enum):
    MENOR_DISTANCIA = auto()
    QUADRANTE = auto()


def _bbox_center(bbox: BoundingBox) -> Tuple[int, int]:
    """Retorna o centro (x, y) de uma bounding box."""
    return ((bbox.x1 + bbox.x2) // 2, (bbox.y1 + bbox.y2) // 2)


class Think:
    def __init__(
        self,
        region: dict[str, int],
        dodge_strategy: DodgeStrategy = DodgeStrategy.MENOR_DISTANCIA,
    ) -> None:
        self.region = region
        self.center_x_offset = -225
        self.center_y_offset = 200
        self.perp_count = 0
        self.set_dodge_strategy(dodge_strategy)

    def set_dodge_strategy(self, dodge_strategy: DodgeStrategy):
        self.dodge_strategy = {
            DodgeStrategy.MENOR_DISTANCIA: self._dodge_menor_distancia,
            DodgeStrategy.QUADRANTE: self._dodge_quadrante,
        }.get(dodge_strategy, self._dodge_menor_distancia)

    def think(self, detections: Detections) -> Tuple[int, int]:
        """
        Decide o vetor de destino baseado na estratégia de desvio configurada.
        Retorna (dx, dy) relativo ao player.
        """
        return self.dodge_strategy(detections)

    def is_player_in_danger(self, detections: Detections) -> bool:
        """
        Retorna True se algum tiro intersecta a hitbox do jogador.
        """
        if not detections.players:
            return False  # Nenhum player detectado

        player = detections.players[0]
        for bullet in detections.bullets:
            if self._intersect(player, bullet):
                return True

        return False

    # ============================================================
    # Estrategias
    # ============================================================

    def _dodge_menor_distancia(self, detections: Detections) -> Tuple[int, int]:
        """
        Desvia do inimigo/bala mais próxima escolhendo entre as duas
        direções perpendiculares ao vetor de aproximação, escolhendo
        aquela que aproxima o player do centro da janela.
        """
        if not detections.players:
            return (0, 0)  # Sem player detectado

        player = _bbox_center(detections.players[0])
        threats = detections.bullets + detections.enemies
        if not threats:
            return (0, 0)  # Nada para desviar

        # Ameaça mais próxima
        closest = min(threats, key=lambda b: self._dist(player, _bbox_center(b)))
        cx, cy = _bbox_center(closest)

        # Vetor ameaça → player
        vx, vy = player[0] - cx, player[1] - cy

        # Direções perpendiculares
        perp1 = (-vy, vx)
        perp2 = (vy, -vx)
        perp_chose = True

        self.perp_count += 1
        if self.perp_count % 2 == 0:
            perp_chose = False if perp_chose else True

        if perp_chose:
            perp = perp1
        else:
            perp = perp2
        return perp

    def _dodge_quadrante(self, detections: Detections) -> Tuple[int, int]:
        return (0, 0)

    # ============================================================
    # Utils
    # ============================================================

    @staticmethod
    def _dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

    @staticmethod
    def _intersect(a: BoundingBox, b: BoundingBox) -> bool:
        """
        Verifica se duas bounding boxes se intersectam.
        """
        return not (a.x2 < b.x1 or a.x1 > b.x2 or a.y2 < b.y1 or a.y1 > b.y2)
