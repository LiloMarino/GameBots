import cv2
import mss
import numpy as np
import pygetwindow as gw


class Sensor:
    def __init__(self, window_name: str) -> None:
        self.region = self.get_window(window_name)
        self.sct = mss.mss()

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

    def __del__(self):
        self.sct.close()
