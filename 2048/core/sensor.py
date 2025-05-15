import cv2
import easyocr
import mss
import numpy as np
import pygetwindow as gw
from core import debug
from core.constants import BLUE, GREEN


class Sensor:
    def __init__(self, window_name: str):
        self.region = self.get_window(window_name)
        # Mantém o MSS aberto enquanto o objeto existir
        self.sct = mss.mss()
        self.reader = easyocr.Reader(["en"], gpu=False)
        self.grade_region = None

    def get_window(self, window_name: str):
        window = gw.getWindowsWithTitle(window_name)
        if window:
            win = window[0]
            return {
                "top": win.top,
                "left": win.left,
                "width": win.width,
                "height": win.height,
            }
        return None

    def get_screenshot(self, region=None):
        img = np.array(self.sct.grab(region if region else self.region))
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def detectar_grade_cor(self):
        pass

    def detectar_grade_canny_edge(self):
        if self.region:
            screenshot = self.get_screenshot(self.region)
            debug.save_image(screenshot, "screenshot")
        else:
            screenshot = self.get_screenshot()
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

        quadrados = []
        for i, cnt in enumerate(contours):
            # Filtra apenas contornos externos
            if hierarchy[0][i][3] == -1:
                approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
                if len(approx) == 4 and cv2.isContourConvex(approx):
                    x, y, w, h = cv2.boundingRect(approx)
                    aspect_ratio = w / float(h)
                    if 0.9 < aspect_ratio < 1.1 and 100 < w < 300:
                        quadrados.append((x, y, w, h))

        # Agrupar quadrados próximos para tentar encontrar a grade
        if len(quadrados) >= 16:
            # Tenta encontrar a região englobando todos os quadrados
            xs = [x for x, y, w, h in quadrados]
            ys = [y for x, y, w, h in quadrados]
            ws = [w for x, y, w, h in quadrados]
            hs = [h for x, y, w, h in quadrados]
            x_min, y_min = min(xs), min(ys)
            x_max, y_max = max([x + w for x, w in zip(xs, ws)]), max(
                [y + h for y, h in zip(ys, hs)]
            )
            cv2.rectangle(screenshot, (x_min, y_min), (x_max, y_max), GREEN, 3)
            grade = screenshot[y_min:y_max, x_min:x_max]
            debug.save_image(grade, "grade")
        else:
            print("Grade não encontrada. Quadrados detectados:", len(quadrados))

        # Salva a região da grade para screenshots futuras
        self.grade_region = {
            "top": y_min,
            "left": x_min,
            "width": x_max - x_min,
            "height": y_max - y_min,
        }

        # Mostrar debug opcional
        for i, (x, y, w, h) in enumerate(quadrados):
            cv2.rectangle(screenshot, (x, y), (x + w, y + h), BLUE, 1)
            tile = screenshot[y : y + h, x : x + w]
            debug.save_image(tile, f"tile_{i:02}")
        debug.save_image(screenshot, "screenshot com quadrados")
        quadrados_ordenados = sorted(quadrados, key=lambda q: (q[0], q[1]))
        return self.grade_region, quadrados_ordenados

    def extrair_tiles(self, grade_img, quadrados, offset=(0, 0)):
        ox, oy = offset

        resultados_ocr = []
        for x, y, w, h in quadrados:
            # Ajusta coordenadas relativas ao recorte da grade
            tile = grade_img[(y - oy) : (y - oy + h), (x - ox) : (x - ox + w)]
            texto = self._ler_texto(tile)
            resultados_ocr.append(texto)
        return np.array(resultados_ocr).reshape((4, 4))

    def _ler_texto(self, img):
        resultado = self.reader.readtext(img, detail=0, paragraph=False)
        return resultado[0] if resultado else None

    def __del__(self):
        self.sct.close()
