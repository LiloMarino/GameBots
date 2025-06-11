from pathlib import Path

import cv2

DEBUG_DIR = Path("debug")
DEBUG_DIR.mkdir(parents=True, exist_ok=True)


def save_image(image: cv2.typing.MatLike, name: str):
    image_path = DEBUG_DIR / f"{name}.png"
    cv2.imwrite(str(image_path), image)
