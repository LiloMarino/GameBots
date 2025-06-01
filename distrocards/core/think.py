import random
from typing import TYPE_CHECKING, Iterator

from logger_config import logger

if TYPE_CHECKING:
    import numpy as np
    from core.sensor import Card


class Think:
    def __init__(self) -> None:
        self.cards: dict[Card, None | np.ndarray] = {}

    def set_cards(self, cards: list[Card]) -> None:
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

    def is_pair(self, card1: Card, card2: Card) -> bool:
        pass

    @property
    def discovered_cards(self) -> Iterator[Card]:
        return (card for card, img in self.cards.items() if img is not None)

    @property
    def undiscovered_cards(self) -> Iterator[Card]:
        return (card for card, img in self.cards.items() if img is None)
