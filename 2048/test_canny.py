import cv2
import numpy as np

# Carrega imagem em escala de cinza
original_img = cv2.imread("screenshot gray.png", cv2.IMREAD_GRAYSCALE)


def nothing(x):
    pass


# Janela de controle
cv2.namedWindow("Canny Tuner")
cv2.createTrackbar("Blur Kernel", "Canny Tuner", 1, 20, nothing)
cv2.createTrackbar("Blur Sigma", "Canny Tuner", 0, 100, nothing)
cv2.createTrackbar("Threshold 1", "Canny Tuner", 5, 255, nothing)
cv2.createTrackbar("Threshold 2", "Canny Tuner", 10, 255, nothing)

while True:
    # Trackbar configs
    ksize = cv2.getTrackbarPos("Blur Kernel", "Canny Tuner")
    sigma = cv2.getTrackbarPos("Blur Sigma", "Canny Tuner")
    t1 = cv2.getTrackbarPos("Threshold 1", "Canny Tuner")
    t2 = cv2.getTrackbarPos("Threshold 2", "Canny Tuner")

    # Garantir kernel ímpar e válido
    ksize = max(1, ksize)
    if ksize % 2 == 0:
        ksize += 1

    # --- Abordagem 1: Gaussian + Canny puro
    blurred = cv2.GaussianBlur(original_img, (ksize, ksize), sigmaX=sigma)
    t2 = max(t1 + 1, t2)
    canny_puro = cv2.Canny(blurred, t1, t2)

    # --- Abordagem 2: + Morph Close
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(canny_puro, cv2.MORPH_CLOSE, kernel)

    # --- Abordagem 3: + Dilate → Erode
    dilated = cv2.dilate(canny_puro, kernel, iterations=1)
    morphed = cv2.erode(dilated, kernel, iterations=1)

    # --- Abordagem 4: Bilateral + Canny com thresholds automáticos
    bilateral = cv2.bilateralFilter(original_img, d=9, sigmaColor=75, sigmaSpace=75)
    v = np.median(bilateral)
    auto_t1 = int(max(0, 0.66 * v))
    auto_t2 = int(min(255, 1.33 * v))
    auto_canny = cv2.Canny(bilateral, auto_t1, auto_t2)

    # Mostrar resultados lado a lado
    cv2.imshow("Canny Puro", canny_puro)
    cv2.imshow("Morph Close", closed)
    cv2.imshow("Dilate -> Erode", morphed)
    cv2.imshow("Auto Canny + Bilateral", auto_canny)

    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC
        break

cv2.destroyAllWindows()
