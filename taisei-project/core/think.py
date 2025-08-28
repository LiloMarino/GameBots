import math
import random
from enum import Enum, auto
from typing import Tuple

from core.sensor import BoundingBox, Detections


class DodgeStrategy(Enum):
    MENOR_DISTANCIA = auto()
    QUADRANTE = auto()


def _bbox_center(bbox: BoundingBox) -> Tuple[int, int]:
    """Retorna o centro (x, y) de uma bounding box."""
    return ((bbox.x1 + bbox.x2) // 2, (bbox.y1 + bbox.y2) // 2)


class Think:
    def __init__(
        self, dodge_strategy: DodgeStrategy = DodgeStrategy.MENOR_DISTANCIA
    ) -> None:
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

    # ============================================================
    # Estrategias
    # ============================================================

    def _dodge_menor_distancia(self, detections: Detections) -> Tuple[int, int]:
        """
        Desvia do inimigo/bala mais próximo escolhendo aleatoriamente
        entre as duas direções perpendiculares ao vetor de aproximação.
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

        # Escolha aleatória entre as duas
        return random.choice([perp1, perp2])

    def _dodge_quadrante(self, detections: Detections) -> Tuple[int, int]:
        return (0, 0)

    # ============================================================
    # Utils
    # ============================================================

    @staticmethod
    def _dist(a: Tuple[int, int], b: Tuple[int, int]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])
