import json
import logging
import threading
from itertools import product

import keyboard
from core.sensor import GradeMethod, OCRMethod
from logger_config import logger
from runner import KEY, executar_simulacao, toggle_bot

# logger.setLevel(logging.DEBUG)

# Hotkey
threading.Thread(
    target=lambda: keyboard.add_hotkey(KEY, toggle_bot), daemon=True
).start()
logger.info(f"Pressione {KEY} para pausar ou retomar o bot.")

# ---------- FASE 1: Testes de desempenho (OCR + GRID) ----------
MAX_PARTIDAS = 20
MAX_MOVIMENTOS = 50

resultados_fase1 = []
combinacoes = list(product(OCRMethod, GradeMethod))

for ocr_method, grade_method in combinacoes:
    estatisticas = executar_simulacao(
        ocr_method=ocr_method,
        grade_method=grade_method,
        max_partidas=MAX_PARTIDAS,
        max_movimentos=MAX_MOVIMENTOS,
    )
    resultados_fase1.append(estatisticas)

with open("resultados.json", "w") as f:
    json.dump(resultados_fase1, f, indent=2)

# ---------- FASE 2: Teste heurística (100 partidas sem limite) ----------
MAX_PARTIDAS = 100
MAX_MOVIMENTOS = 9999

resultado_fase2 = executar_simulacao(
    ocr_method=OCRMethod.EASYOCR_THREAD,
    grade_method=GradeMethod.COR_FIXED,
    max_partidas=MAX_PARTIDAS,
    max_movimentos=MAX_MOVIMENTOS,
)

with open("resultados_think.json", "w") as f:
    json.dump([resultado_fase2], f, indent=2)
