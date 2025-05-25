import pyautogui


class Act:
    def executar_jogada(self, movimento: str):
        pyautogui.press(movimento)

    def click(self, x: int, y: int):
        pyautogui.click(x, y)
