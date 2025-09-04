from pathlib import Path

import cv2
import numpy as np

DEBUG_DIR = Path("debug")
DEBUG_DIR.mkdir(parents=True, exist_ok=True)
SCALE = 0.5

debug_img: np.ndarray = np.zeros((0, 0, 3), dtype=np.uint8)
frame_count = 0


def debug_show():
    global frame_count
    frame_count += 1
    cv2.imshow(
        "YOLO Debug",
        cv2.resize(debug_img, (0, 0), fx=SCALE, fy=SCALE),
    )
    if frame_count % 20 == 0:
        save_image(debug_img, f"debug_{frame_count}")
    cv2.waitKey(1)


def save_image(image: cv2.typing.MatLike, name: str):
    image_path = DEBUG_DIR / f"{name}.png"
    cv2.imwrite(str(image_path), image)
