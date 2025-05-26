# Makefile

# Caminho do script principal
PASTA=2048
MAIN=main.py

# Nome dos arquivos de saída
CPROFILE_OUT=saida.prof
LINEPROFILE_OUT=saida.lprof

# ---------- CProfile ----------
snakeviz: cprofile
	snakeviz $(CPROFILE_OUT)

cprofile:
	cd $(PASTA) && python -m cProfile -o $(CPROFILE_OUT) $(MAIN)

# ---------- Line Profiler ----------
lineprofile:
	cd $(PASTA) && kernprof -l -v -o $(LINEPROFILE_OUT) $(MAIN)

lineprofile-view:
	python -m line_profiler $(LINEPROFILE_OUT)

# ---------- Limpeza ----------
clean:
	del /Q *.prof *.lprof 2>nul
	@echo Arquivos ja limpos
