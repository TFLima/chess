class Board:
    """Guarda o estado físico do tabuleiro. Não sabe nada de regras de xadrez."""

    SIZE = 8

    def __init__(self):
        self.grid = [[None for _ in range(self.SIZE)] for _ in range(self.SIZE)]

    def _check_bounds(self, row, col):
        if not (0 <= row < self.SIZE and 0 <= col < self.SIZE):
            raise ValueError(f"Posição fora do tabuleiro: ({row}, {col})")
        
    def place(self, piece, row, col):
        self._check_bounds(row, col)
        self.grid[row][col] = piece

    def remove(self, row, col):
        self._check_bounds(row, col)
        piece = self.grid[row][col]
        self.grid[row][col] = None
        return piece

    def get(self, row, col):
        self._check_bounds(row, col)
        return self.grid[row][col]

    def __repr__(self):
        linhas = []
        for row in range(self.SIZE - 1, -1, -1):
            casas = []
            for col in range(self.SIZE):
                piece = self.grid[row][col]
                casas.append(str(piece) if piece is not None else ".")
            linhas.append(f"{row + 1} " + " ".join(casas))
        linhas.append("  " + " ".join("abcdefgh"))
        return "\n".join(linhas)


if __name__ == "__main__":
    from notation import coords

    board = Board()
    #Pretas
    board.place("r", *coords("a8"))
    board.place("n", *coords("b8"))
    board.place("b", *coords("c8"))
    board.place("q", *coords("d8"))
    board.place("k", *coords("e8"))
    board.place("b", *coords("f8"))
    board.place("n", *coords("g8"))
    board.place("r", *coords("h8"))
    board.place("p", *coords("a7"))
    board.place("p", *coords("b7"))
    board.place("p", *coords("c7"))
    board.place("p", *coords("d7"))
    board.place("p", *coords("e7"))
    board.place("p", *coords("f7"))
    board.place("p", *coords("g7"))
    board.place("p", *coords("h7"))
    #Brancas
    board.place("R", *coords("a1"))
    board.place("N", *coords("b1"))
    board.place("B", *coords("c1"))
    board.place("Q", *coords("d1"))
    board.place("K", *coords("e1"))
    board.place("B", *coords("f1"))
    board.place("N", *coords("g1"))
    board.place("R", *coords("h1"))
    board.place("P", *coords("a2"))
    board.place("P", *coords("b2"))
    board.place("P", *coords("c2"))
    board.place("P", *coords("d2"))
    board.place("P", *coords("e2"))
    board.place("P", *coords("f2"))
    board.place("P", *coords("g2"))
    board.place("P", *coords("h2"))
    print(board)
