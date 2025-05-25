# 2048

- Comparar tempo de execução médio dos 4 métodos em 20 movimentos em 50 partidas?:
  - Tesseract + Canny Edge
  - Tesseract + Detecção por cor
  - EasyOCR + Canny Edge
  - EasyOCR + Detecção por cor

- Explicar os problemas encontrados no Canny Edge, (explicar qual foi o erro e como ele foi corrigido):
  - Necessidade de + Gaussian Blur
  - Necessidade de Morfologia de fechamento (Escreve isso?)

Apresentou diversos problemas na presença dos números 128, 256 e 512. Razão: Efeitos de brilho.

- Comparar performance da heurística de movimento utilizando a detecção que teve o menos problemas:
  - Gráfico comparativo de maior número atingido durante X partidas até o fim
  - Gráfico comparativo de score atingido durante X partidas até o fim
  - Gráfico comparativo de maior número atingido durante X partidas limitado a X movimentos
  - Gráfico comparativo de score atingido durante X partidas limitado a X movimentos

Explicar que os gráficos que vão até o fim são muito sensíveis a sorte, tanto da configuração inicial e da posição em que 
os números podem ser gerados ao longo do jogo, permitindo que partidas que tiveram sorte cheguem mais longe
obtendo score e números maiores, enquanto e que limitando a X movimentos reduz os efeitos da sorte.