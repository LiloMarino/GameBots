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
        threshold_distance: float = 300,
    ) -> None:
        self.region = region
        self.perp_count = 0
        self.initial_player_pos: tuple[int, int] | None = None
        self.threshold_distance = threshold_distance
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
        if not detections.players:
            return (0, 0)

        player = _bbox_center(detections.players[0])

        # Salva posição inicial na primeira chamada
        if self.initial_player_pos is None:
            self.initial_player_pos = player

        # Vetores ameaça → player
        threats = detections.bullets + detections.enemies
        if not threats:
            return (0, 0)

        closest = min(threats, key=lambda b: self._dist(player, _bbox_center(b)))
        cx, cy = _bbox_center(closest)
        vx, vy = player[0] - cx, player[1] - cy

        # Direções perpendiculares
        perp1 = (-vy, vx)
        perp2 = (vy, -vx)

        # Distância do player à posição inicial
        dist_to_center = self._dist(player, self.initial_player_pos)

        # Se estiver distante demais, escolhe direção que aproxima do centro
        if dist_to_center > self.threshold_distance:
            perp1_dist = self._dist(
                (player[0] + perp1[0], player[1] + perp1[1]), self.initial_player_pos
            )
            perp2_dist = self._dist(
                (player[0] + perp2[0], player[1] + perp2[1]), self.initial_player_pos
            )
            perp = perp1 if perp1_dist < perp2_dist else perp2
        else:
            perp = perp1

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
