import pyautogui


class Act:
    def click(self, x: int, y: int):
        pyautogui.click(x, y)
