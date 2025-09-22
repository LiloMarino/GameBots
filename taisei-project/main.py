import logging
import time
from pathlib import Path

import cv2
from bot import Bot
from core.think import DodgeStrategy
from logger_config import logger

logger.setLevel(logging.INFO)

RESULTADOS_DIR = Path("../resultados")
RESULTADOS_DIR.mkdir(exist_ok=True)
SCORES_DIR = RESULTADOS_DIR / "score_images"
SCORES_DIR.mkdir(exist_ok=True)
SCORE_ROI = (1429, 107, 231, 58)


def capture_score_image(bot: Bot, run_info: dict) -> Path:
    """Captura a imagem de score e salva em SCORES_DIR."""
    screenshot = bot.sensor.get_screenshot()
    x, y, w, h = SCORE_ROI
    cropped = screenshot[y : y + h, x : x + w]

    # Usa o helper para montar o caminho do arquivo
    image_path = get_run_filename(
        strategy=(
            run_info["strategy"]
            if isinstance(run_info["strategy"], DodgeStrategy)
            else DodgeStrategy[run_info["strategy"]]
        ),
        run_index=run_info["run_index"],
        bomb=run_info.get("bomb", False),
        travel_time=run_info.get("travel_time", 1.0),
        cell_size=run_info.get("cell_size", 1.0),
    )

    cv2.imwrite(str(image_path), cropped)
    logger.debug(f"Score salvo: {image_path}")
    return image_path


def get_run_filename(
    strategy: DodgeStrategy, run_index: int, bomb, travel_time, cell_size
) -> Path:
    """Retorna o caminho esperado da imagem de score para esse run."""
    file_name = f"{strategy.name}_EASY_run{run_index}_bomb{bomb}_travel_time{travel_time}_cell_size{cell_size}.png"
    return SCORES_DIR / file_name


def run_tests(bot: Bot, strategy: DodgeStrategy, n_runs=10):
    bot.think.set_dodge_strategy(strategy)

    bombs_options = [False, True]
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
        image_path = get_run_filename(strategy, run_index, bomb, travel_time, cell_size)

        # Se o arquivo já existir, pula
        if image_path.exists():
            logger.info(f"[SKIP] Já existe: {image_path.name}")
            continue

        while not bot.is_active():
            time.sleep(1)

        logger.info(
            f"Iteração {run_index+1}/{n_runs} | {strategy.name} | "
            f"bomb={bomb} | travel_time={travel_time} | cell_size={cell_size}"
        )

        bot.start()

        try:
            bot.run(use_bombs=bomb)
            run_info = {
                "strategy": strategy.name,
                "run_index": run_index,
                "bomb": bomb,
                "travel_time": travel_time,
                "cell_size": cell_size,
            }
            capture_score_image(bot, run_info)
            bot.restart()
        except Exception as e:
            logger.error(f"Erro durante execução: {e}")


if __name__ == "__main__":
    bot = Bot(DodgeStrategy.MIX_DISTANCIA_DENSIDADE)
    while not bot.is_active():
        time.sleep(1)

    for strategy in DodgeStrategy:
        run_tests(bot, strategy, n_runs=20)

    logger.info("Execução finalizada. Todas as imagens de score foram salvas.")
