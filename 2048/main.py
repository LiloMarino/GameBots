from time import sleep

from core.debug import save_image
from core.sensor import Sensor

visor = Sensor("Google Chrome")
sleep(2)
visor.detectar_grade_canny_edge()
