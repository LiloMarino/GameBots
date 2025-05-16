from time import sleep

from core.debug import save_image
from core.sensor import Sensor

visor = Sensor("Google Chrome")
dados = visor.get_grid()
print(dados)
