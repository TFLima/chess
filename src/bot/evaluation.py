"""
Falta implementar: rook_activity, bishop_pair, outposts, early_queen, time_waste, late_development 
(esses 3 últimos precisam de histórico)
"""
from board import Board
from pieces import Side, piece_from_str
from moves import validate_piece_moves, validate_piece_attacks, find_king

# Colunas d/e: rei que não rocou não recebe bônus de escudo.
CENTER_COLUMNS = (3, 4)
# Um peão a mais de 3 fileiras de distância não protege o rei.
SHIELD_MAX_DISTANCE = 3
SHIELD_SCORE = {1: 12, 2: 6, 3: 4}
STORM_PENALTY = {1: 10, 2: 6, 3: 3}
PASSED_BONUS = {1: 0, 2: 10, 3: 15, 4: 25, 5: 40, 6: 70}
ISLAND_PENALTY = {1: 0, 2: 3, 3: 6, 4: 9}
ISLAND_WEIGHT = (1.0, 2.0)    # fragmentar a estrutura dói mais no final
DOUBLED_PENALTY = (10, 22)    # (meio-jogo, final)
ISOLATED_PENALTY = (5, 14)
BACKWARD_PENALTY = (8, 14)
PASSED_WEIGHT = (0.4, 1.0)    # o passado nunca zera no meio-jogo
# Bônus de peões conectados, por fileira do peão (base 0).
CONNECTED_BONUS = {1: 3, 2: 4, 3: 6, 4: 11, 5: 20, 6: 35}
CONNECTED_WEIGHT = (0.5, 1.0) # peões conectados decidem finais
DEFENDED_EXTRA = (4, 6)       # somado ao bônus de falange, não substituto



def evaluation(board: Board):
    score = 0
    phase, attackers, pawn_attacks, pawn_columns = _precompute(board)

    score += evaluate_material(board)
    score += evaluate_position(board, phase)
    score += evaluate_mobility(board, pawn_attacks)

    score += (king_safety(board, Side.WHITE, attackers, phase) 
            - king_safety(board, Side.BLACK, attackers, phase))   
    
    score += (pawn_structure(Side.WHITE, pawn_columns, phase) 
            - pawn_structure(Side.BLACK, pawn_columns, phase))   

    return score


def _precompute(board: Board):
    phase_value = 0
    attackers = {Side.WHITE: {}, Side.BLACK: {}}
    pawn_attacks = {Side.WHITE: set(), Side.BLACK: set()}
    pawn_columns = {Side.WHITE: {}, Side.BLACK: {}}
    for row in range(8):
        for col in range(8):
            piece = _piece_at(board, row, col)
            if piece is None:
                continue
            phase_value += piece.phase or 0
            if piece.notation.lower() == 'p':
                pawn_columns[piece.side].setdefault(col, []).append(row) # Agrupa os peões por coluna
            _record_attacks(board, piece, row, col, attackers, pawn_attacks)
    
    phase_value = min(1, phase_value / 24) # Normaliza o valor da fase do jogo para o intervalo [0, 1]            
    return phase_value, attackers, pawn_attacks, pawn_columns 


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
    
    
def king_safety(board: Board, side: Side, attacks_map, phase):
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
                    
def pawn_structure(side: Side, pawn_columns: dict[Side, dict[int, list[int]]], phase: float):
    enemy_side = Side.BLACK if side == Side.WHITE else Side.WHITE
    ally_pawns = pawn_columns[side]
    enemy_pawns = pawn_columns[enemy_side]
    direction = 1 if side == Side.WHITE else -1
    
    score = 0
    for col, rows in ally_pawns.items():
        score -= (len(rows) - 1) * _taper(*DOUBLED_PENALTY, phase) # Penaliza peões dobrados
        if col-1 not in ally_pawns and col+1 not in ally_pawns:
            score -= len(rows) * _taper(*ISOLATED_PENALTY, phase)  # Penaliza peões isolados
        passed = _pawn_passed(col, rows, enemy_pawns, direction)
        if passed is not None:            
            score += _rank_bonus(PASSED_BONUS, passed, direction) * _taper(*PASSED_WEIGHT, phase) # Premia peões passados conforme avanço
        for row in rows:
            score += _connected_pawn(row, col, ally_pawns, direction, phase)
            score -= _backward_pawn(row, col, ally_pawns, enemy_pawns, direction, phase)

    islands = sum(1 for col in range(8) if col in ally_pawns and col - 1 not in ally_pawns) # Conta as ilhas de peões

    return score - ISLAND_PENALTY.get(min(islands, 4), 0) * _taper(*ISLAND_WEIGHT, phase)

def _taper(mg, eg, phase):
    """Interpola entre o peso de meio-jogo e o de final (phase: 1 = meio-jogo, 0 = final)."""
    return mg * phase + eg * (1-phase)

def _rank_bonus(table, row, dir):
    """Lê a tabela pela fileira do peão, espelhando as fileiras para as pretas."""
    return table[row if dir == 1 else 7 - row]
            
def _pawn_passed(col, rows, enemy_pawns: dict[int, list[int]], dir: int):
    leading_pawn = _leading_pawn(rows, dir)
    if col not in enemy_pawns and col-1 not in enemy_pawns and col+1 not in enemy_pawns:
        return leading_pawn
    if col in enemy_pawns and _leading_pawn(enemy_pawns.get(col), dir) * dir > leading_pawn * dir:
        return None
    if col-1 in enemy_pawns and _leading_pawn(enemy_pawns.get(col-1), dir) * dir > leading_pawn * dir:
        return None
    if col+1 in enemy_pawns and _leading_pawn(enemy_pawns.get(col+1), dir) * dir > leading_pawn * dir:
        return None    
    return leading_pawn
    
def _leading_pawn(rows, direction):
    return max(rows) if direction == 1 else min(rows)

def _connected_pawn(row, col, ally_pawns, dir, phase):
    """Falange e defesa são vantagens independentes e somam."""
    neighbours = [ally_pawns[adjacent_col]
                  for adjacent_col in (col-1, col+1) if adjacent_col in ally_pawns]

    bonus = 0
    if any(row in rows for rows in neighbours):
        bonus += _rank_bonus(CONNECTED_BONUS, row, dir) * _taper(*CONNECTED_WEIGHT, phase) # Peão em falange
    if any(row-dir in rows for rows in neighbours):
        bonus += _taper(*DEFENDED_EXTRA, phase) # Peão defendido por outro aliado
    return bonus

def _backward_pawn(row, col, ally_pawns, enemy_pawns, dir, phase):
    distance = 8
    is_guarded = False
    is_blocked = False if col not in enemy_pawns else row+dir in enemy_pawns.get(col)
    
    for adjacent_col in (col-1, col+1):
        if adjacent_col in enemy_pawns and row+dir*2 in enemy_pawns.get(adjacent_col):
            is_guarded = True            
        if adjacent_col in ally_pawns:
            nearest_pawn = _leading_pawn(ally_pawns.get(adjacent_col), -dir)
            distance = min(distance, (nearest_pawn * dir) - (row * dir))
       
    if 1 <= distance < 8 and (is_blocked or is_guarded):
        return _taper(*BACKWARD_PENALTY, phase) # Penalidade por atraso de peão
    return 0

def rook_activity(board: Board, piece_map: set):
    score = 0
    white_rooks = {rows: {}, cols: {}}
    black_rooks = {rows: {}, cols: {}}
    for square, piece in piece_map.items():
        if piece not in ('R','r'):
            continue
        row, col = square
        # restante do código aqui
        if piece == 'R':
           white_rooks[rows].setdefault(row, []).extend(col)
           white_rooks[cols].setdefault(col, []).extend(row)
        else:
           # mesma coisa para as pretas

    score += _connected_rooks(white_rooks, 'R')
    score -= _connected_rooks(black_rooks, 'r')
    return score


def _connected_rooks(board, rooks, _not):
    row_score = 0
    col_score = 0
    for row, cols in rooks[rows].items():
        if len(cols) <= 1:
            continue 
        for col in range(min(cols)+1, max(cols)):
            value = board.get(row, col)
            if value is None:
                continue
            if value == _not:
                row_score += 1
            break

    # mesma coisa para as colunas
    return row_score + col_score



    