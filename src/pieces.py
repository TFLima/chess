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
        
    def pst_value(self, row, col, phase=None):
        """Retorna o valor da peça na posição (row, col) de acordo com a tabela de valores."""
        if not self.square_table:
            return 0
        # Se for peça preta, inverte o row
        row = 7 - row if self.side == Side.BLACK else row        
        return self.square_table[row][col]

class King(Piece):
    def __init__(self, side: Side):
        super().__init__(side)
        self.notation = 'K' if side == Side.WHITE else 'k'
        self.midgame_square_table = [
                                        [-30,-40,-40,-50,-50,-40,-40,-30],
                                        [-30,-40,-40,-50,-50,-40,-40,-30],
                                        [-30,-40,-40,-50,-50,-40,-40,-30],
                                        [-30,-40,-40,-50,-50,-40,-40,-30],
                                        [-20,-30,-30,-40,-40,-30,-30,-20],
                                        [-10,-20,-20,-20,-20,-20,-20,-10],
                                        [ 20, 20,  0,  0,  0,  0, 20, 20],  # Linha 2 (Roque seguro)
                                        [ 20, 30, 10,  0,  0, 10, 30, 20]   # Linha 1 (G, C e B são ótimas casas)
                                    ]
        self.endgame_square_table = [
                                        [-50,-40,-30,-30,-30,-30,-40,-50],
                                        [-30,-20,-10,  0,  0,-10,-20,-30],
                                        [-30,-10, 20, 30, 30, 20,-10,-30],
                                        [-30,-10, 30, 40, 40, 30,-10,-30],  # Centro muito valorizado
                                        [-30,-10, 30, 40, 40, 30,-10,-30],
                                        [-30,-10, 20, 30, 30, 20,-10,-30],
                                        [-30,-30,  0,  0,  0,  0,-30,-30],
                                        [-50,-30,-30,-30,-30,-30,-30,-50]
                                    ]


    def moves(self, row, col):
        """Rei se move 1 casa em qualquer direção."""
        return self._rays(row, col, 
                    [(-1, -1), (-1, 0), (-1, 1),
                     ( 0, -1),          ( 0, 1),
                     ( 1, -1), ( 1, 0), ( 1, 1)], max_dist=1)          

    def pst_value(self, row, col, phase=None):
        """Retorna o valor da peça na posição (row, col) de acordo com a tabela de valores."""        
        phase = 1 if phase is None else phase
        row = 7 - row if self.side == Side.BLACK else row
        mg_score = self.midgame_square_table[row][col]
        eg_score = self.endgame_square_table[row][col]
        return mg_score * phase + eg_score * (1 - phase)


class Queen(Piece):
    def __init__(self, side: Side):
        super().__init__(side)
        self.notation = 'Q' if side == Side.WHITE else 'q'
        self.value = 900
        self.square_table = [
                                [-20,-10,-10, -5, -5,-10,-10,-20],
                                [-10,  0,  0,  0,  0,  0,  0,-10],
                                [-10,  0,  5,  5,  5,  5,  0,-10],
                                [ -5,  0,  5,  5,  5,  5,  0, -5],
                                [  0,  0,  5,  5,  5,  5,  0,  0],
                                [-10,  5,  5,  5,  5,  5,  0,-10],
                                [-10,  0,  5,  0,  0,  0,  0,-10],
                                [-20,-10,-10, -5, -5,-10,-10,-20]
                            ]

        
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
        self.square_table = [
                                [ 0,  0,  0,  5,  5,  0,  0,  0],
                                [ 5, 10, 10, 10, 10, 10, 10,  5],  # Linha 7 (Excelente para Torres)
                                [-5,  0,  0,  0,  0,  0,  0, -5],
                                [-5,  0,  0,  0,  0,  0,  0, -5],
                                [-5,  0,  0,  0,  0,  0,  0, -5],
                                [-5,  0,  0,  0,  0,  0,  0, -5],
                                [-5,  0,  0,  0,  0,  0,  0, -5],
                                [ 0,  0,  0,  5,  5,  0,  0,  0]   # Linha 1 (Bons pontos no centro)
                            ]

        
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
        self.square_table = [
                                [-20,-10,-10,-10,-10,-10,-10,-20],
                                [-10,  0,  0,  0,  0,  0,  0,-10],
                                [-10,  0,  5, 10, 10,  5,  0,-10],
                                [-10,  5,  5, 10, 10,  5,  5,-10],
                                [-10,  0, 10, 10, 10, 10,  0,-10],
                                [-10, 10, 10, 10, 10, 10, 10,-10],
                                [-10,  5,  0,  0,  0,  0,  5,-10],
                                [-20,-10,-10,-10,-10,-10,-10,-20]
                            ]

        
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
        self.square_table = [
                                [-50,-40,-30,-30,-30,-30,-40,-50],
                                [-40,-20,  0,  0,  0,  0,-20,-40],
                                [-30,  0, 10, 15, 15, 10,  0,-30],
                                [-30,  5, 15, 20, 20, 15,  5,-30],
                                [-30,  0, 15, 20, 20, 15,  0,-30],
                                [-30,  5, 10, 15, 15, 10,  5,-30],
                                [-40,-20,  0,  5,  5,  0,-20,-40],
                                [-50,-40,-30,-30,-30,-30,-40,-50]
                            ]

        
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
        self.square_table = [
                                [  0,  0,  0,  0,  0,  0,  0,  0],  # Linha 8: Promoção (0, pois vira Dama/outra peça)
                                [ 50, 50, 50, 50, 50, 50, 50, 50],  # Linha 7: A um passo da promoção (Bônus Máximo!)
                                [ 10, 10, 20, 30, 30, 20, 10, 10],  # Linha 6: Avançado e muito perigoso
                                [  5,  5, 10, 25, 25, 10,  5,  5],  # Linha 5: Invasão e controle de espaço
                                [  0,  0,  0, 20, 20,  0,  0,  0],  # Linha 4: Bom controle central
                                [  5, -5,-10,  0,  0,-10, -5,  5],  # Linha 3: Peões centrais atrasados são ruins
                                [  5, 10, 10,-20,-20, 10, 10,  5],  # Linha 2: Posição inicial (protegendo o rei nas alas)
                                [  0,  0,  0,  0,  0,  0,  0,  0]   # Linha 1: Impossível ter peão aqui
                            ]

        
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

        