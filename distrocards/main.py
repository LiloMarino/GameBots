import threading

import keyboard
from core.act import Act
from core.sensor import Sensor
from core.think import Think
from logger_config import logger
from runner import KEY, toggle_bot

# Hotkey
threading.Thread(
    target=lambda: keyboard.add_hotkey(KEY, toggle_bot), daemon=True
).start()
logger.info(f"Pressione {KEY} para pausar ou retomar o bot.")

sensor = Sensor("DistroCards")
think = Think()
act = Act()
