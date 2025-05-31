import cv2
import numpy as np


def nothing(x):
    pass


# Carregar imagem colorida
original_img = cv2.imread("debug/screenshot.png")
hsv_img = cv2.cvtColor(original_img, cv2.COLOR_BGR2HSV)


def on_mouse(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        pixel = hsv_img[y, x]
        print(f"HSV em ({x},{y}): {pixel}")


# Criar janelas
cv2.namedWindow("Color Tuner")
cv2.namedWindow("Original")

# HSV min
cv2.createTrackbar("H Min", "Color Tuner", 14, 360, nothing)
cv2.createTrackbar("S Min", "Color Tuner", 37, 100, nothing)
cv2.createTrackbar("V Min", "Color Tuner", 187, 100, nothing)

# HSV max
cv2.createTrackbar("H Max", "Color Tuner", 14, 360, nothing)
cv2.createTrackbar("S Max", "Color Tuner", 37, 100, nothing)
cv2.createTrackbar("V Max", "Color Tuner", 187, 100, nothing)

# Callback para pegar HSV com clique
cv2.setMouseCallback("Original", on_mouse)

while True:
    # Ler valores dos sliders
    h_min = cv2.getTrackbarPos("H Min", "Color Tuner")
    s_min = cv2.getTrackbarPos("S Min", "Color Tuner")
    v_min = cv2.getTrackbarPos("V Min", "Color Tuner")

    h_max = cv2.getTrackbarPos("H Max", "Color Tuner")
    s_max = cv2.getTrackbarPos("S Max", "Color Tuner")
    v_max = cv2.getTrackbarPos("V Max", "Color Tuner")

    # Criar máscaras com base nos valores
    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])

    mask = cv2.inRange(hsv_img, lower, upper)

    # Aplicar máscara na imagem original
    result = cv2.bitwise_and(original_img, original_img, mask=mask)

    # Mostrar resultado
    cv2.imshow("Original", original_img)
    cv2.imshow("Mask", mask)
    cv2.imshow("Segmentado", result)

    if cv2.waitKey(1) & 0xFF == 27:  # Esc
        break

cv2.destroyAllWindows()
