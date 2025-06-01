from typing import TYPE_CHECKING

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
