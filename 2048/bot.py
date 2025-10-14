import threading
import time

import keyboard
from core.act import Act
from core.sensor import Sensor
from core.think import Think
from logger_config import logger


class Bot:
    def __init__(self, ocr_method, grade_method, hotkey: str = "F8"):
        self.hotkey = hotkey
        self.bot_ativo = False

        # Componentes principais
        self.sensor = Sensor("Google Chrome", ocr_method, grade_method)
        self.think = Think()
        self.act = Act()
        # Atalho para pausar/retomar (mesmo padrão dos outros projetos)
        threading.Thread(
            target=lambda: keyboard.add_hotkey(self.hotkey, self.toggle), daemon=True
        ).start()
        logger.info(f"Pressione {self.hotkey} para pausar ou retomar o bot.")

    def toggle(self):
        self.bot_ativo = not self.bot_ativo
        estado = "ATIVADO" if self.bot_ativo else "PAUSADO"
        logger.info(f"{estado}")

    def reset(self) -> bool:
        coords = self.sensor.match_template("new_game")
        if coords:
            self.act.click(*coords)
            logger.info("Clicou em New Game para reiniciar.")
            time.sleep(0.2)
            return True
        else:
            logger.warning("Botão 'New Game' não encontrado.")
            return False

    def start(self) -> None:
        coords = self.sensor.match_template("new_game")
        if coords is None:
            logger.warning(
                "Não foi possível iniciar o jogo: templates 'new_game'/'play' não encontrados."
            )
            return
        self.act.click(*coords)
        time.sleep(0.2)

    def run(self, max_movimentos: int = 9999):
        # Espera ativação do bot
        while not self.bot_ativo:
            time.sleep(0.5)

        falhas_grid = 0
        movimentos = 0
        ultimo_board = None
        inicio = time.perf_counter_ns()

        while movimentos < max_movimentos:
            while not self.bot_ativo:
                time.sleep(0.5)

            try:
                board = self.sensor.get_grid()
            except Exception as e:
                falhas_grid += 1
                logger.error(f"Falha ao detectar grid ({falhas_grid}ª): {e}")
                # Agregado maior número do board passando board como parâmetro e obtido pontuação independemente se o último board é None ou não
                duracao = time.perf_counter_ns() - inicio
                return ultimo_board, falhas_grid, duracao

            move, next_board = self.think.best_move(board)
            ultimo_board = next_board
            if move:
                self.act.executar_jogada(move)
                movimentos += 1
                logger.debug(f"Movimento {movimentos}/{max_movimentos}")
                time.sleep(0.2)
            else:
                logger.info("Fim de jogo detectado.")
                # Agregado maior número do board passando board como parâmetro e obtido pontuação independemente se o último board é None ou não
                duracao = time.perf_counter_ns() - inicio
                return board, falhas_grid, duracao

        # atingiu limite de movimentos
        logger.info(f"Atingiu o limite de {max_movimentos} movimentos.")
        duracao = time.perf_counter_ns() - inicio
        return ultimo_board, falhas_grid, duracao

    def is_active(self):
        return self.bot_ativo
