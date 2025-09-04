from pathlib import Path

import cv2
import numpy as np

DEBUG_DIR = Path("debug")
DEBUG_DIR.mkdir(parents=True, exist_ok=True)

debug_img: np.ndarray = np.zeros((0, 0, 3), dtype=np.uint8)


def save_image(image: cv2.typing.MatLike, name: str):
    image_path = DEBUG_DIR / f"{name}.png"
    cv2.imwrite(str(image_path), image)
