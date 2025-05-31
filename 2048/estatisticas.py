import json

import numpy as np
from matplotlib import pyplot as plt

# Carrega os resultados
with open("resultados.json", "r") as f:
    resultados = json.load(f)

# Gráfico 1: Tempo médio por combinação
plt.figure()
labels = []
tempos_medios = []

for r in resultados:
    label = f"{r['ocr']} + {r['grade']}"
    labels.append(label)
    tempos_medios.append(np.mean(r["tempos"]))

plt.bar(labels, tempos_medios, color="skyblue")
plt.xticks(rotation=45, ha="right")
plt.title("Tempo médio por combinação de métodos")
plt.ylabel("Tempo médio (s)")
plt.tight_layout()
plt.savefig("grafico_tempo_medio.png")

# Gráfico 2: Maior pontuação por partida (de um método específico)
r = resultados[0]  # ou filtre pelo método desejado
plt.figure()
plt.bar(range(1, len(r["pontuacoes"]) + 1), r["pontuacoes"], color="orange")
plt.title(f"Pontuação por partida ({r['ocr']} + {r['grade']})")
plt.xlabel("Partida")
plt.ylabel("Pontuação")
plt.tight_layout()
plt.savefig("grafico_pontuacoes_partida.png")

# Gráfico 3: Maior número por partida (mesmo método fixo)
plt.figure()
plt.bar(range(1, len(r["maiores_numeros"]) + 1), r["maiores_numeros"], color="green")
plt.title(f"Maior número por partida ({r['ocr']} + {r['grade']})")
plt.xlabel("Partida")
plt.ylabel("Maior número")
plt.tight_layout()
plt.savefig("grafico_maiores_numeros_partida.png")

# Gráfico 4: Total de falhas por combinação
plt.figure()
labels = []
falhas = []

for r in resultados:
    label = f"{r['ocr']} + {r['grade']}"
    labels.append(label)
    falhas.append(r["falhas_grid"])

plt.bar(labels, falhas, color="red")
plt.xticks(rotation=45, ha="right")
plt.title("Falhas de grid por combinação de métodos")
plt.ylabel("Total de falhas")
plt.tight_layout()
plt.savefig("grafico_falhas_grid.png")
