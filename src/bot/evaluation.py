from board import Board
from pieces import Piece, Side, piece_from_str
from moves import validate_piece_moves, validate_piece_attacks, piece_attacks_square, find_king

def evaluation(board: Board):
    score = 0
    phase, attackers, pawn_attacks = _precompute(board)

    score += evaluate_material(board)
    score += evaluate_position(board, phase)
    score += evaluate_mobility(board, pawn_attacks)

    score += (king_safety(board, Side.WHITE, phase, attackers) - king_safety(board, Side.BLACK, phase, attackers))

    return score


def _precompute(board: Board):
    phase_value = 0
    attackers = {Side.WHITE: {}, Side.BLACK: {}}
    pawn_attacks_map = {Side.WHITE: set(), Side.BLACK: set()}
    for row in range(8):
        for col in range(8):
            piece = _piece_at(board, row, col)
            if piece is None:
                continue
            phase_value += piece.phase or 0
            _record_attacks(board, piece, row, col, attackers, pawn_attacks_map)
                
    return min(1, phase_value / 24), attackers, pawn_attacks_map  # Normaliza o valor da fase do jogo para o intervalo [0, 1]


def _piece_at(board: Board, row: int, col: int):
    value = board.get(row, col)
    return piece_from_str(value) if value is not None else None


def _record_attacks(board, piece, row, col, attackers, pawn_attacks_map):
    attacks = validate_piece_attacks(board, piece, row, col, True)
    if not attacks:
        return

    by_square = attackers[piece.side]
    for square in attacks:
        by_square.setdefault(square, []).append((row, col))

    if piece.notation.lower() == 'p':
        pawn_attacks_map[piece.side].update(attacks)
    

def evaluate_material(board: Board):
    """Avalia o material das peças do lado especificado."""
    white_material = 0
    black_material = 0
    for row in range(8):
        for col in range(8):
            piece = _piece_at(board, row, col)
            if piece is None:
                continue
            if piece.value is not None:
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
            piece = _piece_at(board, row, col)
            if piece is None:
                continue
            if piece.side == Side.WHITE:
                white_position += piece.pst_value(row, col, phase)
            else:
                black_position += piece.pst_value(row, col, phase)
    return white_position - black_position


def evaluate_mobility(board: Board, attacks):
    """Avalia a mobilidade das peças do lado especificado."""
    mobility_score = 0
    for row in range(8):
        for col in range(8):
            piece = _piece_at(board, row, col)
            if piece is None:
                continue
            moves = validate_piece_moves(board, piece, row, col)                
            moves = _safe_moves(moves, piece.side, attacks)
            if piece.side == Side.WHITE:
                mobility_score += len(moves) * piece.mobility
            else:
                mobility_score -= len(moves) * piece.mobility 
    return mobility_score              

def _safe_moves(moves, side: Side, pawn_attacks):
    unsafe_moves = pawn_attacks[Side.BLACK if side == Side.WHITE else Side.WHITE]
    return [move for move in moves if move not in unsafe_moves]
    
    
def king_safety(board: Board, side: Side, phase, attacks_map):
    return (_pawn_shield(board, side) * phase) - _king_zone_attackers(board, side, attacks_map)


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

        piece = _piece_at(board, row, col)
        if piece is None:
            continue
        pawn = piece if piece.notation.lower() == 'p' else None
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


def _king_zone_attackers(board: Board, side: Side, attackers):
    king = find_king(board, side)
    if king is None:
        return 0  # Rei não encontrado, retorna 0

    king_row, king_col = king
    enemy_side = Side.BLACK if side == Side.WHITE else Side.WHITE
    zone = {
        (row, col)
        for row in range(max(0, king_row -1), min(7, king_row + 1) + 1)
        for col in range(max(0, king_col -1), min(7, king_col + 1) + 1)
        if board.get(row, col) not in ('K', 'k')
    }
    
    return _zone_attack_weight(board, attackers[enemy_side], zone)
                   
                    
def _zone_attack_weight(board: Board, attackers_by_square, zone):
    count_penalty = {0: 0, 1: 0, 2: 50, 3: 75, 4: 88, 5: 94, 6: 97}
    
    zone_attacks = {}
    for square in zone:
        for origin in attackers_by_square.get(square, ()):
            zone_attacks[origin] = zone_attacks.get(origin, 0) + 1
            
    weight = 0
    for origin, squares in zone_attacks.items():
        piece = piece_from_str(board.get(*origin))
        weight += piece.weight * squares
                                
    return weight * count_penalty.get(len(zone_attacks), 99) / 100            
                    
