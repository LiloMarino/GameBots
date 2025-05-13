import cv2
import mss
import numpy as np
import pygetwindow as gw


class Sensor:
    def __init__(self, window_name: str):
        self.region = self.get_window(window_name)
        # Mantém o MSS aberto enquanto o objeto existir
        self.sct = mss.mss()

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

    def __del__(self):
        self.sct.close()
