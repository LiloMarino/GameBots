from pathlib import Path

import cv2
import numpy as np
from logger_config import logger

DEBUG_DIR = Path("debug")
DEBUG_DIR.mkdir(parents=True, exist_ok=True)
SCALE = 0.5

debug_img: np.ndarray = np.zeros((0, 0, 3), dtype=np.uint8)
frame_count = 0


def debug_show():
    return
    global frame_count
    frame_count += 1
    cv2.imshow(
        "YOLO Debug",
        cv2.resize(debug_img, (0, 0), fx=SCALE, fy=SCALE),
    )
    if frame_count % 1 == 0:
        logger.debug(f"Salvando imagem {frame_count}")
        save_image(debug_img, f"debug_{frame_count}")
    cv2.waitKey(1)


def save_image(image: cv2.typing.MatLike, name: str, clip: bool = True):
    return
    if clip:
        x, y, w, h = 313, 35, 862, 1007
        image = image[y : y + h, x : x + w]

    image_path = DEBUG_DIR / f"{name}.png"
    cv2.imwrite(str(image_path), image)


def draw_arrow(
    start: tuple[int, int],
    direction: tuple[float, float],
    img: np.ndarray | None = None,
    color: tuple[int, int, int] = (0, 255, 0),
    scale: int = 50,
) -> None:
    return
    """
    Desenha uma seta em uma imagem a partir de um ponto inicial na direção de um vetor.

    Args:
        img: Imagem onde a seta será desenhada.
        start: Coordenada inicial (x, y).
        direction: Vetor de direção (dx, dy).
        color: Cor da seta em BGR (padrão: verde).
        scale: Escala/tamanho da seta (padrão: 50).
    """
    dx, dy = direction
    # Normaliza o vetor para comprimento 1
    norm = np.hypot(dx, dy)
    if norm == 0:
        return  # direção nula, não desenha nada
    dx, dy = dx / norm, dy / norm
    end_point = (int(start[0] + dx * scale), int(start[1] + dy * scale))
    if img is None:
        img = debug_img
    cv2.arrowedLine(img, start, end_point, color, 2, tipLength=0.3)
