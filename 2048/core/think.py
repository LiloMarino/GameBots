import numpy as np


class Think:
    def compress(self, row):
        return [i for i in row if i != 0]

    def count_empty(self, board):
        return np.count_nonzero(board == 0)

    def merge(self, row):
        new_row = []
        skip = False
        for i in range(len(row)):
            if skip:
                skip = False
                continue
            if i + 1 < len(row) and row[i] == row[i + 1]:
                new_row.append(row[i] * 2)
                skip = True
            else:
                new_row.append(row[i])
        return new_row

    def move_left(self, board: np.ndarray) -> np.ndarray:
        new_board = []
        for row in board:
            compressed = self.compress(row)
            merged = self.merge(compressed)
            filled = merged + [0] * (4 - len(merged))
            new_board.append(filled)
        return np.array(new_board)

    def move_right(self, board: np.ndarray) -> np.ndarray:
        reversed_board = np.fliplr(board)
        moved = self.move_left(reversed_board)
        return np.fliplr(moved)

    def move_up(self, board: np.ndarray) -> np.ndarray:
        transposed = board.T
        moved = self.move_left(transposed)
        return moved.T

    def move_down(self, board: np.ndarray) -> np.ndarray:
        transposed = board.T
        moved = self.move_right(transposed)
        return moved.T

    def best_move(self, board: np.ndarray):
        moves = {
            "up": self.move_up(board),
            "down": self.move_down(board),
            "left": self.move_left(board),
            "right": self.move_right(board),
        }

        print("\nEstado atual do tabuleiro:")
        print(board)

        # Filtra os movimentos que geram mudança
        valid_moves = {}
        for move, new_board in moves.items():
            if not np.array_equal(board, new_board):
                valid_moves[move] = new_board
                print(f"\nMovimento: {move}")
                print(new_board)
            else:
                print(f"\nMovimento: {move} (inválido — sem mudança)")

        if not valid_moves:
            print("\nNenhum movimento possível. Game over.")
            return None

        # Escolhe o melhor baseado no número de espaços vazios
        best = max(valid_moves.items(), key=lambda item: self.count_empty(item[1]))
        print(f"\n>> Melhor movimento escolhido: {best[0]}")
        return best[0]
