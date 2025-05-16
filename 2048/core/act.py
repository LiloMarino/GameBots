import pyautogui


class Act:
    def executar_jogada(self, movimento: str):
        pyautogui.press(movimento)
