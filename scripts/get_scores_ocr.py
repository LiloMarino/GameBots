import logging
from pathlib import Path

import easyocr
import pandas as pd
from PIL import Image

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

RESULTADOS_DIR = Path("../resultados")
SCORES_DIR = RESULTADOS_DIR / "score_images"
OUTPUT_FILE = RESULTADOS_DIR / "resultados_dodge_final.parquet"


def parse_filename(file_name: str) -> dict:
    """
    Converte o nome do arquivo em um dicionário com strategy, difficulty, run_index,
    bomb, travel_time, cell_size.
    Exemplo:
    MENOR_DENSIDADE_EASY_run0_bombFalse_travel_time0.5_cell_size1.png
    """
    base = Path(file_name).stem
    parts = base.split("_")

    # dificuldade sempre será EASY ou HARD (ou outra lista que você defina)
    difficulties = {"EASY", "HARD"}
    diff_idx = next(i for i, p in enumerate(parts) if p in difficulties)

    strategy = "_".join(parts[:diff_idx])  # tudo antes da dificuldade
    difficulty = parts[diff_idx]
    run_index = int(parts[diff_idx + 1].replace("run", ""))

    info = {
        "strategy": strategy,
        "difficulty": difficulty,
        "run_index": run_index,
        "bomb": None,
        "travel_time": None,
        "cell_size": None,
    }

    for part in parts[diff_idx + 2 :]:
        if part.startswith("bomb"):
            info["bomb"] = part.replace("bomb", "") == "True"
        elif part.startswith("travel_time"):
            info["travel_time"] = float(part.replace("travel_time", ""))
        elif part.startswith("cell_size"):
            info["cell_size"] = float(part.replace("cell_size", ""))
    return info


def ocr_score_image(reader, image_path: Path) -> int:
    """
    Aplica EasyOCR na imagem do score e retorna o valor como inteiro.
    """
    result = reader.readtext(str(image_path), detail=0, paragraph=False)
    # Tenta extrair o primeiro número encontrado
    for r in result:
        r_clean = r.replace(",", "").replace(" ", "")
        if r_clean.isdigit():
            return int(r_clean)
    return 0


def generate_parquet_from_scores(scores_dir: Path, output_file: Path):
    reader = easyocr.Reader(["en"], gpu=True)
    dfs = []

    image_files = sorted(scores_dir.glob("*.png"))
    logger.info(f"Processando {len(image_files)} imagens de score...")

    for img_file in image_files:
        info = parse_filename(img_file.name)
        score = ocr_score_image(reader, img_file)
        info["score"] = score
        dfs.append(info)

    df_final = pd.DataFrame(dfs)
    df_final.to_parquet(output_file, index=False)
    logger.info(f"Parquet final gerado em: {output_file}")
    return df_final


if __name__ == "__main__":
    df = generate_parquet_from_scores(SCORES_DIR, OUTPUT_FILE)
    print(df.head())
