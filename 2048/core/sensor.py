from enum import Enum, auto
from typing import TypeAlias

import cv2
import easyocr
import mss
import numpy as np
import pygetwindow as gw
from core import debug
from core.constants import BLUE, GREEN

# Tipos
Tile: TypeAlias = tuple[int, int, int, int]


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
            GradeMethod.CANNY: self.detectar_grade_canny_edge,
            GradeMethod.COR: self.detectar_grade_cor,
        }.get(grade_method, self.detectar_grade_canny_edge)

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

    def detectar_grade_cor(self):
        pass

    def detectar_grade_canny_edge(self):
        screenshot = self.get_screenshot(self.grade_region)
        debug.save_image(screenshot, "screenshot")

        # Converte para escala de cinza
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        debug.save_image(gray, "screenshot gray")

        # Desfoque Gaussiano para reduzir o ruído
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        debug.save_image(blur, "screenshot gaussian blur")

        # Detectar bordas com Canny Edge Detection
        edges = cv2.Canny(blur, 10, 50)
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
                        tiles.append((x, y, w, h))

        # Verifica se encontrou os 16 tiles
        if len(tiles) == 16:
            # Obtém os delimitadores da grade
            x_min = min(x for x, y, w, h in tiles)
            y_min = min(y for x, y, w, h in tiles)
            x_max = max(x + w for x, y, w, h in tiles)
            y_max = max(y + h for x, y, w, h in tiles)

            # Salva a região da grade para screenshots futuras
            self.grade_region = {
                "top": y_min,
                "left": x_min,
                "width": x_max - x_min,
                "height": y_max - y_min,
            }
            cv2.rectangle(screenshot, (x_min, y_min), (x_max, y_max), GREEN, 3)

            grade = screenshot[y_min:y_max, x_min:x_max]
            debug.save_image(grade, "grade")
        else:
            raise ValueError("Grade não encontrada. Quadrados detectados:", len(tiles))

        return self.grade_region, tiles
        # ERRO AQUI, OS TILES NÃO ESTÃO ORDENADOS
        tiles = sorted(tiles, key=lambda t: (t[1], t[0]))
        for i, (x, y, w, h) in enumerate(tiles):
            cv2.rectangle(screenshot, (x, y), (x + w, y + h), BLUE, 1)
            cx, cy = x + w // 2, y + h // 2
            cv2.putText(
                screenshot,
                str(i),
                (cx - 10, cy + 10),  # deslocamento para centralizar melhor o texto
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,  # tamanho da fonte
                (0, 255, 255),  # cor (amarelo)
                1,  # espessura
                cv2.LINE_AA,
            )
        debug.save_image(screenshot, "screenshot com quadrados")
        return self.grade_region, tiles

    def extrair_tiles(self, grade_img, quadrados, offset=(0, 0)):
        ox, oy = offset

        resultados_ocr = []
        for x, y, w, h in quadrados:
            # Ajusta coordenadas relativas ao recorte da grade
            tile = grade_img[(y - oy) : (y - oy + h), (x - ox) : (x - ox + w)]
            texto = self._ocr_easyocr(tile)
            resultados_ocr.append(texto)
        return np.array(resultados_ocr).reshape((4, 4))

    def _ocr_easyocr(self, img):
        resultado = self.reader.readtext(img, detail=0, paragraph=False)
        return resultado[0] if resultado else None

    def _ocr_tesseract(self):
        pass

    def __del__(self):
        self.sct.close()
