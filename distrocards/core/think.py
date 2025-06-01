from typing import TYPE_CHECKING, Iterator

from logger_config import logger

if TYPE_CHECKING:
    from core.sensor import Card


class Think:
    def __init__(self) -> None:
        self.cards: dict[Card, None] = {}

    def set_cards(self, cards: list[Card]) -> None:
        if len(cards) % 2 != 0:
            logger.error("Quantidade de cartas ímpar detectadas")
            raise Exception("Quantidade de cartas ímpar detectadas")

        self.cards = {card: None for card in cards}

    def left_cards(self) -> int:
        return len(self.cards)

    def random_undiscovered(self) -> Card:
        pass

    def get_pair(self, card: Card) -> Card | None:
        pass

    def get_discovered_pair(self) -> tuple(Card, Card) | None:
        pass

    @property
    def discovered_cards(self) -> Iterator[Card]:
        return (card for card, img in self.cards.items() if img is not None)

    @property
    def undiscovered_cards(self) -> Iterator[Card]:
        return (card for card, img in self.cards.items() if img is None)
