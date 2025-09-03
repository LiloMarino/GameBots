import json

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Lendo a imagem
img = cv2.imread("frame_0037.jpg")
img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
draw = ImageDraw.Draw(img_pil)

# Fonte Tahoma
font_path = r"C:\Windows\Fonts\tahoma.ttf"
font = ImageFont.truetype(font_path, 21)

# Lendo JSON
with open("frame_0037.json") as f:
    data = json.load(f)

boxes = data["boxes"]

colors = {
    "Bullet": (255, 165, 0),  # laranja – mantém destaque para os tiros
    "Player": (0, 102, 204),  # azul médio – suave e legível
    "Enemy": (204, 0, 0),  # vermelho escuro – agressivo, distinto do Power
    "Power": (255, 0, 255),  # magenta – chama atenção, diferente de Enemy
    "Score": (0, 204, 0),  # verde vivo – reforça ideia de pontuação
    "Value": (255, 215, 0),  # dourado/amarelo ouro – dá ênfase de “valor”
}

for box in boxes:
    label = box["label"]
    x_center = float(box["x"])
    y_center = float(box["y"])
    width = float(box["width"])
    height = float(box["height"])

    x1 = int(x_center - width / 2)
    y1 = int(y_center - height / 2)
    x2 = int(x_center + width / 2)
    y2 = int(y_center + height / 2)

    # Desenhando retângulo no Pillow
    draw.rectangle(
        [x1, y1, x2, y2], outline=colors.get(label, (255, 255, 255)), width=3
    )


for box in boxes:
    label = box["label"]
    x_center = float(box["x"])
    y_center = float(box["y"])
    width = float(box["width"])
    height = float(box["height"])

    x1 = int(x_center - width / 2)
    y1 = int(y_center - height / 2)
    x2 = int(x_center + width / 2)
    y2 = int(y_center + height / 2)

    # Texto com contorno (simulado)
    draw.text(
        (x1, y1 - 25),
        label,
        font=font,
        fill="white",
        stroke_width=2,
        stroke_fill="black",
    )

# Convertendo de volta para OpenCV
img = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
cv2.imwrite("saida_pillow.jpg", img)
cv2.imshow("Imagem com Boxes", img)
cv2.waitKey(0)
cv2.destroyAllWindows()
