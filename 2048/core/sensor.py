from enum import Enum, auto
from typing import NamedTuple

import cv2
import easyocr
import mss
import numpy as np
import pygetwindow as gw
from core import debug
from core.constants import BLUE, GREEN


# Tipos
class Tile(NamedTuple):
    x: int
    y: int
    w: int
    h: int


class OCRMethod(Enum):
    TESSERACT = auto()
    EASYOCR = auto()


class GradeMethod(Enum):
    CANNY = auto()
    COR = auto()


# Classe Principal
class Sensor:
    def __init__(
        self,
        window_name: str,
        ocr_method: OCRMethod = OCRMethod.EASYOCR,
        grade_method: GradeMethod = GradeMethod.CANNY,
    ):
        self.region = self.get_window(window_name)
        self.grade_region = None
        self.sct = mss.mss()
        self.reader = easyocr.Reader(["pt"])
        self.ler_texto = {
            OCRMethod.EASYOCR: self._ocr_easyocr,
            OCRMethod.TESSERACT: self._ocr_tesseract,
        }.get(ocr_method, self._ocr_easyocr)
        self.detectar_grade = {
            GradeMethod.CANNY: self._detectar_grade_canny_edge,
            GradeMethod.COR: self._detectar_grade_cor,
        }.get(grade_method, self._detectar_grade_canny_edge)

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

    def get_grid(self):
        grade, tiles = self.detectar_grade()
        tiles = self._sort_tiles(grade.copy(), tiles)
        return self._extrair_tiles(grade, tiles)

    def _detectar_grade_cor(self) -> tuple[cv2.typing.MatLike, list[Tile]]:
        pass

    def _detectar_grade_canny_edge(self) -> tuple[cv2.typing.MatLike, list[Tile]]:
        screenshot = self.get_screenshot(self.grade_region)
        original = screenshot.copy()
        debug.save_image(screenshot, "screenshot")

        # Converte para escala de cinza
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        debug.save_image(gray, "screenshot gray")

        # Desfoque Gaussiano para reduzir o ruído
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        debug.save_image(blur, "screenshot gaussian blur")

        # Detectar bordas com Canny Edge Detection
        edges = cv2.Canny(blur, 5, 10)
        debug.save_image(edges, "screenshot edges")

        # Detectar contornos
        contours, hierarchy = cv2.findContours(
            edges, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
        )
        img_contorns = cv2.drawContours(
            cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR), contours, -1, GREEN, 1
        )
        debug.save_image(img_contorns, "screenshot contornos")

        tiles: list[Tile] = []
        for i, cnt in enumerate(contours):
            # Filtra apenas contornos externos (pai = -1)
            if hierarchy[0][i][3] == -1:
                approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
                if len(approx) == 4 and cv2.isContourConvex(approx):

                    # Obtém os retângulos delimitadores
                    x, y, w, h = cv2.boundingRect(approx)
                    aspect_ratio = w / float(h)
                    if 0.9 < aspect_ratio < 1.1 and 100 < w < 300:
                        tiles.append(Tile(x, y, w, h))

        # Verifica se encontrou os 16 tiles
        if len(tiles) == 16:
            # Obtém os delimitadores da grade
            x_min = min(t.x for t in tiles)
            y_min = min(t.y for t in tiles)
            x_max = max(t.x + t.w for t in tiles)
            y_max = max(t.y + t.h for t in tiles)

            # Salva a região da grade para screenshots futuras
            if not self.grade_region:
                MARGEM = 20
                self.grade_region = {
                    "top": self.region["top"] + y_min - MARGEM,
                    "left": self.region["left"] + x_min - MARGEM,
                    "width": x_max - x_min + 2 * MARGEM,
                    "height": y_max - y_min + 2 * MARGEM,
                }
            cv2.rectangle(screenshot, (x_min, y_min), (x_max, y_max), GREEN, 3)

            # Atualiza coordenadas para ficarem relativas à grade
            tiles = [Tile(t.x - x_min, t.y - y_min, t.w, t.h) for t in tiles]

            grade = original[y_min:y_max, x_min:x_max]
            debug.save_image(screenshot, "screenshot grade")
            debug.save_image(grade, "grade")
        else:
            raise ValueError("Grade não encontrada. Quadrados detectados:", len(tiles))

        return grade, tiles

    def _sort_tiles(
        self, screenshot: cv2.typing.MatLike, tiles: list[Tile]
    ) -> list[Tile]:
        # Ordena primeiro por y (linha)
        tiles = sorted(tiles, key=lambda t: t.y)

        linhas = []
        linha_atual = []
        margem = 20  # tolerância vertical para considerar que dois tiles estão na mesma linha

        for tile in tiles:
            if not linha_atual:
                linha_atual.append(tile)
                continue

            if abs(tile.y - linha_atual[0].y) <= margem:
                linha_atual.append(tile)
            else:
                linhas.append(sorted(linha_atual, key=lambda t: t.x))
                linha_atual = [tile]

        if linha_atual:
            linhas.append(sorted(linha_atual, key=lambda t: t.x))

        # Junta todas as linhas ordenadas
        tiles_ordenados = [tile for linha in linhas for tile in linha]

        # Visualização com índice
        for i, (x, y, w, h) in enumerate(tiles_ordenados):
            cv2.rectangle(screenshot, (x, y), (x + w, y + h), BLUE, 1)
            cx, cy = x + w // 2, y + h // 2
            cv2.putText(
                screenshot,
                str(i),
                (cx - 10, cy + 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),
                1,
                cv2.LINE_AA,
            )

        debug.save_image(screenshot, "screenshot com quadrados ordenados")
        return tiles_ordenados

    def _extrair_tiles(
        self,
        grid: cv2.typing.MatLike,
        tiles: list[Tile],
    ):
        gray = cv2.cvtColor(grid, cv2.COLOR_BGR2GRAY)
        # Threshold para números brancos
        _, thresh_light = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        # Threshold para números pretos
        _, thresh_dark = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)
        # Combinar as duas máscaras (OR bit a bit)
        thresh_combined = cv2.bitwise_or(thresh_dark, thresh_light)

        resultados_ocr: list[int] = []
        for t in tiles:
            tile_img = thresh_combined[t.y : t.y + t.h, t.x : t.x + t.w]
            debug.save_image(tile_img, f"tile_{t.x}_{t.y}")
            valor = self.ler_texto(tile_img)
            resultados_ocr.append(valor)
        return np.array(resultados_ocr, dtype=int).reshape((4, 4))

    def _ocr_easyocr(self, img: cv2.typing.MatLike) -> int:
        resultado = self.reader.readtext(img, detail=0, paragraph=False)
        return int(resultado[0]) if resultado else 0

    def _ocr_tesseract(self, img: cv2.typing.MatLike) -> int:
        pass

    def __del__(self):
        self.sct.close()
