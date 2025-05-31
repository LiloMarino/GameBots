import logging
import threading
from itertools import product

import keyboard
import matplotlib.pyplot as plt
from core.sensor import GradeMethod, OCRMethod
from logger_config import logger
from runner import KEY, executar_simulacao, toggle_bot

# logger.setLevel(logging.DEBUG)

# Hotkey
threading.Thread(
    target=lambda: keyboard.add_hotkey(KEY, toggle_bot), daemon=True
).start()
logger.info(f"Pressione {KEY} para pausar ou retomar o bot.")

# Parâmetros de simulação
MAX_PARTIDAS = 1
MAX_MOVIMENTOS = 50

resultados = []

# Testar todas as combinações de métodos
combinacoes = list(product(OCRMethod, GradeMethod))
for ocr_method, grade_method in combinacoes:
    estatisticas = executar_simulacao(
        ocr_method=ocr_method,
        grade_method=grade_method,
        max_partidas=MAX_PARTIDAS,
        max_movimentos=MAX_MOVIMENTOS,
    )
    resultados.append(estatisticas)


for metrica in ["pontuacoes", "maiores_numeros", "tempos"]:
    plt.figure()
    for resultado in resultados:
        label = f"{resultado['ocr']} + {resultado['grade']}"
        valores = resultado[metrica]
        plt.plot(valores, marker="o", label=label)
    plt.title(f"{metrica.capitalize()} por partida")
    plt.xlabel("Partida")
    plt.ylabel(metrica.capitalize())
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"grafico_{metrica}.png")  # ou plt.show() se preferir
