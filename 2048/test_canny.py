import cv2
import numpy as np

# Carrega a imagem em escala de cinza
original_img = cv2.imread("screenshot gray.png", cv2.IMREAD_GRAYSCALE)


def nothing(x):
    pass


# Cria janela com trackbars
cv2.namedWindow("Canny Tuner")
cv2.createTrackbar("Blur Kernel", "Canny Tuner", 1, 20, nothing)  # kernel de 1 a 20
cv2.createTrackbar("Blur Sigma", "Canny Tuner", 1, 100, nothing)  # sigma de 1 a 100
cv2.createTrackbar("Threshold 1", "Canny Tuner", 10, 255, nothing)
cv2.createTrackbar("Threshold 2", "Canny Tuner", 50, 255, nothing)

while True:
    # Lê os valores das trackbars
    ksize = cv2.getTrackbarPos("Blur Kernel", "Canny Tuner")
    sigma = cv2.getTrackbarPos("Blur Sigma", "Canny Tuner")
    t1 = cv2.getTrackbarPos("Threshold 1", "Canny Tuner")
    t2 = cv2.getTrackbarPos("Threshold 2", "Canny Tuner")

    # Garante que o kernel seja ímpar e maior que zero
    ksize = max(1, ksize)
    if ksize % 2 == 0:
        ksize += 1

    # Aplica Gaussian Blur com o kernel e sigma definidos
    blurred = cv2.GaussianBlur(original_img, (ksize, ksize), sigmaX=sigma)

    # Evita t2 menor que t1
    t2 = max(t1 + 1, t2)

    # Aplica Canny
    edges = cv2.Canny(blurred, t1, t2)

    # Mostra o resultado
    cv2.imshow("Canny Tuner", edges)

    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC
        break

cv2.destroyAllWindows()
