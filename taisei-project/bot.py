import threading
import time

import keyboard
from core import debug
from core.act import Act
from core.sensor import Difficulty, Sensor
from core.think import DodgeStrategy, Think
from logger_config import logger
from pynput.keyboard import Key


class Bot:
    def __init__(self, dodge_strategy: DodgeStrategy, hotkey="F8"):
        self.hotkey = hotkey
        self.bot_ativo = False

        # Componentes principais
        self.sensor = Sensor("Taisei Project v1.4.4")
        self.think = Think(self.sensor.region, dodge_strategy)
        self.act = Act()

        # Inicia atalho de teclado em uma thread
        threading.Thread(
            target=lambda: keyboard.add_hotkey(self.hotkey, self.toggle), daemon=True
        ).start()
        logger.info(f"Pressione {self.hotkey} para pausar ou retomar o bot.")

    def toggle(self):
        self.bot_ativo = not self.bot_ativo
        estado = "ATIVADO" if self.bot_ativo else "PAUSADO"
        logger.info(f"{estado}")

    def start(self, difficulty: Difficulty = Difficulty.EASY) -> None:
        start_done = False
        difficulty_done = False
        character_done = False

        # Passo 1: Start Game
        if self.sensor.match_template("start_game"):
            self.act.fire()
            time.sleep(1)
            start_done = True
        else:
            logger.info("Start Game não encontrado, tentando continuar...")

        # Passo 2: Escolha de dificuldade
        difficulty_template = f"{difficulty.name.lower()}"
        if self.sensor.match_template(difficulty_template):
            self.act.fire()
            time.sleep(1)
            difficulty_done = True
        else:
            logger.error("Não foi possível selecionar a dificuldade")

        # Passo 3: Seleção de personagem
        if self.sensor.match_template("reimu"):
            self.act.fire()
            time.sleep(1)
            character_done = True
        else:
            logger.error("Não foi possível selecionar a personagem")

        # Verificação final
        if not (start_done and difficulty_done and character_done):
            raise Exception("Não foi possível iniciar o jogo: sequência incompleta")

        # Espera o jogo carregar
        time.sleep(2)

    def run(self, use_bombs=False):
        while not self.bot_ativo:
            time.sleep(1)

        # Alterar para enquanto estiver vidas
        self.act.continuous_fire(True)
        player_not_detected = 0
        while player_not_detected < 100:
            while not self.bot_ativo:
                self.act.continuous_fire(False)
                time.sleep(1)

            screenshot, detections = self.sensor.get_objects()
            if not detections.players:
                player_not_detected += 1
                logger.debug(f"Jogador nao detectado ({player_not_detected})")
                if player_not_detected == 50:
                    logger.info("Tentando pular dialogo...")
                    self.act.speedup_dialog(True)
                    time.sleep(0.5)
                    self.act.speedup_dialog(False)
                self.act.continuous_fire(False)
                continue
            else:
                player_not_detected = 0
                self.act.continuous_fire(True)

            if use_bombs:
                if self.think.is_player_in_danger(detections):
                    # Usa o bomb para preservar a sobrevivência
                    self.act.continuous_fire(False)
                    self.act.bomb()
                    self.act.continuous_fire(True)

            vector, step = self.think.think(screenshot, detections)
            debug.debug_show()
            self.act.dodge(vector, step)
            if not detections.enemies and not detections.bullets:
                if self.sensor.match_template("win"):
                    self.act.continuous_fire(False)
                    return True
        self.act.continuous_fire(False)
        return False

    def benchmark(self, n_iters: int = 200) -> dict:
        while not self.bot_ativo:
            time.sleep(1)
        self.act.continuous_fire(True)
        print("Iniciando benchmark...")
        times = []
        for _ in range(n_iters):
            t0 = time.perf_counter_ns()
            screenshot, detections = self.sensor.get_objects()
            vector, step = self.think.think(screenshot, detections)
            self.act.dodge(vector, step)
            if not detections.enemies and not detections.bullets:
                if self.sensor.match_template("win"):
                    self.act.continuous_fire(False)
            times.append(time.perf_counter_ns() - t0)
        avg_ns = sum(times) / len(times)
        avg_s = avg_ns / 1e9
        fps = 1 / avg_s if avg_s > 0 else 0
        self.act.continuous_fire(False)
        return {
            "avg_loop_s": avg_s,
            "avg_loop_ns": avg_ns,
            "fps_loop": fps,
            "n_iters": n_iters,
        }

    def reset(self, victory: bool = False, timeout: float = 10.0) -> None:
        logger.info("Reiniciando partida...")

        if victory:
            logger.info("Vitória detectada. Tentando abrir menu de pause...")
            # Pressiona ESC algumas vezes para garantir que o pause abriu
            for _ in range(5):
                self.act.press_key(Key.esc)
                # Se conseguiu entrar no pause
                if self.wait_for("options"):
                    logger.info(
                        "Tela de opções detectada. Saindo para o menu inicial..."
                    )
                    # Navega no pause -> Exit
                    self.act.press_key(Key.down)
                    time.sleep(0.5)
                    self.act.press_key(Key.down)
                    time.sleep(0.5)
                    self.act.fire()
                    time.sleep(0.5)
                    self.act.press_key(Key.right)
                    time.sleep(0.5)
                    self.act.fire()
                    time.sleep(0.5)
                    break
                else:
                    logger.warning("Tentativa falhou. Tentando novamente...")
            else:
                logger.error("Não conseguiu abrir menu de pause mesmo após vitória.")

        # Loop para garantir que voltou ao menu inicial
        start_time = time.perf_counter()
        while time.perf_counter() - start_time < timeout:
            # Já está no menu inicial?
            if self.sensor.match_template("start_game"):
                logger.info("Menu inicial detectado. Reset concluído.")
                return

            # Tela de continue → Restart
            if self.sensor.match_template("continue"):
                logger.info("Tela de Continue detectada. Reiniciando...")
                self.act.press_key(Key.down)
                time.sleep(0.5)
                self.act.press_key(Key.down)
                time.sleep(0.5)
                self.act.fire()
                time.sleep(0.5)
                self.act.press_key(Key.right)
                time.sleep(0.5)
                self.act.fire()
                time.sleep(0.5)
                continue

            # Último recurso: tentar abrir menu de pause novamente
            if time.perf_counter() - start_time > timeout / 2:
                self.act.press_key(Key.esc)
                time.sleep(0.5)
                # Se conseguiu entrar no pause
                if self.wait_for("options"):
                    logger.info(
                        "Tela de opções detectada. Saindo para o menu inicial..."
                    )
                    # Navega no pause -> Exit
                    self.act.press_key(Key.down)
                    time.sleep(0.5)
                    self.act.press_key(Key.down)
                    time.sleep(0.5)
                    self.act.fire()
                    time.sleep(0.5)
                    self.act.press_key(Key.right)
                    time.sleep(0.5)
                    self.act.fire()
                    time.sleep(0.5)
                    continue

            time.sleep(0.5)

        if not self.sensor.match_template("start_game"):
            raise TimeoutError("Não voltou para o menu inicial após reset.")

    def wait_for(
        self, template: str, timeout: float = 5.0, interval: float = 0.5
    ) -> bool:
        start = time.perf_counter()
        while time.perf_counter() - start < timeout:
            if self.sensor.match_template(template):
                return True
            time.sleep(interval)
        return False

    def is_active(self):
        return self.bot_ativo
