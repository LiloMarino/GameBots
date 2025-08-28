from enum import Enum, auto


class DodgeStrategy(Enum):
    MENOR_DISTANCIA = auto()
    QUADRANTE = auto()


class Think:
    def __init__(
        self, dodge_strategy: DodgeStrategy = DodgeStrategy.MENOR_DISTANCIA
    ) -> None:
        self.set_dodge_strategy(dodge_strategy)

    def set_dodge_strategy(self, dodge_strategy: DodgeStrategy):
        self.dodge_strategy = {
            DodgeStrategy.MENOR_DISTANCIA: self._dodge_menor_distancia,
            DodgeStrategy.QUADRANTE: self._dodge_quadrante,
        }.get(dodge_strategy, self._dodge_menor_distancia)

    def _dodge_menor_distancia(self):
        pass

    def _dodge_quadrante(self):
        pass
