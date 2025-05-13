from time import sleep

from core.debug import save_image
from core.sensor import Sensor

visor = Sensor("Google Chrome")
sleep(2)
save_image(visor.get_screenshot(), "screenshot")
visor.get_grade()
