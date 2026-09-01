from board import Board
from pieces import Piece, Side, piece_from_str
from moves import validate_piece_moves, piece_attacks_square, find_king

def evaluation(board: Board):
    score = 0
    phase = _phase_value(board)
    
    score += evaluate_material(board)
    score += evaluate_position(board, phase)
    score += evaluate_mobility(board)
    
    score += (king_safety(board, Side.WHITE, phase) - king_safety(board, Side.BLACK, phase))
    
    return score

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


def evaluate_position(board: Board, phase):
    """Avalia a posição das peças de cada lado."""
    white_position = 0
    black_position = 0
    for row in range(8):
        for col in range(8):
            piece = board.get(row, col)
            if piece is None:
                continue
            piece = piece_from_str(piece)
            if piece:
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
    return min(1, phase_value / 24)  # Normaliza o valor da fase do jogo para o intervalo [0, 1]


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
        if _pawn_attacks_square(board, enemy_side, row, col):
            continue
        safe_moves.append((row, col))
    return safe_moves


def _pawn_attacks_square(board: Board, pawn_side: Side, target_row, target_col):
    row = target_row + (1 if pawn_side == Side.BLACK else -1)
    if not (1 <= row < 7):
        return False
    for offset_col in (-1, 1):
        col = target_col + offset_col
        if not (0 <= col < 8):
            continue
        piece = board.get(row, col)
        if piece is None or piece.lower() != 'p':
            continue
        pawn = piece_from_str(piece)
        if pawn and pawn.side == pawn_side:
            return True
    return False
              


def king_safety(board: Board, side: Side, phase):
    return (_pawn_shield(board, side) * phase) - _king_zone_attackers(board, side)


def _pawn_shield(board: Board, side: Side):
    """Avalia a presença de peões que protegem o rei."""
    king = find_king(board, side)
    if king is None:
        return 0  # Rei não encontrado, retorna 0

    king_row, king_col = king
    score = 0
    for col_offset in (-1, 0, 1):
        score += _pawn_shield_column(board, side, king_row, king_col, col_offset)
    return score


def _pawn_shield_column(board: Board, side: Side, king_row: int, king_col: int, col_offset: int):
    col = king_col + col_offset
    if not 0 <= col < 8:
        return 0

    pawn, row = _pawn_in_king_column(board, side, king_row, col)
    if pawn is None:
        return -20
    if pawn.side != side:
        return -10

    row_offset = _pawn_row_offset(side, king_row, row)
    return _pawn_shield_bonus(row_offset)


def _pawn_in_king_column(board: Board, side: Side, king_row: int, col: int):
    for row in _pawn_scan_rows(side):
        row_offset = _pawn_row_offset(side, king_row, row)
        if row_offset <= 0:
            continue

        piece = board.get(row, col)
        if piece is None or piece.lower() != 'p':
            continue

        pawn = piece_from_str(piece)
        if pawn is not None:
            return pawn, row

    return None, None


def _pawn_scan_rows(side: Side):
    if side == Side.WHITE:
        return range(8)
    return range(7, -1, -1)


def _pawn_row_offset(side: Side, king_row: int, row: int):
    row_offset = row - king_row
    if side == Side.BLACK:
        row_offset *= -1
    return row_offset


def _pawn_shield_bonus(row_offset: int):
    bonus = {
        1: 15,
        2: 8,
        3: 3
    }
    return bonus.get(row_offset, 0)


def _king_zone_attackers(board: Board, side: Side):
    king = find_king(board, side)
    if king is None:
        return 0  # Rei não encontrado, retorna 0

    king_row, king_col = king
    enemy_side = Side.BLACK if side == Side.WHITE else Side.WHITE
    start_row = max(0, king_row - 1)
    end_row = min(7, king_row + 1)
    start_col = max(0, king_col - 1)
    end_col = min(7, king_col + 1)
    
    return _zone_attack_weight(board, enemy_side, range(start_row, end_row + 1), range(start_col, end_col + 1))
                   
                    
def _zone_attack_weight(board: Board, attacker_side: Side, row_range, col_range):
    weight = 0
    count = 0
    count_penalty = {0: 0, 1: 0, 2: 50, 3: 75, 4: 88, 5: 94, 6: 97}
    for row in range(8):
        for col in range(8):
            piece = board.get(row, col)
            if piece is None:
                continue
            piece = piece_from_str(piece)
            if not (piece and piece.side == attacker_side):
                continue
            attacks = _piece_zone_attacks(board, piece, row, col, row_range, col_range)
            if attacks >= 1:                
                count += 1
                weight += piece.weight * attacks
                                
    return weight * count_penalty.get(count, 99) / 100

                    
def _piece_zone_attacks(board: Board, piece: Piece, piece_row, piece_col, row_range, col_range):
    count = 0
    for target_row in row_range:
        for target_col in col_range:
            if board.get(target_row, target_col) in ('K', 'k'):
                continue
            if piece_attacks_square(board, piece, piece_row, piece_col, target_row, target_col):
                count += 1
    return count              
                    
