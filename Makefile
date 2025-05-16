# Makefile

# Caminho do script principal
MAIN=2048/main.py

# Nome dos arquivos de saída
CPROFILE_OUT=saida.prof
LINEPROFILE_OUT=saida.lprof

# ---------- CProfile ----------
snakeviz: cprofile
	snakeviz $(CPROFILE_OUT)

cprofile:
	python -m cProfile -o $(CPROFILE_OUT) $(MAIN)

# ---------- Line Profiler ----------
lineprofile:
	kernprof -l -v -o $(LINEPROFILE_OUT) $(MAIN)

lineprofile-view:
	python -m line_profiler $(LINEPROFILE_OUT)

# ---------- Limpeza ----------
clean:
	del /Q *.prof *.lprof 2>nul
	@echo Arquivos ja limpos
