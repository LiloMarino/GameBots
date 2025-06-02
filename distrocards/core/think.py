from __future__ import annotations

import random
from typing import TYPE_CHECKING, Iterator

import cv2
from logger_config import logger
from skimage.metrics import structural_similarity as ssim

if TYPE_CHECKING:
    import numpy as np
    from core.sensor import Card


class Think:
    def __init__(self) -> None:
        self.cards: dict[Card, None | np.ndarray] = {}

    def set_cards(self, cards: list[Card]) -> None:
        logger.info(f"Cartas encontradas: {len(cards)}")
        if len(cards) % 2 != 0:
            logger.error("Quantidade de cartas ímpar detectadas")
            raise Exception("Quantidade de cartas ímpar detectadas")

        self.cards = {card: None for card in cards}

    def left_cards(self) -> int:
        return len(self.cards)

    def random_undiscovered(self) -> Card:
        undiscovered = list(self.undiscovered_cards)
        return random.choice(undiscovered)

    def get_pair(self, actual_card: Card) -> Card | None:
        for card in self.discovered_cards:
            if self.is_pair(actual_card, card):
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

        # Converte para escala de cinza
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        # Redimensiona para mesma forma se necessário
        if gray1.shape != gray2.shape:
            gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))

        score, *_ = ssim(gray1, gray2, full=True)

        # Limiar de similaridade
        return score > threshold

    @property
    def discovered_cards(self) -> Iterator[Card]:
        return (card for card, img in self.cards.items() if img is not None)

    @property
    def undiscovered_cards(self) -> Iterator[Card]:
        return (card for card, img in self.cards.items() if img is None)
