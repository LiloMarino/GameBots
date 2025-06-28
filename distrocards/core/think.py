from __future__ import annotations

import random
import time
from enum import Enum, auto
from typing import TYPE_CHECKING, Iterator

import cv2
import numpy as np
from core import debug
from logger_config import logger
from skimage.metrics import structural_similarity as ssim

if TYPE_CHECKING:
    from core.sensor import Card


class PairStrategy(Enum):
    SSIM = auto()
    TEMPLATE_MATCHING = auto()


def medir_execucao(func):
    """Decorator que mede o tempo da função e salva em self.pair_times."""

    def wrapper(self, *args, **kwargs):
        inicio = time.perf_counter_ns()
        resultado = func(self, *args, **kwargs)
        duracao = time.perf_counter_ns() - inicio
        self.pair_times.append(duracao)
        return resultado

    return wrapper


class Think:
    def __init__(self, strategy: PairStrategy = PairStrategy.SSIM) -> None:
        self.cards: dict[Card, None | np.ndarray] = {}
        self.pair_times: list[int] = []
        self.threshold = 0.9
        self.pair_hits = 0
        self.pair_errors = 0
        self.set_pair_strategy(strategy)

    def set_threshold(self, threshold: float) -> None:
        self.threshold = threshold

    def set_cards(self, cards: list[Card]) -> None:
        logger.info(f"Cartas encontradas: {len(cards)}")
        if len(cards) % 2 != 0:
            logger.error("Quantidade de cartas ímpar detectadas")
            raise Exception("Quantidade de cartas ímpar detectadas")

        self.cards = {card: None for card in cards}

    def set_pair_strategy(self, strategy: PairStrategy) -> None:
        self.strategy = strategy
        self.pair_check = {
            PairStrategy.SSIM: self._is_pair_ssim,
            PairStrategy.TEMPLATE_MATCHING: self._is_pair_template,
        }.get(strategy, self._is_pair_ssim)

    def left_cards(self) -> int:
        return len(self.cards)

    def random_undiscovered(self) -> Card:
        undiscovered = list(self.undiscovered_cards)
        return random.choice(undiscovered)

    def get_pair(self, actual_card: Card) -> Card | None:
        for card in self.discovered_cards:
            if card != actual_card and self.is_pair(actual_card, card):
                return card
        return None

    def get_discovered_pair(self) -> tuple[Card, Card] | None:
        for card1 in self.discovered_cards:
            for card2 in self.discovered_cards:
                if card1 != card2 and self.is_pair(card1, card2):
                    return card1, card2
        return None

    @medir_execucao
    def is_pair(self, card1: Card, card2: Card) -> bool:
        img1 = self.cards[card1]
        img2 = self.cards[card2]

        if img1 is None or img2 is None:
            return False

        # h = min(img1.shape[0], img2.shape[0])
        # img1 = cv2.resize(img1, (int(img1.shape[1] * h / img1.shape[0]), h))
        # img2 = cv2.resize(img2, (int(img2.shape[1] * h / img2.shape[0]), h))
        # img_concat = np.hstack((img1, img2))
        # debug.save_image(img_concat, f"Par {card1} = {card2}")

        return self.pair_check(img1, img2, self.threshold)

    def _is_pair_ssim(
        self, img1: np.ndarray, img2: np.ndarray, threshold: float = 0.9
    ) -> bool:

        # Converte para escala de cinza
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        # Redimensiona para mesma forma se necessário
        if gray1.shape != gray2.shape:
            gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))

        score, *_ = ssim(gray1, gray2, full=True)

        # Limiar de similaridade
        return score > threshold

    def _is_pair_template(
        self, img1: np.ndarray, img2: np.ndarray, threshold: float = 0.9
    ) -> bool:
        # Redimensiona o template (img1) se maior que a imagem base (img2)
        if img1.shape[0] > img2.shape[0] or img1.shape[1] > img2.shape[1]:
            img1 = cv2.resize(img1, (img2.shape[1], img2.shape[0]))

        # Faz o template matching
        result = cv2.matchTemplate(img1, img2, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        # Geração do mapa de confiança e heatmap para debug
        # confidence_map = cv2.normalize(result, None, 0, 255, cv2.NORM_MINMAX)
        # confidence_map = np.uint8(confidence_map)
        # debug.save_image(confidence_map, "confidence_pair_map")

        # heatmap = cv2.applyColorMap(confidence_map, cv2.COLORMAP_JET)
        # debug.save_image(heatmap, "heatmap_template_pair_match")

        return max_val >= threshold

    @property
    def discovered_cards(self) -> Iterator[Card]:
        return (card for card, img in self.cards.items() if img is not None)

    @property
    def undiscovered_cards(self) -> Iterator[Card]:
        return (card for card, img in self.cards.items() if img is None)
