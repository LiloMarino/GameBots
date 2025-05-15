import cv2
import mss
import numpy as np
import pygetwindow as gw
from core import debug
from core.constants import GREEN, RED


class Sensor:
    def __init__(self, window_name: str):
        self.region = self.get_window(window_name)
        # Mantém o MSS aberto enquanto o objeto existir
        self.sct = mss.mss()
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
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        img_contorns = cv2.drawContours(
            cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR), contours, -1, GREEN, 1
        )
        debug.save_image(img_contorns, "screenshot contornos")

        quadrados = []
        for cnt in contours:
            approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
            if len(approx) == 4 and cv2.isContourConvex(approx):
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = w / float(h)

                # Elimina retângulos e quadrados pequenos e grandes
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
        self.grade_region = (x_min, y_min, x_max, y_max)

        # Mostrar debug opcional
        for x, y, w, h in quadrados:
            cv2.rectangle(screenshot, (x, y), (x + w, y + h), RED, 1)
        debug.save_image(screenshot, "screenshot com quadrados")

    def __del__(self):
        self.sct.close()
