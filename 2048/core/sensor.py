import cv2
import mss
import numpy as np
import pygetwindow as gw
from core import debug


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

    def get_screenshot(self):
        if self.region:
            img = np.array(self.sct.grab(self.region))
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return None

    def get_grade(self):
        if self.grade_region:
            img = np.array(self.sct.grab(self.grade_region))
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        else:
            img = self.get_screenshot()
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            # Intevalo de cor HSV do marrom da borda
            lower = np.array([26, 18, 60])
            upper = np.array([29, 21, 61])

            # Cria uma máscara usando o intervalo HSV
            mask = cv2.inRange(hsv, lower, upper)
            debug.save_image(mask, "mask")

            # Encontra contornos da máscara
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            if contours:
                # Pega o maior contorno (provavelmente a grade)
                largest = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest)
                grid = img[y : y + h, x : x + w]
                debug.save_image(grid, "grid")
                return grid

    def __del__(self):
        self.sct.close()
