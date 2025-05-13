import os

import cv2

DEBUG_DIR = "debug"
os.makedirs(DEBUG_DIR, exist_ok=True)


def save_image(image, name: str):
    cv2.imwrite(os.path.join(DEBUG_DIR, f"{name}.png"), image)
