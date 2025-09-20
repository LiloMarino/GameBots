import logging
import time
from pathlib import Path

import cv2
from bot import Bot
from core.think import DodgeStrategy
from logger_config import logger

logger.setLevel(logging.DEBUG)

RESULTADOS_DIR = Path("../resultados")
RESULTADOS_DIR.mkdir(exist_ok=True)
SCORES_DIR = RESULTADOS_DIR / "score_images"
SCORES_DIR.mkdir(exist_ok=True)
SCORE_ROI = (1429, 107, 231, 58)


def capture_score_image(bot: Bot, run_info: dict):
    # Captura score
    screenshot = bot.sensor.get_screenshot()
    x, y, w, h = SCORE_ROI
    cropped = screenshot[y : y + h, x : x + w]

    # Monta o nome do arquivo
    file_name = f"{run_info['strategy']}_EASY_run{run_info['run_index']}"
    for key in ["bomb", "travel_time", "cell_size"]:
        if key in run_info:
            file_name += f"_{key}{run_info[key]}"

    # Salva a imagem
    image_path = SCORES_DIR / f"{file_name}.png"
    cv2.imwrite(str(image_path), cropped)
    logger.debug(f"Score salvo: {image_path}")
    return image_path


def run_tests(bot: Bot, strategy: DodgeStrategy, n_runs=10):
    bot.think.set_dodge_strategy(strategy)

    bombs_options = [True, False]
    travel_time_options = [0.5, 1.0, 1.5, 2.0]
    cell_size_options = [0.5, 1.0, 1.5, 2.0, 3.0]

    for bomb in bombs_options:
        execute_runs(bot, strategy, n_runs, bomb=bomb)

    for travel_time in travel_time_options:
        execute_runs(bot, strategy, n_runs, travel_time=travel_time)

    if "DENSIDADE" in strategy.name:
        for cell_size in cell_size_options:
            execute_runs(bot, strategy, n_runs, cell_size=cell_size)


def execute_runs(
    bot: Bot,
    strategy: DodgeStrategy,
    n_runs: int,
    bomb: bool = False,
    travel_time: float = 1,
    cell_size: float = 1,
):
    bot.think.set_travel_time_mult(travel_time)
    bot.think.set_cell_size_mult(cell_size)
    for run_index in range(n_runs):
        while not bot.is_active():
            time.sleep(1)
        logger.info(
            f"Iteração {run_index+1}/{n_runs} | {strategy.name} | bomb={bomb} | travel_time={travel_time} | cell_size={cell_size}"
        )
        bot.start()

        try:
            bot.run(use_bombs=bomb)
            bot.restart()
        except Exception as e:
            logger.error(f"Erro durante execução: {e}")

        run_info = {
            "strategy": strategy.name,
            "run_index": run_index,
            "bomb": bomb,
            "travel_time": travel_time,
            "cell_size": cell_size,
        }
        capture_score_image(bot, run_info)


if __name__ == "__main__":
    bot = Bot(DodgeStrategy.MIX_DISTANCIA_DENSIDADE)
    while not bot.is_active():
        time.sleep(1)

    for strategy in DodgeStrategy:
        run_tests(bot, strategy, n_runs=10)

    logger.info("Execução finalizada. Todas as imagens de score foram salvas.")
