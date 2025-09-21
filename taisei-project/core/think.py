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
    danger_score: float = 0
    score: float = 0


# ============================================================
# Utils
# ============================================================


def dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def normalize(v: tuple[int, int], scale: int) -> tuple[float, float]:
    norm = math.hypot(v[0], v[1])
    if norm == 0:
        return (0, 0)
    return ((v[0] / norm) * scale, (v[1] / norm) * scale)


class Think:
    DEFAULT_DETECT_RADIUS = 250
    DEFAULT_CELL_SIZE = 200
    DEFAULT_TRAVEL_TIME = 0.05

    def __init__(
        self,
        region: dict[str, int],
        dodge_strategy: DodgeStrategy = DodgeStrategy.MENOR_DISTANCIA,
        detect_radius: int = 250,
        cell_size: int = 200,
        travel_time: float = 0.05,
    ) -> None:
        self.region = region
        self.initial_player_pos: tuple[int, int] | None = None
        self.radius = detect_radius
        self.cell_size = cell_size
        self.travel_time = travel_time
        self.set_dodge_strategy(dodge_strategy)

    def set_dodge_strategy(self, dodge_strategy: DodgeStrategy):
        self.dodge_strategy = {
            DodgeStrategy.MENOR_DISTANCIA: self._dodge_menor_distancia,
            DodgeStrategy.MENOR_DENSIDADE: self._dodge_menor_densidade,
            DodgeStrategy.MIX_DISTANCIA_DENSIDADE: self._dodge_mix_distancia_densidade,
        }.get(dodge_strategy, self._dodge_menor_distancia)

    def set_travel_time_mult(self, multiplier: float):
        self.travel_time = self.DEFAULT_TRAVEL_TIME * multiplier

    def set_cell_size_mult(self, multiplier: float):
        self.cell_size = int(self.DEFAULT_CELL_SIZE * multiplier)

    def think(
        self, screenshot: np.ndarray, detections: Detections
    ) -> Tuple[Tuple[float, float], float]:
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
    ) -> Tuple[Tuple[float, float], float]:
        if not detections.players:
            return (0, 0), 0

        player = detections.players[0].center()

        # Salva posição inicial na primeira chamada
        if self.initial_player_pos is None:
            self.initial_player_pos = (player[0], player[1])
            logger.debug("Posição inicial: %s", self.initial_player_pos)

        # ==============================
        # 1) Filtrar threats próximas
        # ==============================
        threats = [
            t
            for t in detections.bullets + detections.enemies
            if dist(player, t.center()) <= self.radius
        ]
        cv2.circle(debug.debug_img, player, self.radius, (0, 0, 255), 2)

        # ==============================
        # 2) Caso existam threats
        # ==============================
        if threats:
            # Threat mais próxima
            closest = min(threats, key=lambda b: dist(player, b.center()))
            cx, cy = closest.center()

            # Linha player -> projétil
            cv2.line(debug.debug_img, player, (cx, cy), (255, 0, 0), 2)

            vx, vy = player[0] - cx, player[1] - cy

            # Duas perpendiculares possíveis
            perp1 = (-vy, vx)
            perp2 = (vy, -vx)
            perp1 = normalize(perp1, 50)
            perp2 = normalize(perp2, 50)

            # ==============================
            # DEBUG
            # ==============================
            # debug_img_extra = debug.debug_img.copy()

            # # Desenha as duas perpendiculares (cores diferentes)
            # debug.draw_arrow(
            #     player, perp1, img=debug_img_extra, color=(255, 255, 0)
            # )  # magenta
            # debug.draw_arrow(
            #     player, perp2, img=debug_img_extra, color=(0, 255, 255)
            # )  # amarelo

            # # Salva imagem extra com perpendiculares
            # debug.save_image(debug_img_extra, f"debug_perp_{debug.frame_count}")

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
                dist1 = dist(
                    (player[0] + perp1[0], player[1] + perp1[1]),
                    self.initial_player_pos,
                )
                dist2 = dist(
                    (player[0] + perp2[0], player[1] + perp2[1]),
                    self.initial_player_pos,
                )
                perp = perp1 if dist1 < dist2 else perp2

            # Desenha seta na direção escolhida
            debug.draw_arrow(player, perp)

            return perp, self.travel_time

        # ==============================
        # 3) Caso não haja threats próximas
        # ==============================
        if detections.enemies:
            # Vai para debaixo do inimigo mais próximo
            enemies_center_x = [e.center()[0] for e in detections.enemies]
            closest_enemy_x = min(enemies_center_x, key=lambda ex: abs(player[0] - ex))
            move_x = closest_enemy_x - player[0]

            debug.draw_arrow(player, (move_x, 0))
            return (move_x, 0), self.travel_time

        # ==============================
        # 4) Caso não haja threats nem inimigos
        # ==============================
        move_x = self.initial_player_pos[0] - player[0]
        move_y = self.initial_player_pos[1] - player[1]
        debug.draw_arrow(player, (move_x, move_y))
        return (move_x, move_y), self.travel_time

    def _dodge_menor_densidade(
        self, screenshot: np.ndarray, detections: Detections
    ) -> Tuple[Tuple[float, float], float]:
        if not detections.players:
            return (0, 0), 0

        # Posição atual do player
        player_bbox = detections.players[0]
        px, py = player_bbox.center()

        # Salva posição inicial na primeira chamada
        if self.initial_player_pos is None:
            self.initial_player_pos = (px, py)
            logger.debug("Posição inicial: %s", self.initial_player_pos)

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

        # ==============================
        # 2) Contar projéteis em cada região
        # ==============================
        for b in detections.bullets:
            for idx, region in regions.items():
                if region.bbox.intersects(b):
                    regions[idx].count += 1

        # ==============================
        # 3) Definir vizinhos de cada célula
        # ==============================
        vizinhos = {
            1: [2, 4, 5],
            2: [1, 3, 5],
            3: [2, 6, 5],
            4: [1, 5, 7],
            5: [2, 4, 6, 8],  # player
            6: [3, 5, 9],
            7: [4, 8, 5],
            8: [5, 7, 9],
            9: [6, 8, 5],
        }

        # ==============================
        # 4) Calcular score de perigo
        # ==============================
        for idx, region in regions.items():
            neighbor_count = sum(regions[n].count for n in vizinhos[idx])
            region.danger_score = region.count + 0.5 * neighbor_count

        # ==============================
        # 5) Calcular score final para cada região
        # ==============================
        enemies_center_x = [e.center()[0] for e in detections.enemies]

        for idx, region in regions.items():
            region_cx, region_cy = region.bbox.center()

            # Distância até a posição inicial
            initial_pos_dist = dist((region_cx, region_cy), self.initial_player_pos)
            initial_pos_dist = max(initial_pos_dist, 1e-6)  # Evitar divisão por zero

            # Distância até o inimigo mais próximo (em x)
            if enemies_center_x:
                min_enemy_dist = min(abs(region_cx - ex) for ex in enemies_center_x)
                min_enemy_dist = max(min_enemy_dist, 1e-6)
            else:
                min_enemy_dist = (
                    1e6  # Se não houver inimigo, trata como distância infinita
                )

            # score final
            region.score = (
                (1.0 / initial_pos_dist) + (1.0 / min_enemy_dist) - region.danger_score
            )

            logger.debug(
                "Regiao %d: danger=%.2f, dist_init=%.2f, dist_enemy=%.2f, score=%.4f",
                idx,
                region.danger_score,
                initial_pos_dist,
                min_enemy_dist,
                region.score,
            )

        # ==============================
        # 6) Escolher região com maior score
        # ==============================
        chosen = max(
            (idx for idx in regions.keys() if idx != 5),
            key=lambda i: regions[i].score,
        )
        logger.debug("Regiao escolhida: %d (score=%.4f)", chosen, regions[chosen].score)

        # ==============================
        # 7) Converter região escolhida em vetor de movimento
        # ==============================
        region_center = regions[chosen].bbox.center()
        move_x = region_center[0] - px
        move_y = region_center[1] - py

        # ==============================
        # Debug visual - imagem 1: grid com numeração
        # ==============================
        # debug_img_grid = debug.debug_img.copy()
        # for idx, r in regions.items():
        #     # retângulo da região
        #     cv2.rectangle(
        #         debug_img_grid,
        #         (r.bbox.x1, r.bbox.y1),
        #         (r.bbox.x2, r.bbox.y2),
        #         (255, 0, 0),
        #         2,
        #     )
        #     # índice da região
        #     cx, cy = r.bbox.center()

        #     # 1) desenha a "borda" preta
        #     cv2.putText(
        #         debug_img_grid,
        #         str(idx),
        #         (cx - 10, cy + 10),
        #         cv2.FONT_HERSHEY_SIMPLEX,
        #         0.7,
        #         (0, 0, 0),  # cor preta
        #         4,  # espessura maior
        #         cv2.LINE_AA,
        #     )
        #     # 2) desenha o texto branco por cima
        #     cv2.putText(
        #         debug_img_grid,
        #         str(idx),
        #         (cx - 10, cy + 10),
        #         cv2.FONT_HERSHEY_SIMPLEX,
        #         0.7,
        #         (255, 255, 255),  # cor branca
        #         2,  # espessura menor
        #         cv2.LINE_AA,
        #     )
        # debug.save_image(debug_img_grid, f"debug_grid_{debug.frame_count}")

        # ==============================
        # Debug visual - imagem 2: região escolhida + seta
        # ==============================
        for r in regions.values():
            cv2.rectangle(
                debug.debug_img,
                (r.bbox.x1, r.bbox.y1),
                (r.bbox.x2, r.bbox.y2),
                (255, 0, 0),
                2,
            )
        chosen_region = regions[chosen]
        cv2.rectangle(
            debug.debug_img,
            (chosen_region.bbox.x1, chosen_region.bbox.y1),
            (chosen_region.bbox.x2, chosen_region.bbox.y2),
            (0, 255, 255),
            2,
        )
        debug.draw_arrow((px, py), (move_x, move_y), color=(0, 255, 0))

        return (move_x, move_y), self.travel_time

    def _dodge_mix_distancia_densidade(
        self, screenshot: np.ndarray, detections: Detections
    ) -> Tuple[Tuple[float, float], float]:
        if not detections.players:
            return (0, 0), 0

        # ------------------------------
        # Posição atual do player
        # ------------------------------
        player_bbox = detections.players[0]
        px, py = player_bbox.center()
        player = (px, py)

        if self.initial_player_pos is None:
            self.initial_player_pos = (px, py)
            logger.debug("Posição inicial: %s", self.initial_player_pos)

        # ------------------------------
        # 1) Ameaça imediata?
        # ------------------------------
        critical_radius = (self.cell_size * math.sqrt(2)) / 2
        threats = [
            t for t in detections.bullets if dist(player, t.center()) <= critical_radius
        ]
        if threats:
            # Threat mais próxima
            closest = min(threats, key=lambda b: dist(player, b.center()))
            cx, cy = closest.center()
            cv2.line(debug.debug_img, player, (cx, cy), (255, 0, 0), 2)

            # Vetor player->projétil
            vx, vy = player[0] - cx, player[1] - cy

            # Perpendiculares
            perp1 = (-vy, vx)
            perp2 = (vy, -vx)
            perp1 = normalize(perp1, self.cell_size)
            perp2 = normalize(perp2, self.cell_size)

            # ====================================================
            # Construir grid de regiões em torno do player
            # ====================================================
            cs = self.cell_size
            regions: dict[int, Region] = {
                i: Region(
                    BoundingBox.from_center(player[0] + dx, player[1] + dy, cs, cs)
                )
                for i, (dx, dy) in {
                    1: (-cs, -cs),
                    2: (0, -cs),
                    3: (cs, -cs),
                    4: (-cs, 0),
                    5: (0, 0),
                    6: (cs, 0),
                    7: (-cs, cs),
                    8: (0, cs),
                    9: (cs, cs),
                }.items()
            }

            # Contar projéteis em cada região
            for b in detections.bullets:
                for idx, region in regions.items():
                    if region.bbox.intersects(b):
                        regions[idx].count += 1

            # Calcular danger_score
            vizinhos = {
                1: [2, 4, 5],
                2: [1, 3, 5],
                3: [2, 6, 5],
                4: [1, 5, 7],
                5: [2, 4, 6, 8],
                6: [3, 5, 9],
                7: [4, 8, 5],
                8: [5, 7, 9],
                9: [6, 8, 5],
            }
            for idx, region in regions.items():
                neighbor_count = sum(regions[n].count for n in vizinhos[idx])
                region.danger_score = region.count + 0.5 * neighbor_count
                logger.debug(
                    "Região %d -> count=%d, danger_score=%.2f",
                    idx,
                    region.count,
                    region.danger_score,
                )

            # ====================================================
            # Avaliar cada perpendicular
            # ====================================================
            def score_perp(perp: Tuple[float, float]) -> Tuple[int, float]:
                target_pos = (player[0] + perp[0], player[1] + perp[1])
                for idx, region in regions.items():
                    if region.bbox.contains(*target_pos):
                        return idx, region.danger_score
                return 5, regions[5].danger_score  # fallback centro

            idx1, danger_score1 = score_perp(perp1)
            idx2, danger_score2 = score_perp(perp2)

            # ====================================================
            # DEBUG VISUAL
            # ====================================================
            # 1) Imagem de opções: círculo + duas perpendiculares
            for r in regions.values():
                cv2.rectangle(
                    debug.debug_img,
                    (r.bbox.x1, r.bbox.y1),
                    (r.bbox.x2, r.bbox.y2),
                    (255, 0, 0),
                    2,
                )
            cv2.circle(debug.debug_img, player, int(critical_radius), (0, 0, 255), 2)
            debug_img_options = debug.debug_img.copy()
            debug.draw_arrow(player, perp1, color=(255, 255, 0), img=debug_img_options)
            debug.draw_arrow(player, perp2, color=(0, 255, 255), img=debug_img_options)
            debug.save_image(debug_img_options, f"debug_perp_{debug.frame_count}")

            # Escolha final
            if danger_score1 < danger_score2:
                chosen, chosen_idx = perp1, idx1
            else:
                chosen, chosen_idx = perp2, idx2

            logger.debug(
                "MixStrategy: Threat próxima detectada! Escolhida perpendicular da região %d "
                "(score=%.2f vs %.2f)",
                chosen_idx,
                max(danger_score1, danger_score2),
                min(danger_score1, danger_score2),
            )

            # 2) Imagem final: seta escolhida (verde) + highlight região
            debug.draw_arrow(player, chosen, color=(0, 255, 0))
            chosen_region = regions[chosen_idx]
            cv2.rectangle(
                debug.debug_img,
                (chosen_region.bbox.x1, chosen_region.bbox.y1),
                (chosen_region.bbox.x2, chosen_region.bbox.y2),
                (0, 255, 255),
                2,
            )

            return chosen, self.travel_time

        # ------------------------------
        # 2) Caso contrário, usar menor densidade normal
        # ------------------------------
        logger.debug("MixStrategy: Sem ameaça imediata, usando menor densidade")
        return self._dodge_menor_densidade(screenshot, detections)
