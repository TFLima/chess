from board import Board
from pieces import Piece, Side, piece_from_str
from moves import validate_piece_moves, is_square_attacked, find_king

def evaluate_material(board: Board):
    """Avalia o material das peças do lado especificado."""
    white_material = 0
    black_material = 0
    for row in range(8):
        for col in range(8):
            piece = board.get(row, col)
            if piece is None:
                continue
            piece = piece_from_str(piece)
            if piece and piece.value is not None:
                if piece.side == Side.WHITE:
                    white_material += piece.value
                else:
                    black_material += piece.value
    return white_material - black_material


def evaluate_position(board: Board):
    """Avalia a posição das peças do lado especificado."""
    white_position = 0
    black_position = 0
    phase = _phase_value(board)
    for row in range(8):
        for col in range(8):
            piece = board.get(row, col)
            if piece is None:
                continue
            piece = piece_from_str(piece)
            if piece and piece.square_table is not None:
                if piece.side == Side.WHITE:
                    white_position += piece.pst_value(row, col, phase)
                else:
                    black_position += piece.pst_value(row, col, phase)
    return white_position - black_position


def _phase_value(board: Board):
    """Calcula o valor da fase do jogo com base nas peças restantes no tabuleiro."""
    phase_value = 0
    for row in range(8):
        for col in range(8):
            piece = board.get(row, col)
            if piece is None:
                continue
            piece = piece_from_str(piece)
            if piece and piece.phase is not None:
                phase_value += piece.phase
    return phase_value / 24  # Normaliza o valor da fase do jogo para o intervalo [0, 1]


def evaluate_mobility(board: Board):
    """Avalia a mobilidade das peças do lado especificado."""
    mobility_score = 0
    for row in range(8):
        for col in range(8):
            piece = board.get(row, col)
            if piece is None:
                continue
            piece = piece_from_str(piece)
            if piece: 
                moves = validate_piece_moves(board, piece, row, col)
                moves = _safe_moves(moves, board, piece.side)
                if piece.side == Side.WHITE:
                    mobility_score += len(moves) * piece.mobility
                else:
                    mobility_score -= len(moves) * piece.mobility 
    return mobility_score


def _safe_moves(moves, board: Board, side: Side):
    safe_moves = []
    enemy_side = Side.BLACK if side == Side.WHITE else Side.WHITE
    for row, col in moves:
        if is_square_attacked(board, row, col, enemy_side):
            continue
        safe_moves.append((row, col))
    return safe_moves


def _pawn_shield(board: Board, side: Side):
    """Avalia a presença de peões que protegem o rei."""
    score = 0
    bonus = {
        1: 15,
        2: 8,
        3: 3
    }
    king_row, king_col = find_king(board, side)
    if king_row is None or king_col is None:
        return score  # Rei não encontrado, retorna 0

    # Verifica as colunas adjacentes ao rei para encontrar peões
    for col_offset in [-1, 0, 1]:
        col = king_col + col_offset
        if 0 <= col < 8:
            for row in range(8):
                row_offset = row - king_row
                row_offset = row_offset if side == Side.WHITE else -1 * row_offset
                if row_offset <= 0:
                    continue  # Apenas verifica peões à frente do rei
                piece = board.get(row, col)
                if piece is not None and piece.lower() == 'p':
                    pawn = piece_from_str(piece)
                    if pawn and pawn.side == side:
                        score += bonus.get(row_offset, 0)  # Aumenta a pontuação para cada peão que protege o rei de acordo com a distância
                        break  # Apenas um peão por coluna é contado
                    if pawn and pawn.side != side:
                        score -= 10 # Penaliza coluna semiaberta (só tem peão inimigo) que expõe o rei
                        break 
            score -= 20 # Penaliza a coluna aberta (sem peões) que protege o rei
    return score