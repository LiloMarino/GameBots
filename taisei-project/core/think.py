import math
from dataclasses import dataclass
from enum import Enum, auto
from typing import Tuple

import cv2
import numpy as np
from core import debug
from core.sensor import BoundingBox, Detections
from logger_config import logger


class DodgeStrategy(Enum):
    MENOR_DISTANCIA = auto()
    MENOR_DENSIDADE = auto()
    MIX_DISTANCIA_DENSIDADE = auto()


@dataclass
class Region:
    bbox: BoundingBox
    count: int = 0


class Think:

    def __init__(
        self,
        region: dict[str, int],
        dodge_strategy: DodgeStrategy = DodgeStrategy.MENOR_DISTANCIA,
        detect_radius: int = 250,
        cell_size: int = 200,
    ) -> None:
        self.region = region
        self.initial_player_pos: tuple[int, int] | None = None
        self.radius = detect_radius
        self.cell_size = cell_size
        self.returning_to_center = False
        self.set_dodge_strategy(dodge_strategy)

    def set_dodge_strategy(self, dodge_strategy: DodgeStrategy):
        self.dodge_strategy = {
            DodgeStrategy.MENOR_DISTANCIA: self._dodge_menor_distancia,
            DodgeStrategy.MENOR_DENSIDADE: self._dodge_menor_densidade,
            DodgeStrategy.MIX_DISTANCIA_DENSIDADE: self._dodge_mix_distancia_densidade,
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
            if player.intersects(bullet):
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

        player = detections.players[0].center()

        # Salva posição inicial na primeira chamada
        if self.initial_player_pos is None:
            self.initial_player_pos = (player[0], player[1])
            logger.info("Posição inicial: %s", self.initial_player_pos)

        # ==============================
        # 1) Filtrar threats próximas
        # ==============================
        threats = [
            t
            for t in detections.bullets + detections.enemies
            if self._dist(player, t.center()) <= self.radius
        ]
        cv2.circle(debug.debug_img, player, self.radius, (0, 0, 255), 2)

        # ==============================
        # 2) Caso existam threats
        # ==============================
        if threats:
            # Threat mais próxima
            closest = min(threats, key=lambda b: self._dist(player, b.center()))
            cx, cy = closest.center()

            # Linha player -> projétil
            cv2.line(debug.debug_img, player, (cx, cy), (255, 0, 0), 2)

            vx, vy = player[0] - cx, player[1] - cy

            # Duas perpendiculares possíveis
            perp1 = (-vy, vx)
            perp2 = (vy, -vx)

            # Caso existam inimigos na tela, escolher a perpendicular que aproxima de um inimigo
            if detections.enemies:
                enemies_center_x = [e.center()[0] for e in detections.enemies]

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

            # Desenha seta na direção escolhida
            debug.draw_arrow(player, perp)

            return perp

        # ==============================
        # 3) Caso não haja threats próximas
        # ==============================
        if detections.enemies:
            # Vai para debaixo do inimigo mais próximo
            enemies_center_x = [e.center()[0] for e in detections.enemies]
            closest_enemy_x = min(enemies_center_x, key=lambda ex: abs(player[0] - ex))
            move_x = closest_enemy_x - player[0]

            debug.draw_arrow(player, (move_x, 0))
            return (move_x, 0)

        # ==============================
        # 4) Caso não haja threats nem inimigos
        # ==============================
        move_x = self.initial_player_pos[0] - player[0]
        move_y = self.initial_player_pos[1] - player[1]
        debug.draw_arrow(player, (move_x, move_y))
        return (move_x, move_y)

    def _dodge_menor_densidade(
        self, screenshot: np.ndarray, detections: Detections
    ) -> Tuple[int, int]:
        if not detections.players:
            return (0, 0)

        # Posição atual do player
        player_bbox = detections.players[0]
        px, py = player_bbox.center()

        # Salva posição inicial na primeira chamada
        if self.initial_player_pos is None:
            self.initial_player_pos = (px, py)
            logger.info("Posição inicial: %s", self.initial_player_pos)

        # ==============================
        # 1) Definir a grid 3x3 (centrada no player)
        # ==============================
        cs = self.cell_size
        offsets = {
            1: (-cs, -cs),
            2: (0, -cs),
            3: (cs, -cs),
            4: (-cs, 0),
            5: (0, 0),  # Player
            6: (cs, 0),
            7: (-cs, cs),
            8: (0, cs),
            9: (cs, cs),
        }

        regions: dict[int, Region] = {
            i: Region(BoundingBox.from_center(px + dx, py + dy, cs, cs))
            for i, (dx, dy) in offsets.items()
        }

        # Desenhar grid
        for r in regions.values():
            cv2.rectangle(
                debug.debug_img,
                (r.bbox.x1, r.bbox.y1),
                (r.bbox.x2, r.bbox.y2),
                (255, 0, 0),
                2,
            )

        # ==============================
        # 2) Contar projéteis em cada região
        # ==============================
        for b in detections.bullets:
            for idx, region in regions.items():
                if region.bbox.intersects(b):
                    regions[idx].count += 1

        for idx, region in regions.items():
            logger.info("Regiao %d: %d projeteis", idx, region.count)

        # ==============================
        # 3) Escolher regiões com menor quantidade
        # ==============================
        min_count = min(r.count for r in regions.values())
        best_regions = [idx for idx, r in regions.items() if r.count == min_count]
        logger.info("Melhores regioes: %s", best_regions)

        # ==============================
        # 4) Critério de desempate
        # ==============================
        if detections.enemies:
            enemies_center_x = [e.center()[0] for e in detections.enemies]

            def dist_to_nearest_enemy(region_idx: int):
                cx, _ = regions[region_idx].bbox.center()
                return min(abs(cx - ex) for ex in enemies_center_x)

            logger.info("Aproximando-se do inimigo...")
            chosen = min(best_regions, key=dist_to_nearest_enemy)
        else:
            # Escolhe a região cujo centro aproxima mais da posição inicial
            def dist_to_initial(region_idx: int):
                return self._dist(
                    regions[region_idx].bbox.center(),
                    self.initial_player_pos,
                )

            logger.info("Retornando ao ponto inicial...")
            chosen = min(best_regions, key=dist_to_initial)

        # ==============================
        # 5) Converter região escolhida em vetor de movimento
        # ==============================
        region_center = regions[chosen].bbox.center()
        move_x = region_center[0] - px
        move_y = region_center[1] - py

        # Debug visual
        r = regions[chosen]
        cv2.rectangle(
            debug.debug_img,
            (r.bbox.x1, r.bbox.y1),
            (r.bbox.x2, r.bbox.y2),
            (0, 255, 255),
            2,
        )
        debug.draw_arrow((px, py), (move_x, move_y), color=(0, 255, 0))

        return (move_x, move_y)

    def _dodge_mix_distancia_densidade(
        self, screenshot: np.ndarray, detections: Detections
    ) -> Tuple[int, int]:
        return (0, 0)

    # ============================================================
    # Utils
    # ============================================================
    @staticmethod
    def _dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])
