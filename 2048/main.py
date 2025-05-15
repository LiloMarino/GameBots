from time import sleep

from core.debug import save_image
from core.sensor import Sensor

visor = Sensor("Google Chrome")
_, tiles = visor.detectar_grade_canny_edge()
offset = (visor.grade_region["left"], visor.grade_region["top"])
dados = visor.extrair_tiles(visor.get_screenshot(visor.grade_region), tiles, offset)
print(dados)
