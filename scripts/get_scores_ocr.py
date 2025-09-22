import logging
import re
from pathlib import Path

import easyocr
import pandas as pd
from PIL import Image

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

RESULTADOS_DIR = Path("../resultados")
SCORES_DIR = RESULTADOS_DIR / "score_images"
OUTPUT_FILE = RESULTADOS_DIR / "resultados_dodge_final.parquet"
FILENAME_REGEX = re.compile(
    r"^(?P<strategy>.+)_(?P<difficulty>EASY)_run(?P<run_index>\d+)"
    r"_bomb(?P<bomb>True|False)"
    r"_travel_time(?P<travel_time>\d+(?:\.\d+)?)"
    r"_cell_size(?P<cell_size>\d+(?:\.\d+)?)$"
)


def parse_filename(file_name: str) -> dict:
    """
    Extrai informações do nome do arquivo via regex.
    """
    base = Path(file_name).stem
    match = FILENAME_REGEX.match(base)
    if not match:
        raise ValueError(f"Nome de arquivo inválido: {file_name}")

    info = match.groupdict()
    # Converte tipos
    info["run_index"] = int(info["run_index"])
    info["bomb"] = info["bomb"] == "True"
    info["travel_time"] = float(info["travel_time"])
    info["cell_size"] = float(info["cell_size"])
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
