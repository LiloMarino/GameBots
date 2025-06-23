from __future__ import annotations

import random
from enum import Enum, auto
from typing import TYPE_CHECKING, Iterator

import cv2
from logger_config import logger
from skimage.metrics import structural_similarity as ssim

if TYPE_CHECKING:
    import numpy as np
    from core.sensor import Card


class PairStrategy(Enum):
    SSIM = auto()
    TEMPLATE_MATCHING = auto()


class Think:
    def __init__(self, strategy: PairStrategy = PairStrategy.SSIM) -> None:
        self.cards: dict[Card, None | np.ndarray] = {}
        self.set_pair_strategy(strategy)

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

    def is_pair(self, card1: Card, card2: Card, threshold: float = 0.9) -> bool:
        img1 = self.cards[card1]
        img2 = self.cards[card2]

        if img1 is None or img2 is None:
            return False

        return self.pair_check(img1, img2, threshold)

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
        # TODO: Implementar pareamento por template matching
        pass

    @property
    def discovered_cards(self) -> Iterator[Card]:
        return (card for card, img in self.cards.items() if img is not None)

    @property
    def undiscovered_cards(self) -> Iterator[Card]:
        return (card for card, img in self.cards.items() if img is None)
