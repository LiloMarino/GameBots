import math
import random
from enum import Enum, auto
from typing import Tuple

import numpy as np
from core.sensor import BoundingBox, Detections
from logger_config import logger


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
        reset_distance: float = 50,
    ) -> None:
        self.region = region
        self.initial_player_pos: tuple[int, int] | None = None
        self.threshold_distance = threshold_distance
        self.reset_distance = reset_distance
        self.returning_to_center = False
        self.set_dodge_strategy(dodge_strategy)

    def set_dodge_strategy(self, dodge_strategy: DodgeStrategy):
        self.dodge_strategy = {
            DodgeStrategy.MENOR_DISTANCIA: self._dodge_menor_distancia,
            DodgeStrategy.QUADRANTE: self._dodge_quadrante,
        }.get(dodge_strategy, self._dodge_menor_distancia)

    def think(self, screenshot: np.ndarray, detections: Detections) -> Tuple[int, int]:
        """
        Decide o vetor de destino baseado na estratégia de desvio configurada.
        Retorna (dx, dy) relativo ao player.
        """
        return self.dodge_strategy(screenshot, detections)

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
    def _dodge_menor_distancia(
        self, screenshot: np.ndarray, detections: Detections
    ) -> Tuple[int, int]:
        if not detections.players:
            return (0, 0)

        player = _bbox_center(detections.players[0])

        # Salva posição inicial na primeira chamada
        if self.initial_player_pos is None:
            self.initial_player_pos = (player[0], player[1])
            logger.info("Posição inicial: %s", self.initial_player_pos)

        # ==============================
        # 1) Filtrar threats próximas
        # ==============================
        radius = 250  # raio de "visão" do player
        threats = [
            t
            for t in detections.bullets + detections.enemies
            if self._dist(player, _bbox_center(t)) <= radius
        ]

        # ==============================
        # 2) Caso existam threats
        # ==============================
        if threats:
            # Threat mais próxima
            closest = min(threats, key=lambda b: self._dist(player, _bbox_center(b)))
            cx, cy = _bbox_center(closest)
            vx, vy = player[0] - cx, player[1] - cy

            # Duas perpendiculares possíveis
            perp1 = (-vy, vx)
            perp2 = (vy, -vx)

            # Caso existam inimigos na tela, escolher a perpendicular que aproxima de um inimigo
            if detections.enemies:
                enemies_center_x = [_bbox_center(e)[0] for e in detections.enemies]

                # Avaliar para onde cada perpendicular leva
                def dist_to_nearest_enemy(pos):
                    return min(abs(pos[0] - ex) for ex in enemies_center_x)

                p1_pos = (player[0] + perp1[0], player[1] + perp1[1])
                p2_pos = (player[0] + perp2[0], player[1] + perp2[1])

                p1_score = dist_to_nearest_enemy(p1_pos)
                p2_score = dist_to_nearest_enemy(p2_pos)

                perp = perp1 if p1_score < p2_score else perp2
            else:
                # Se não houver inimigos, volta à posição inicial
                dist1 = self._dist(
                    (player[0] + perp1[0], player[1] + perp1[1]),
                    self.initial_player_pos,
                )
                dist2 = self._dist(
                    (player[0] + perp2[0], player[1] + perp2[1]),
                    self.initial_player_pos,
                )
                perp = perp1 if dist1 < dist2 else perp2

            return perp

        # ==============================
        # 3) Caso não haja threats próximas
        # ==============================
        if detections.enemies:
            # Vai para debaixo do inimigo mais próximo
            enemies_center_x = [_bbox_center(e)[0] for e in detections.enemies]
            closest_enemy_x = min(enemies_center_x, key=lambda ex: abs(player[0] - ex))
            move_x = closest_enemy_x - player[0]
            return (move_x, 0)

        # ==============================
        # 4) Caso não haja threats nem inimigos
        # ==============================
        move_x = self.initial_player_pos[0] - player[0]
        move_y = self.initial_player_pos[1] - player[1]
        return (move_x, move_y)

    def _dodge_quadrante(
        self, screenshot: np.ndarray, detections: Detections
    ) -> Tuple[int, int]:
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
