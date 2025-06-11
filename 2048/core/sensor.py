from concurrent.futures import ThreadPoolExecutor
from enum import Enum, auto
from pathlib import Path
from typing import NamedTuple

import cv2
import easyocr
import mss
import numpy as np
import pygetwindow as gw
import pytesseract
from core import debug
from core.constants import BLUE, GREEN, TILE_SIZE
from logger_config import logger


# Tipos
class Tile(NamedTuple):
    x: int
    y: int
    w: int
    h: int


class OCRMethod(Enum):
    TESSERACT = auto()
    EASYOCR = auto()
    TESSERACT_THREAD = auto()
    EASYOCR_THREAD = auto()


class GradeMethod(Enum):
    CANNY = auto()
    CANNY_FIXED = auto()
    COR = auto()
    COR_FIXED = auto()


# Classe Principal
class Sensor:
    TEMPLATES_DIR = Path("templates")

    def __init__(
        self,
        window_name: str,
        ocr_method: OCRMethod = OCRMethod.EASYOCR,
        grade_method: GradeMethod = GradeMethod.CANNY,
    ):
        self.region = self.get_window(window_name)
        self.grade_region = None
        self.fixed = "FIXED" in grade_method.name
        self.fixed_tiles = None
        self.sct = mss.mss()
        self.reader = easyocr.Reader(["pt"])
        self.margem = 0 if self.fixed else 20

        # Métodos e técnicas
        self.ler_texto = {
            OCRMethod.EASYOCR: self._ocr_easyocr,
            OCRMethod.TESSERACT: self._ocr_tesseract,
            OCRMethod.TESSERACT_THREAD: self._ocr_tesseract_parallel,
            OCRMethod.EASYOCR_THREAD: self._ocr_easyocr_parallel,
        }.get(ocr_method, self._ocr_easyocr)
        self.detectar_grade = {
            GradeMethod.CANNY: self._detectar_grade_canny_edge,
            GradeMethod.COR: self._detectar_grade_cor,
            GradeMethod.CANNY_FIXED: self._detectar_grade_canny_edge,
            GradeMethod.COR_FIXED: self._detectar_grade_cor,
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

    def get_grid(self) -> np.ndarray[tuple[int, int], np.dtype[np.int64]]:
        """Obtém a matriz com os valores dos tiles

        Returns:
            np.ndarray[tuple[int, int], np.dtype[np.int64]]: Matriz
        """
        # Se for FIXED e já detectou uma vez, só reutiliza
        if self.fixed and self.fixed_tiles:
            grade = self.get_screenshot(self.grade_region)
            return self._extrair_tiles(grade, self.fixed_tiles)

        # Caso contrário, detecta normalmente
        grade, tiles = self.detectar_grade()
        tiles = self._sort_tiles(grade.copy(), tiles)

        if self.fixed:
            self.fixed_tiles = tiles

        return self._extrair_tiles(grade, tiles)

    def match_template(
        self, template_name: str, threshold: float = 0.8
    ) -> tuple[int, int] | None:
        """Procura por um template na janela do jogo e clica nele se encontrar.

        Args:
            template_name (str): Nome da imagem do template.
            threshold (float): Limite mínimo de similaridade. Defaults to 0.8.

        Returns:
            tuple[int, int] | None: Coordenadas clicadas ou None se não encontrado.
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
            return (click_x, click_y)
        else:
            return None

    def extrair_score(self) -> int:
        """Extrai o score do jogo

        Returns:
            int: Score
        """
        screenshot = self.get_screenshot()

        # Carrega template "score"
        template = cv2.imread(str(self.TEMPLATES_DIR / "score.png"), cv2.IMREAD_COLOR)
        h, w = template.shape[:2]

        # Aplica template matching
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val < 0.8:
            logger.warning(f"Template 'score' não encontrado - {max_val}")
            return -1

        # Calcula coordenadas da ROI abaixo do template
        x, y = max_loc
        roi_y = y + h - 5
        roi_h = 35
        roi_w = w + 30
        roi_x = x - 15

        roi = screenshot[roi_y : roi_y + roi_h, roi_x : roi_x + roi_w]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, thresh_light = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        cv2.bitwise_not(thresh_light, thresh_light)
        contours, _ = cv2.findContours(
            thresh_light, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
        )

        # Encontra o maior contorno (deve ser o quadrado do número)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)

            # Recorta só a área escura (onde está o número)
            number_area = thresh_light[y : y + h, x : x + w]
            cv2.bitwise_not(number_area, number_area)

            scale_factor = 4
            resized = cv2.resize(
                number_area,
                None,
                fx=scale_factor,
                fy=scale_factor,
                interpolation=cv2.INTER_CUBIC,
            )
            debug.save_image(resized, "score_clean")

        # Faz OCR somente na ROI
        result = self.reader.readtext(resized, detail=0, paragraph=False)
        if result:
            return int(result[0])

        logger.error("Não foi possível extrair score via OCR.")
        return -1

    def _detectar_grade_cor(self) -> tuple[cv2.typing.MatLike, list[Tile]]:
        """Detecta a grade e os tiles usando a segmentação por cor

        Raises:
            ValueError: Caso não seja possível detectar a grade

        Returns:
            tuple[cv2.typing.MatLike, list[Tile]]: Imagem da grade e os tiles
        """
        screenshot = self.get_screenshot(self.grade_region)
        original = screenshot.copy()
        debug.save_image(screenshot, "screenshot")

        # Converte para HSV para segmentação por cor
        hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)

        # Define o intervalo da cor predominante dos tiles (ajuste conforme necessário)
        lower_color = np.array([13, 36, 186])
        upper_color = np.array([15, 38, 188])

        mask = cv2.inRange(hsv, lower_color, upper_color)
        debug.save_image(mask, "mask_color")

        # Detecta contornos
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        img_contorns = cv2.drawContours(screenshot.copy(), contours, -1, GREEN, 2)
        debug.save_image(img_contorns, "screenshot contornos 1")

        # Obtém o contorno de maior área (provavelmente a grid central)
        biggest = max(contours, key=cv2.contourArea)
        x_grade, y_grade, w_grade, h_grade = cv2.boundingRect(biggest)

        # Salva a região da grade (em coordenadas absolutas da tela)
        if not self.grade_region:
            self.grade_region = {
                "top": self.region["top"] + y_grade,
                "left": self.region["left"] + x_grade,
                "width": w_grade,
                "height": h_grade,
            }

        cv2.rectangle(
            screenshot,
            (x_grade, y_grade),
            (x_grade + w_grade, y_grade + h_grade),
            GREEN,
            3,
        )

        # Recorta a grade
        grade = original[y_grade : y_grade + h_grade, x_grade : x_grade + w_grade]
        debug.save_image(screenshot, "screenshot grade")
        debug.save_image(grade, "grade")

        # Obtém os contornos dos tiles
        mask_grade = mask[y_grade : y_grade + h_grade, x_grade : x_grade + w_grade]
        debug.save_image(mask_grade, "mask grade")
        contours, hierarchy = cv2.findContours(
            mask_grade, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
        )
        img_contorns = cv2.drawContours(grade.copy(), contours, -1, GREEN, 2)
        debug.save_image(img_contorns, "screenshot contornos 2")

        tiles: list[Tile] = []
        for i, cnt in enumerate(contours):
            # Verifica se é contorno interno (filho do maior contorno)
            if hierarchy[0][i][3] != -1:  # Pai diferente de -1 => é interno
                x_tile, y_tile, w_tile, h_tile = cv2.boundingRect(cnt)
                tiles.append(Tile(x_tile, y_tile, w_tile, h_tile))

        # Verifica se encontrou os 16 tiles
        if len(tiles) >= 16:
            tiles = sorted(tiles, key=lambda t: t.w * t.h, reverse=True)[:16]
        else:
            raise ValueError("Grade não encontrada. Tiles detectados:", len(tiles))

        return grade, tiles

    def _detectar_grade_canny_edge(self) -> tuple[cv2.typing.MatLike, list[Tile]]:
        """Detecta a grade e os tiles usando a segmentação por bordas

        Raises:
            ValueError: Caso não seja possível detectar a grade

        Returns:
            tuple[cv2.typing.MatLike, list[Tile]]: Imagem da grade e os tiles
        """
        screenshot = self.get_screenshot(self.grade_region)
        original = screenshot.copy()
        debug.save_image(screenshot, "screenshot")

        # Converte para escala de cinza
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        debug.save_image(gray, "screenshot gray")

        # Desfoque Gaussiano para reduzir o ruído
        # blur = cv2.GaussianBlur(gray, (5, 5), 0)
        # debug.save_image(blur, "screenshot gaussian blur")

        # Detectar bordas com Canny Edge Detection
        edges = cv2.Canny(gray, 5, 10)
        debug.save_image(edges, "screenshot edges")

        # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        # closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)

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
        if len(tiles) >= 16:
            tiles = sorted(tiles, key=lambda t: t.w * t.h, reverse=True)[:16]
        else:
            raise ValueError("Grade não encontrada. Quadrados detectados:", len(tiles))

        # Obtém os delimitadores da grade
        x_min = min(t.x for t in tiles)
        y_min = min(t.y for t in tiles)
        x_max = max(t.x + t.w for t in tiles)
        y_max = max(t.y + t.h for t in tiles)

        # Salva a região da grade para screenshots futuras
        if not self.grade_region:
            self.grade_region = {
                "top": self.region["top"] + y_min - self.margem,
                "left": self.region["left"] + x_min - self.margem,
                "width": x_max - x_min + 2 * self.margem,
                "height": y_max - y_min + 2 * self.margem,
            }
        cv2.rectangle(screenshot, (x_min, y_min), (x_max, y_max), GREEN, 3)

        # Atualiza coordenadas para ficarem relativas à grade
        tiles = [Tile(t.x - x_min, t.y - y_min, t.w, t.h) for t in tiles]

        grade = original[y_min:y_max, x_min:x_max]
        debug.save_image(screenshot, "screenshot grade")
        debug.save_image(grade, "grade")

        return grade, tiles

    def _sort_tiles(
        self, screenshot: cv2.typing.MatLike, tiles: list[Tile]
    ) -> list[Tile]:
        """Ordena os tiles por linhas para serem organizados na matriz

        Args:
            screenshot (cv2.typing.MatLike): Imagem da grade
            tiles (list[Tile]): Tiles

        Returns:
            list[Tile]: Tiles ordenados
        """
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
            # Texto em preto como sombra (contorno)
            cv2.putText(
                screenshot,
                str(i),
                (cx - 10, cy + 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),  # Preto
                2,  # Espessura maior
                cv2.LINE_AA,
            )

            # Texto amarelo por cima
            cv2.putText(
                screenshot,
                str(i),
                (cx - 10, cy + 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),  # Amarelo
                1,
                cv2.LINE_AA,
            )

        debug.save_image(screenshot, "screenshot com quadrados ordenados")
        return tiles_ordenados

    def _extrair_tiles(
        self,
        grid: cv2.typing.MatLike,
        tiles: list[Tile],
    ) -> np.ndarray[tuple[int, int], np.dtype[np.int64]]:
        """Extrai os valores dos tiles da grade

        Args:
            grid (cv2.typing.MatLike): Imagem da grade
            tiles (list[Tile]): Tiles

        Returns:
            np.ndarray[tuple[int, int], np.dtype[np.int64]]: Matriz com os valores
        """
        gray = cv2.cvtColor(grid, cv2.COLOR_BGR2GRAY)
        # Threshold para números brancos
        _, thresh_light = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        # Threshold para números pretos
        _, thresh_dark = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)
        # Combinar as duas máscaras (OR bit a bit)
        thresh_combined = cv2.bitwise_or(thresh_dark, thresh_light)

        imgs_padronizadas = []
        for t in tiles:
            tile_img = thresh_combined[t.y : t.y + t.h, t.x : t.x + t.w]
            tile_img = cv2.resize(tile_img, TILE_SIZE, interpolation=cv2.INTER_CUBIC)
            debug.save_image(tile_img, f"tile_{t.x}_{t.y}")
            imgs_padronizadas.append(tile_img)

        if self.ler_texto == self._ocr_tesseract_parallel:
            resultados_ocr = self._ocr_tesseract_parallel(imgs_padronizadas)
        elif self.ler_texto == self._ocr_easyocr_parallel:
            resultados_ocr = self._ocr_easyocr_parallel(imgs_padronizadas)
        else:
            resultados_ocr = [self.ler_texto(img) for img in imgs_padronizadas]
        return np.array(resultados_ocr, dtype=int).reshape((4, 4))

    def _ocr_easyocr(self, img: cv2.typing.MatLike) -> int:
        """Aplica OCR com EasyOCR

        Args:
            img (cv2.typing.MatLike): Imagem

        Returns:
            int: Valor extraído
        """
        resultado = self.reader.readtext(img, detail=0, paragraph=False)
        return int(resultado[0]) if resultado else 0

    def _ocr_tesseract(self, img: cv2.typing.MatLike) -> int:
        """Aplica OCR com Tesseract

        Args:
            img (cv2.typing.MatLike): Imagem

        Returns:
            int: Valor extraído
        """
        config = "--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789"
        texto = pytesseract.image_to_string(img, config=config).strip()
        return int(texto) if texto else 0

    def _ocr_tesseract_parallel(self, imgs: list[cv2.typing.MatLike]) -> list[int]:
        """Aplica OCR com Tesseract em paralelo via ThreadPool

        Args:
            imgs (list[cv2.typing.MatLike]): Imagens dos tiles

        Returns:
            list[int]: Valores extraídos
        """
        with ThreadPoolExecutor(max_workers=16) as executor:
            return list(executor.map(self._ocr_tesseract, imgs))

    def _ocr_easyocr_parallel(self, imgs: list[cv2.typing.MatLike]) -> list[int]:
        """Aplica OCR com EasyOCR em lote (batched) usando GPU (mais eficiente)

        Args:
            imgs (list[cv2.typing.MatLike]): Imagens dos tiles

        Returns:
            list[int]: Valores extraídos
        """
        resultados = self.reader.readtext_batched(imgs, detail=0, paragraph=False)
        return [int(r[0]) if r else 0 for r in resultados]

    def __del__(self):
        self.sct.close()
