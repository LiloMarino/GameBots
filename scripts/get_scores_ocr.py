import logging
from pathlib import Path

import easyocr
import pandas as pd
from logger_config import logger
from PIL import Image

logger.setLevel(logging.DEBUG)

RESULTADOS_DIR = Path("../resultados")
SCORES_DIR = RESULTADOS_DIR / "score_images"
OUTPUT_FILE = RESULTADOS_DIR / "resultados_dodge_final.parquet"


def parse_filename(file_name: str) -> dict:
    """
    Converte o nome do arquivo em um dicionário com estratégia, dificuldade, run, bomb, desloc, cell_size.
    Exemplo de nome: MENOR_DISTANCIA_EASY_run0_bombTrue_desloc1.0_cell_size1.0.png
    """
    base = Path(file_name).stem
    parts = base.split("_")
    info = {
        "strategy": parts[0],
        "difficulty": parts[1],
        "run_index": int(parts[2].replace("run", "")),
        "bomb": None,
        "desloc": None,
        "cell_size": None,
    }
    for part in parts[3:]:
        if part.startswith("bomb"):
            info["bomb"] = part.replace("bomb", "") == "True"
        elif part.startswith("desloc"):
            info["desloc"] = float(part.replace("desloc", ""))
        elif part.startswith("cell_size"):
            info["cell_size"] = float(part.replace("cell_size", ""))
    return info


def ocr_score_image(reader, image_path: Path) -> int:
    """
    Aplica EasyOCR na imagem do score e retorna o valor como inteiro.
    """
    img = Image.open(image_path)
    result = reader.readtext(img, detail=0, paragraph=False)
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
