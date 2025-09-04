from pathlib import Path

import cv2
import numpy as np

DEBUG_DIR = Path("debug")
DEBUG_DIR.mkdir(parents=True, exist_ok=True)
SCALE = 0.5

debug_img: np.ndarray = np.zeros((0, 0, 3), dtype=np.uint8)


def debug_show():
    cv2.imshow(
        "YOLO Debug",
        cv2.resize(debug_img, (0, 0), fx=SCALE, fy=SCALE),
    )
    cv2.waitKey(1)


def save_image(image: cv2.typing.MatLike, name: str):
    image_path = DEBUG_DIR / f"{name}.png"
    cv2.imwrite(str(image_path), image)
