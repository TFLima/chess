from abc import ABC, abstractmethod
from enum import Enum
from functools import lru_cache

class Side(Enum):
    WHITE = "w"
    BLACK = "b"
    
class Piece(ABC):
    side: Side
    notation: chr
    value: int | None = None
    
    captures_as_it_moves = True

    def __init__(self, side: Side):
        self.side = side
        ...
        
    @abstractmethod
    def moves(self, row, col):
        """dr = delta row, dc = delta column"""
        ...

    def attacks(self, row, col):
        """Casas que essa peça ameaça capturar. Por padrão, igual a moves()."""
        return self.moves(row, col)
    
    def _rays(self, row, col, directions, max_dist=7):
        """Uma lista por direção, das casas mais próximas para as mais distantes."""
        return [[(row + dr * d, col + dc * d) for d in range(1, max_dist + 1)]
                for dr, dc in directions]
        

class King(Piece):
    def __init__(self, side: Side):
        super().__init__(side)
        self.notation = 'K' if side == Side.WHITE else 'k'

    def moves(self, row, col):
        """Rei se move 1 casa em qualquer direção."""
        return self._rays(row, col, 
                    [(-1, -1), (-1, 0), (-1, 1),
                     ( 0, -1),          ( 0, 1),
                     ( 1, -1), ( 1, 0), ( 1, 1)], max_dist=1)          


class Queen(Piece):
    def __init__(self, side: Side):
        super().__init__(side)
        self.notation = 'Q' if side == Side.WHITE else 'q'
        self.value = 900
        
    def moves(self, row, col):
        """Rainha se move em linha reta ou diagonal, até 7 casas."""
        return self._rays(row, col, 
                    [(-1, -1), (-1, 0), (-1, 1),
                     ( 0, -1),          ( 0, 1),
                     ( 1, -1), ( 1, 0), ( 1, 1)])
    

class Rook(Piece):
    def __init__(self, side: Side):
        super().__init__(side)
        self.notation = 'R' if side == Side.WHITE else 'r'
        self.value = 500
        
    def moves(self, row, col):
        """Torre se move em linha reta, até 7 casas."""
        return self._rays(row, col, 
                    [          (-1, 0),
                     ( 0, -1),          ( 0, 1),
                               ( 1, 0),        ])       


class Bishop(Piece):
    def __init__(self, side: Side):
        super().__init__(side)
        self.notation = 'B' if side == Side.WHITE else 'b'
        self.value = 330
        
    def moves(self, row, col):
        """Bispo se move em diagonal, até 7 casas."""
        return self._rays(row, col, 
                    [(-1, -1),          (-1, 1),
                                
                     ( 1, -1),          ( 1, 1)])         


class Knight(Piece):
    def __init__(self, side: Side):
        super().__init__(side)
        self.notation = 'N' if side == Side.WHITE else 'n'
        self.value = 320
        
    def moves(self, row, col):
        """Cavalo se move uma casa em linha reta + uma na diagonal."""
        return [[(row + dr, col + dc)] for dr, dc in
            [(-2, -1), (-2, 1), (2, -1), (2, 1),
             (-1, -2), (-1, 2), (1, -2), (1, 2)]]
    

class Pawn(Piece):
    captures_as_it_moves = False 
    
    def __init__(self, side: Side):
        super().__init__(side)
        self.notation = 'P' if side == Side.WHITE else 'p'
        self.value = 100
        
    def moves(self, row, col):
        """Peão se move sempre em frente (de acordo com o lado), 1 casa, ou 2 no primeiro movimento"""
        direction = 1 if self.side == Side.WHITE else -1
        moves = [(row + direction, col)]

        initial_row = 1 if self.side == Side.WHITE else 6
        if row == initial_row:
            moves.append((row + 2 * direction, col))

        return [moves]

    def attacks(self, row, col):
        """Peão captura na diagonal, uma casa à frente."""
        direction = 1 if self.side == Side.WHITE else -1
        return [[(row + direction, col - 1)], [(row + direction, col + 1)]]
    
    
    
@lru_cache(maxsize=None)
def piece_from_str(notation):
    """Identifica a peça pela letra"""
    side = Side.WHITE if notation.isupper() else Side.BLACK
    match notation.lower():
        case 'k':
            return King(side)
        case 'q':
            return Queen(side)
        case 'r':
            return Rook(side)
        case 'b':
            return Bishop(side)
        case 'n':
            return Knight(side)
        case 'p':
            return Pawn(side)
        case _:
            raise ValueError(f"Letra de peça inválida: {notation!r}")

        