import cv2

# Carrega a imagem de teste
img = cv2.imread("taisei-project/debug/debug_1.png")

if img is None:
    raise FileNotFoundError("Imagem não encontrada!")

# Parâmetros de recorte iniciais
x, y, w, h = 0, 0, img.shape[1], img.shape[0]

cv2.namedWindow("Cropped")

while True:
    # Mostra o recorte
    cropped = img[y : y + h, x : x + w]
    cv2.imshow("Cropped", cropped)

    key = cv2.waitKey(30) & 0xFF  # espera 30ms por tecla

    if key == ord("q"):
        break
    elif key == ord("w"):
        y = max(0, y - 1)
    elif key == ord("s"):
        y = min(img.shape[0] - h, y + 1)
    elif key == ord("a"):
        x = max(0, x - 1)
    elif key == ord("d"):
        x = min(img.shape[1] - w, x + 1)
    elif key == ord("i"):
        h = min(img.shape[0] - y, h + 1)
    elif key == ord("k"):
        h = max(1, h - 1)
    elif key == ord("j"):
        w = max(1, w - 1)
    elif key == ord("l"):
        w = min(img.shape[1] - x, w + 1)

cv2.destroyAllWindows()
print(f"Recorte final: x={x}, y={y}, w={w}, h={h}")
