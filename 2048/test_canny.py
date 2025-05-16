import cv2

# Carrega a imagem (pode ser o gray ou o blur, já tratado antes)
img = cv2.imread("screenshot gaussian blur.png", cv2.IMREAD_GRAYSCALE)


def nothing(x):
    pass


# Cria janela com trackbars
cv2.namedWindow("Canny Tuner")
cv2.createTrackbar("Threshold 1", "Canny Tuner", 10, 255, nothing)
cv2.createTrackbar("Threshold 2", "Canny Tuner", 50, 255, nothing)

while True:
    t1 = cv2.getTrackbarPos("Threshold 1", "Canny Tuner")
    t2 = cv2.getTrackbarPos("Threshold 2", "Canny Tuner")

    # Evita t2 menor que t1
    t2 = max(t1 + 1, t2)

    # Aplica Canny com os thresholds escolhidos
    edges = cv2.Canny(img, t1, t2)

    # Mostra a imagem resultante
    cv2.imshow("Canny Tuner", edges)

    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC para sair
        break

cv2.destroyAllWindows()
