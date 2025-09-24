import logging
import statistics
import time
import uuid
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path

import easyocr
import pandas as pd
from bot import Bot
from core.think import DodgeStrategy
from logger_config import logger

logger.setLevel(logging.INFO)

RESULTADOS_DIR = Path("../resultados")
RESULTADOS_DIR.mkdir(exist_ok=True)
TEMP_BATCH_DIR = RESULTADOS_DIR / "temp_batches"
TEMP_BATCH_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = RESULTADOS_DIR / "resultados_dodge_final.parquet"
TEMP_MERGE_FILE = RESULTADOS_DIR / "resultados_dodge_final.parquet.tmp"
SCORE_ROI = (1429, 107, 231, 58)

# --- Variáveis globais para ETA ---
TOTAL_RUNS = 0
COMPLETED_RUNS = 0
SKIPPED_RUNS = 0
START_TIME = None
RUN_TIMES = deque(maxlen=10)  # média móvel

# --- OCR Reader (inicializa uma vez só) ---
reader = easyocr.Reader(["en"], gpu=True)


def ocr_score(bot: Bot) -> int:
    """Captura ROI do score e aplica OCR."""
    screenshot = bot.sensor.get_screenshot()
    x, y, w, h = SCORE_ROI
    cropped = screenshot[y : y + h, x : x + w]

    result = reader.readtext(cropped, detail=0, paragraph=False)
    for r in result:
        r_clean = r.replace(",", "").replace(" ", "")
        if r_clean.isdigit():
            return int(r_clean)
    return 0


def load_final_results() -> pd.DataFrame:
    """Carrega o parquet final, se existir."""
    if OUTPUT_FILE.exists():
        try:
            df = pd.read_parquet(OUTPUT_FILE)
            logger.info(f"Carregado {len(df)} resultados do {OUTPUT_FILE.name}")
            return df
        except Exception as e:
            logger.error(f"Falha ao ler {OUTPUT_FILE}: {e}")
            return pd.DataFrame()
    return pd.DataFrame()


def list_temp_batches() -> list:
    """Retorna lista de arquivos parquet temporários gerados por batches."""
    return sorted(TEMP_BATCH_DIR.glob("*.parquet"))


def load_all_progress() -> pd.DataFrame:
    """
    Constrói o dataframe com tudo que já foi processado:
    - primeiro o parquet final (se houver)
    - depois todos os temp batches (apêndice)
    Isso permite continuar mesmo sem mesclar ainda o final.
    """
    dfs = []
    df_final = load_final_results()
    if not df_final.empty:
        dfs.append(df_final)

    for p in list_temp_batches():
        try:
            d = pd.read_parquet(p)
            dfs.append(d)
        except Exception as e:
            logger.error(f"Não foi possível ler batch {p.name}: {e}")

    if dfs:
        df_all = pd.concat(dfs, ignore_index=True)
        # garante colunas esperadas
        return df_all
    return pd.DataFrame()


def save_batch_temp(df_batch: pd.DataFrame, tag: str | None = None) -> Path:
    """Salva um dataframe de batch como parquet temporário identificado por tag+uuid."""
    if tag is None:
        tag = "batch"
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    uid = uuid.uuid4().hex[:8]
    fname = f"{tag}_{timestamp}_{uid}.parquet"
    path = TEMP_BATCH_DIR / fname
    df_batch.to_parquet(path, index=False)
    logger.info(f"Batch temporário salvo: {path.name} ({len(df_batch)} linhas)")
    return path


def consolidate_all_to_final():
    """
    Consolida todos os temp batches + final (se existir) em OUTPUT_FILE de forma atômica.
    Após escrita com sucesso, apaga os temp batches.
    """
    logger.info("Consolidando batches temporários no parquet final...")
    parts = []
    # final (se existir)
    if OUTPUT_FILE.exists():
        try:
            parts.append(pd.read_parquet(OUTPUT_FILE))
        except Exception as e:
            logger.error(f"Erro lendo final existente: {e}")

    # batches
    for p in list_temp_batches():
        try:
            parts.append(pd.read_parquet(p))
        except Exception as e:
            logger.error(f"Erro lendo batch {p.name}: {e}")

    if not parts:
        logger.info("Nada para consolidar.")
        return

    df_all = pd.concat(parts, ignore_index=True)
    # dedupe por chave única
    dedup_cols = [
        "strategy",
        "difficulty",
        "run_index",
        "bomb",
        "travel_time",
        "cell_size",
    ]
    df_all = df_all.drop_duplicates(subset=dedup_cols, keep="last").reset_index(
        drop=True
    )

    # write atomically: escrevemos em arquivo temporário e renomeamos
    try:
        df_all.to_parquet(TEMP_MERGE_FILE, index=False)
        # mover/renomear (substitui final)
        Path(TEMP_MERGE_FILE).replace(OUTPUT_FILE)
        logger.info(
            f"Parquet final gravado com {len(df_all)} linhas em {OUTPUT_FILE.name}"
        )
        # apagar batches temporários
        for p in list_temp_batches():
            try:
                p.unlink()
            except Exception:
                logger.warning(f"Não foi possível apagar batch {p.name}")
    except Exception as e:
        logger.error(f"Erro ao gravar parquet final: {e}")
        # se falhar, deixa os temp batches (para recuperação)
        if Path(TEMP_MERGE_FILE).exists():
            try:
                Path(TEMP_MERGE_FILE).unlink()
            except Exception:
                pass
        raise


def build_already_done_set(df_progress: pd.DataFrame) -> set:
    """Cria set de chaves já processadas a partir de um dataframe (ou vazio)."""
    if df_progress is None or df_progress.empty:
        return set()
    keys = set(
        zip(
            df_progress["strategy"],
            df_progress["run_index"],
            df_progress["bomb"],
            df_progress["travel_time"],
            df_progress["cell_size"],
        )
    )
    return keys


def run_tests(bot: Bot, strategy: DodgeStrategy, n_runs: int):
    bot.think.set_dodge_strategy(strategy)

    bombs_options = [False, True]
    travel_time_options = [0.5, 1.0, 1.5, 2.0]
    cell_size_options = [0.5, 1.0, 1.5, 2.0, 3.0]

    # carregamos o progresso atual (final + batches temporários)
    df_progress = load_all_progress()
    already_done = build_already_done_set(df_progress)

    # Para cada combinação, executa um batch e salva parquet temporário ao final do batch
    # OBS: cada execute_runs() salva um arquivo de batch (não atualiza OUTPUT_FILE)
    for bomb in bombs_options:
        execute_runs(bot, strategy, n_runs, bomb, 1.0, 1.0, already_done)

    for travel_time in travel_time_options:
        execute_runs(bot, strategy, n_runs, False, travel_time, 1.0, already_done)

    if "DENSIDADE" in strategy.name:
        for cell_size in cell_size_options:
            execute_runs(bot, strategy, n_runs, False, 1.0, cell_size, already_done)


def execute_runs(
    bot: Bot,
    strategy: DodgeStrategy,
    n_runs: int,
    bomb: bool,
    travel_time: float,
    cell_size: float,
    already_done: set,
    batch_tag: None | str = None,
):
    """
    Roda até n_runs para a tupla (strategy, bomb, travel_time, cell_size).
    Ao final salva um parquet temporário para o batch (não altera OUTPUT_FILE).
    """
    global COMPLETED_RUNS, SKIPPED_RUNS, START_TIME
    bot.think.set_travel_time_mult(travel_time)
    bot.think.set_cell_size_mult(cell_size)

    if batch_tag is None:
        batch_tag = f"{strategy.name}_bomb{bomb}_tt{travel_time}_cs{cell_size}"

    df_new_rows = []

    for run_index in range(n_runs):
        key = (strategy.name, run_index, bomb, travel_time, cell_size)
        if key in already_done:
            logger.info(f"[SKIP] Já existe (final ou temp): {key}")
            SKIPPED_RUNS += 1
            COMPLETED_RUNS += 1
            continue

        # espera o bot ativo
        while not bot.is_active():
            time.sleep(1)

        logger.info(
            f"Iteração {run_index+1}/{n_runs} | {strategy.name} | bomb={bomb} | travel_time={travel_time} | cell_size={cell_size}"
        )

        if START_TIME is None:
            START_TIME = time.perf_counter()

        run_start = time.perf_counter()
        try:
            # Start e run (pode lançar)
            bot.start()
            victory = bot.run(use_bombs=bomb)

            # OCR direto do ROI
            score = ocr_score(bot)

            # informa linha nova
            row = {
                "strategy": strategy.name,
                "difficulty": "EASY",
                "run_index": run_index,
                "bomb": bomb,
                "travel_time": travel_time,
                "cell_size": cell_size,
                "score": score,
                "victory": bool(victory),
            }
            df_new_rows.append(row)

            # marca como feito para este processo (evita repetir dentro do mesmo run/session)
            already_done.add(key)

            # reinicia jogo (pode lançar TimeoutError se não voltar pro menu)
            bot.reset(victory=victory)

        except Exception as e:
            logger.error(f"Erro durante execução da iteração {run_index}: {e}")
            # não adiciona a linha; a iteração é contabilizada como completada para efeitos de ETA
        finally:
            COMPLETED_RUNS += 1
            exec_time = time.perf_counter() - run_start
            RUN_TIMES.append(exec_time)

            # log de ETA
            if RUN_TIMES:
                avg_time = sum(RUN_TIMES) / len(RUN_TIMES)
                remaining = avg_time * (TOTAL_RUNS - COMPLETED_RUNS)
                if len(RUN_TIMES) > 1:
                    stdev = statistics.stdev(RUN_TIMES)
                    lower = max(0, remaining - stdev * (TOTAL_RUNS - COMPLETED_RUNS))
                    upper = remaining + stdev * (TOTAL_RUNS - COMPLETED_RUNS)
                    eta_str = f"{timedelta(seconds=int(lower))} ~ {timedelta(seconds=int(upper))}"
                else:
                    eta_str = f"{timedelta(seconds=int(remaining))}"

                logger.info(
                    f"[{COMPLETED_RUNS}/{TOTAL_RUNS}] Última execução levou {timedelta(seconds=int(exec_time))} | ETA restante: {eta_str}"
                )

    # ao fim do lote, salva um parquet temporário (apêndice)
    if df_new_rows:
        df_batch = pd.DataFrame(df_new_rows)
        save_batch_temp(df_batch, tag=batch_tag)
    else:
        logger.info("Nenhuma nova linha gerada neste batch.")


if __name__ == "__main__":
    bot = Bot(DodgeStrategy.MIX_DISTANCIA_DENSIDADE)
    while not bot.is_active():
        time.sleep(1)

    # Calcula total de execuções planejadas (usado só para ETA)
    N_RUNS = 20  # você pode aumentar para 30 etc.
    TOTAL_RUNS = 0
    for strategy in DodgeStrategy:
        TOTAL_RUNS += 2 * N_RUNS  # bomb False/True
        TOTAL_RUNS += 4 * N_RUNS  # travel_time options
        if "DENSIDADE" in strategy.name:
            TOTAL_RUNS += 5 * N_RUNS  # cell_size options

    # Run: cada estratégia cria seus batches temporários
    for strategy in DodgeStrategy:
        run_tests(bot, strategy, N_RUNS)

    # --- Ao final: consolida tudo num unico parquet final de forma atomica ---
    try:
        consolidate_all_to_final()
        logger.info("Execução finalizada. Resultados consolidados.")
    except Exception as e:
        logger.error(f"Erro durante a consolidação final: {e}")
        logger.info(
            "Os batches temporários ainda estão em resultados/temp_batches/ — você pode consolidá-los manualmente depois."
        )
