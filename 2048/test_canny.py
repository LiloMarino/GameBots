import cv2
import numpy as np

# Carrega imagem em escala de cinza
original_img = cv2.imread("debug/screenshot gray.png", cv2.IMREAD_GRAYSCALE)


def nothing(x):
    pass


cv2.namedWindow("Canny Tuner")
cv2.createTrackbar("Blur Kernel", "Canny Tuner", 5, 20, nothing)
cv2.createTrackbar("Blur Sigma", "Canny Tuner", 1, 50, nothing)
cv2.createTrackbar("Threshold1", "Canny Tuner", 50, 255, nothing)
cv2.createTrackbar("Threshold2", "Canny Tuner", 150, 255, nothing)
cv2.createTrackbar("Morph W", "Canny Tuner", 7, 20, nothing)
cv2.createTrackbar("Morph H", "Canny Tuner", 7, 20, nothing)
cv2.createTrackbar("Iterations", "Canny Tuner", 2, 10, nothing)

while True:
    # Trackbars
    k = cv2.getTrackbarPos("Blur Kernel", "Canny Tuner")
    s = cv2.getTrackbarPos("Blur Sigma", "Canny Tuner")
    t1 = cv2.getTrackbarPos("Threshold1", "Canny Tuner")
    t2 = cv2.getTrackbarPos("Threshold2", "Canny Tuner")
    mw = cv2.getTrackbarPos("Morph W", "Canny Tuner")
    mh = cv2.getTrackbarPos("Morph H", "Canny Tuner")
    it = cv2.getTrackbarPos("Iterations", "Canny Tuner")

    k = max(1, k)
    if k % 2 == 0:
        k += 1
    s = max(1, s)
    mw, mh = max(1, mw), max(1, mh)
    it = max(1, it)

    # Gaussian Blur
    blurred = cv2.GaussianBlur(original_img, (k, k), sigmaX=s)

    # Canny
    edges = cv2.Canny(blurred, t1, max(t1 + 1, t2))

    # Morph close
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (mw, mh))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=it)

    # Contornos
    contours, _ = cv2.findContours(closed, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    contoured_img = cv2.cvtColor(original_img, cv2.COLOR_GRAY2BGR)

    count = 0
    for c in contours:
        if cv2.contourArea(c) > 1000:  # Ignorar ruídos
            cv2.drawContours(contoured_img, [c], -1, (0, 255, 0), 2)
            count += 1

    cv2.putText(
        contoured_img,
        f"Contornos detectados: {count}",
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 0, 0),
        2,
    )

    # Exibir
    cv2.imshow("Canny", edges)
    cv2.imshow("Closed", closed)
    cv2.imshow("Contornos", contoured_img)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cv2.destroyAllWindows()
