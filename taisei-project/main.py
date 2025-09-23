import logging
import statistics
import time
from collections import deque
from datetime import timedelta
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

# --- Variáveis globais para ETA ---
TOTAL_RUNS = 0
COMPLETED_RUNS = 0
SKIPPED_RUNS = 0
START_TIME = None
RUN_TIMES = deque(maxlen=10)  # média móvel


def capture_score_image(bot: Bot, run_info: dict) -> Path:
    """Captura a imagem de score e salva em SCORES_DIR."""
    screenshot = bot.sensor.get_screenshot()
    x, y, w, h = SCORE_ROI
    cropped = screenshot[y : y + h, x : x + w]

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
    return image_path


def get_run_filename(
    strategy: DodgeStrategy, run_index: int, bomb, travel_time, cell_size
) -> Path:
    """Retorna o caminho esperado da imagem de score para esse run."""
    file_name = f"{strategy.name}_EASY_run{run_index}_bomb{bomb}_travel_time{travel_time}_cell_size{cell_size}.png"
    return SCORES_DIR / file_name


def run_tests(bot: Bot, strategy: DodgeStrategy, n_runs: int):
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
    global COMPLETED_RUNS, SKIPPED_RUNS, START_TIME
    bot.think.set_travel_time_mult(travel_time)
    bot.think.set_cell_size_mult(cell_size)

    for run_index in range(n_runs):
        image_path = get_run_filename(strategy, run_index, bomb, travel_time, cell_size)

        # Se o arquivo já existir, pula
        if image_path.exists():
            logger.info(f"[SKIP] Já existe: {image_path.name}")
            SKIPPED_RUNS += 1
            COMPLETED_RUNS += 1
            continue

        while not bot.is_active():
            time.sleep(1)
        logger.info(
            f"Iteração {run_index+1}/{n_runs} | {strategy.name} | "
            f"bomb={bomb} | travel_time={travel_time} | cell_size={cell_size}"
        )
        if START_TIME is None:
            START_TIME = time.perf_counter()

        run_start = time.perf_counter()
        try:
            bot.start()
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
        finally:
            COMPLETED_RUNS += 1

            exec_time = time.perf_counter() - run_start
            RUN_TIMES.append(exec_time)

            if RUN_TIMES:
                avg_time = sum(RUN_TIMES) / len(RUN_TIMES)
                remaining = avg_time * (TOTAL_RUNS - COMPLETED_RUNS)

                # intervalo de confiança simples com desvio padrão
                if len(RUN_TIMES) > 1:
                    stdev = statistics.stdev(RUN_TIMES)
                    lower = max(0, remaining - stdev * (TOTAL_RUNS - COMPLETED_RUNS))
                    upper = remaining + stdev * (TOTAL_RUNS - COMPLETED_RUNS)
                    eta_str = f"{timedelta(seconds=int(lower))} ~ {timedelta(seconds=int(upper))}"
                else:
                    eta_str = f"{timedelta(seconds=int(remaining))}"

                logger.info(
                    f"[{COMPLETED_RUNS}/{TOTAL_RUNS}] "
                    f"Última execução levou {timedelta(seconds=int(exec_time))} | "
                    f"ETA restante: {eta_str}"
                )


if __name__ == "__main__":
    bot = Bot(DodgeStrategy.MIX_DISTANCIA_DENSIDADE)
    while not bot.is_active():
        time.sleep(1)

    # Calcula total de execuções planejadas
    N_RUNS = 20
    TOTAL_RUNS = 0
    for strategy in DodgeStrategy:
        TOTAL_RUNS += 2 * N_RUNS  # bomb False/True
        TOTAL_RUNS += 4 * N_RUNS  # travel_time options
        if "DENSIDADE" in strategy.name:
            TOTAL_RUNS += 5 * N_RUNS  # cell_size options

    for strategy in DodgeStrategy:
        run_tests(bot, strategy, N_RUNS)

    logger.info("Execução finalizada. Todas as imagens de score foram salvas.")
