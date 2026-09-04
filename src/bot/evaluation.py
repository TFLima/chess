from board import Board
from pieces import Piece, Side, piece_from_str
from moves import validate_piece_moves, validate_piece_attacks, find_king

# Colunas d/e: rei que não rocou não recebe bônus de escudo.
CENTER_COLUMNS = (3, 4)
# Um peão a mais de 3 fileiras de distância não protege o rei.
SHIELD_MAX_DISTANCE = 3
SHIELD_SCORE = {1: 12, 2: 6, 3: 4}
STORM_PENALTY = {1: 10, 2: 6, 3: 3}


def evaluation(board: Board):
    score = 0
    phase, attackers, pawn_attacks = _precompute(board)

    score += evaluate_material(board)
    score += evaluate_position(board, phase)
    score += evaluate_mobility(board, pawn_attacks)

    score += (king_safety(board, Side.WHITE, phase, attackers) 
            - king_safety(board, Side.BLACK, phase, attackers))

    return score


def _precompute(board: Board):
    phase_value = 0
    attackers = {Side.WHITE: {}, Side.BLACK: {}}
    pawn_attacks = {Side.WHITE: set(), Side.BLACK: set()}
    for row in range(8):
        for col in range(8):
            piece = _piece_at(board, row, col)
            if piece is None:
                continue
            phase_value += piece.phase or 0
            _record_attacks(board, piece, row, col, attackers, pawn_attacks)
    
    phase_value = min(1, phase_value / 24) # Normaliza o valor da fase do jogo para o intervalo [0, 1]            
    return phase_value, attackers, pawn_attacks  


def _piece_at(board: Board, row: int, col: int):
    value = board.get(row, col)
    return piece_from_str(value) if value is not None else None


def _record_attacks(board, piece, row, col, attackers, pawn_attacks):
    attacks = validate_piece_attacks(board, piece, row, col, True, xray=True)
    if not attacks:
        return

    by_square = attackers[piece.side]
    for square in attacks:
        by_square.setdefault(square, []).append((row, col))

    if piece.notation.lower() == 'p':
        pawn_attacks[piece.side].update(attacks)
    

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
    return (
        (_king_column_score(board, side) * phase)
      - (_king_zone_attackers(board, side, attacks_map) * phase)
    )


def _king_column_score(board: Board, side: Side):
    """Avalia a presença de peões que protegem o rei."""
    king = find_king(board, side)
    if king is None:
        return 0  # Rei não encontrado, retorna 0

    king_row, king_col = king
    if king_col in CENTER_COLUMNS:
        return 0  # Rei sem roque no centro não tem escudo a avaliar

    # Rei na borda: desloca o centro do escudo para ainda olhar 3 colunas.
    shield_col = min(max(king_col, 1), 6)
    score = 0
    for col in (shield_col - 1, shield_col, shield_col + 1):
        score += _pawn_shield_column(board, side, king_row, king_col, col)
    return score


def _pawn_shield_column(board: Board, side: Side, king_row: int, king_col: int, col: int):
    """Combina o escudo de peões próprios e o avanço de peões inimigos numa coluna."""
    col_weight = 1.3 if col == king_col else 1.0
    ally_pawn, enemy_pawn = _shield_pawns(board, side, king_row, col)

    if ally_pawn is None:
        # Sem peão próprio: coluna aberta é pior que semiaberta (torre/dama inimiga).
        shield = -18 if enemy_pawn is None else -10
    else:
        shield = SHIELD_SCORE[ally_pawn] * col_weight

    # Peão inimigo avançando na coluna. Se o peão aliado está na frente dele,
    # o avanço está travado e a ameaça vale menos.
    storm = 0
    if enemy_pawn is not None:
        blocked = ally_pawn is not None and ally_pawn < enemy_pawn
        storm = -STORM_PENALTY[enemy_pawn] * (0.5 if blocked else 1.0)
    return shield + storm


def _shield_pawns(board: Board, side: Side, king_row: int, col: int):
    """Retorna a distância do peão próprio e do peão inimigo mais próximos do rei na coluna."""
    row_offset = 1 if side == Side.WHITE else -1
    ally_pawn = None
    enemy_pawn = None
    for distance in range(1, SHIELD_MAX_DISTANCE + 1):
        row = king_row + row_offset * distance
        if not 0 <= row < 8:
            break  # Saiu do tabuleiro: as distâncias seguintes também saem
        pawn_side = _shield_pawn_side(board, row, col)
        if pawn_side is None:
            continue
        if pawn_side == side:
            if ally_pawn is None:
                ally_pawn = distance
        elif enemy_pawn is None:
            enemy_pawn = distance
        if ally_pawn is not None and enemy_pawn is not None:
            break
    return ally_pawn, enemy_pawn


def _shield_pawn_side(board: Board, row: int, col: int):
    piece = _piece_at(board, row, col)
    if piece is None or piece.notation.lower() != 'p':
        return None
    return piece.side


def _king_zone_attackers(board: Board, side: Side, attackers):
    king = find_king(board, side)
    if king is None:
        return 0  # Rei não encontrado, retorna 0
    king_row, king_col = king
    center_row = min(max(king_row, 1), 6)
    center_col = min(max(king_col, 1), 6)
    enemy_side = Side.BLACK if side == Side.WHITE else Side.WHITE
    zone = {
        (row, col)
        for row in range(max(0, center_row -1), min(7, center_row + 1) + 1)
        for col in range(max(0, center_col -1), min(7, center_col + 1) + 1)
    }
    
    return _zone_attack_weight(board, side, attackers[enemy_side], zone)
                   
                    
def _zone_attack_weight(board: Board, side: Side, attackers_by_square, zone):
    count_penalty = {0: 0, 1: 0, 2: 50, 3: 75, 4: 88, 5: 94, 6: 97}
    
    zone_attacks = {}
    zone_weakness = 0
    for square in zone:
        # Só peça própria abriga o rei; peça inimiga na zona não é proteção.
        defender = _piece_at(board, *square)
        shelters = (defender is not None
                    and defender.side == side
                    and defender.notation not in ('K', 'k'))  # O rei não abriga a si mesmo
        zone_weakness += 0.5 if shelters else 1.0
        for origin in attackers_by_square.get(square, ()):
            if board.get(*origin) in ('K', 'k', 'P', 'p'):
                continue  # Rei (peso 0) e peão (peso 1) não devem inflar a contagem
            zone_attacks[origin] = zone_attacks.get(origin, 0) + 1
            
    weight = 0
    for origin, squares in zone_attacks.items():
        attacker = piece_from_str(board.get(*origin))        
        weight += attacker.weight * squares
                                
    return weight * (zone_weakness / len(zone)) * count_penalty.get(len(zone_attacks), 99) / 100            
                    
