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
