from notation import coords
from pieces import Piece, Side, piece_from_str
from board import Board
from state import Status

def _make_move(board: Board, origin, destination, c_place = None):
    moving = board.get(*origin)
    
    c_place = destination if c_place is None else c_place
    captured = board.get(*c_place)
    board.remove(*c_place)

    board.place(moving, *destination) 
    board.remove(*origin)
    
    return moving, captured

def _unmake_move(board: Board, moved, captured, origin, destination, c_place = None):
    board.place(moved, *origin)
    board.remove(*destination)
    
    c_place = destination if c_place is None else c_place
    board.place(captured, *c_place)
    

def legal_moves(board: Board, status: Status):
    """Filtra os pseudo-legais, testando cada lance na posição resultante."""
    result = {}
    for origin, destinations in pseudo_legal_moves(board, status.side):
        ok = []
        for dest in destinations:
            moving, captured = _make_move(board, origin, dest)

            if not is_in_check(board, status.side):
                ok.append(dest)

            _unmake_move(board, moving, captured, origin, dest)

        if ok:
            result[origin] = ok
        
    for origin, destinations in castle_moves(board, status):
        result.setdefault(origin, []).extend(destinations)
    
    for origin, destinations in get_en_passant(board, status):
        result.setdefault(origin, []).extend(destinations)    
    
    return list(result.items())
   

def pseudo_legal_moves(board: Board, side: Side):
    """Define todos os movimentos possíveis atualmente no tabuleiro"""
    valid_moves = []
    for row in range(board.SIZE):
        for col in range(board.SIZE):
            item = board.get(row, col)
            if item is None:
                continue
            piece = piece_from_str(item)
            if piece.side != side:
                continue            
            valid_moves.append(((row, col), validate_piece_moves(board, piece, row, col)))
            
    return valid_moves
            
                      
def _ray_moves(board: Board, piece: Piece, ray, *, include_empty: bool, capture_if_enemy: bool):
    """Coleta destinos válidos ao percorrer um raio da peça."""
    for r, c in ray:
        if not (0 <= r < board.SIZE and 0 <= c < board.SIZE):
            return

        item = board.get(r, c)
        if item is None:
            if include_empty:
                yield (r, c)
            continue

        if piece_from_str(item).side != piece.side and capture_if_enemy:
            yield (r, c)
        return


def validate_piece_moves(board: Board, piece: Piece, row, col):
    """Valida os movimentos da peça"""
    valid_moves = []

    for ray in piece.moves(row, col):
        valid_moves.extend(
            _ray_moves(
                board,
                piece,
                ray,
                include_empty=True,
                capture_if_enemy=piece.captures_as_it_moves,
            )
        )

    if piece.captures_as_it_moves:
        return valid_moves

    for ray in piece.attacks(row, col):
        valid_moves.extend(
            _ray_moves(
                board,
                piece,
                ray,
                include_empty=False,
                capture_if_enemy=True,
            )
        )

    return valid_moves


def _piece_attacks_square(board: Board, piece: Piece, origin_row, origin_col, target_row, target_col):
    """Verifica se uma peça ataca a casa alvo, incluindo bloqueios de raio."""
    for ray in piece.attacks(origin_row, origin_col):
        for r, c in ray:
            if not (0 <= r < board.SIZE and 0 <= c < board.SIZE):
                break
            if (r, c) == (target_row, target_col):
                return True
            if board.get(r, c) is not None:
                break
    return False


def is_square_attacked(board: Board, row, col, by_side: Side):
    """A casa (row, col) é atacada por alguma peça de by_side?"""
    for r0 in range(board.SIZE):
        for c0 in range(board.SIZE):
            item = board.get(r0, c0)
            if item is None:
                continue
            piece = piece_from_str(item)
            if piece.side != by_side:
                continue
            if _piece_attacks_square(board, piece, r0, c0, row, col):
                return True
    return False


def find_king(board: Board, side: Side):
    target = 'K' if side == Side.WHITE else 'k'
    for row in range(board.SIZE):
        for col in range(board.SIZE):
            if board.get(row, col) == target:
                return (row, col)
    return None


def is_in_check(board: Board, side: Side):
    pos = find_king(board, side)
    if pos is None:
        return False
    enemy = Side.BLACK if side == Side.WHITE else Side.WHITE
    return is_square_attacked(board, *pos, enemy)


def _can_castle_side(board: Board, status: Status, castle_char: str, rook_file: str, empty_files, path_squares):
    """Valida um lado específico do roque."""
    if castle_char not in status.castle:
        return False

    row = '1' if status.side == Side.WHITE else '8'
    rook = 'R' if status.side == Side.WHITE else 'r'
    rook_square = coords(rook_file + row)
    rook_piece = board.get(*rook_square)
    if rook_piece != rook:
        return False

    if any(board.get(*coords(file + row)) is not None for file in empty_files):
        return False

    if any(is_square_attacked(board, *coords(square + row), Side.BLACK if status.side == Side.WHITE else Side.WHITE)
           for square in path_squares):
        return False

    return True


def castle_moves(board: Board, status: Status):
    """Verifica e valida todas as opções de roque"""
    side_char = 'K' if status.side == Side.WHITE else 'k'
    row = '1' if status.side == Side.WHITE else '8'
    king_square = coords('e' + row)
    king = board.get(*king_square)

    if king != side_char:
        return []

    if is_square_attacked(board, *king_square, Side.BLACK if status.side == Side.WHITE else Side.WHITE):
        return []

    if not any(castle in status.castle for castle in (('K', 'Q') if status.side == Side.WHITE else ('k', 'q'))):
        return []

    result = []
    if _can_castle_side(board, status, 'K' if status.side == Side.WHITE else 'k', 'h', ('f', 'g'), ('f', 'g')):
        result.append((king_square, [coords('g' + row)]))

    if _can_castle_side(board, status, 'Q' if status.side == Side.WHITE else 'q', 'a', ('d', 'c', 'b'), ('d', 'c')):
        result.append((king_square, [coords('c' + row)]))

    return result
        

def _get_en_passant_target(board: Board, status: Status):
    if status.en_passant is None:
        return None

    current_row, current_col = coords(status.en_passant)
    if not (0 <= current_row < 8 and 0 <= current_col < 8):
        return None

    target_pawn = board.get(current_row, current_col)
    if target_pawn is None:
        return None

    expected_pawn = 'p' if status.side == Side.WHITE else 'P'
    if target_pawn != expected_pawn:
        return None

    if (target_pawn == 'P' and current_row != 3) or (target_pawn == 'p' and current_row != 4):
        return None

    return current_row, current_col, target_pawn


def _can_en_passant_capture(board: Board, current_row, current_col, next_col, target_pawn):
    ally_pawn = board.get(current_row, next_col)
    if ally_pawn is None or ally_pawn not in ('P', 'p'):
        return False
    if target_pawn == ally_pawn:
        return False

    target_col = current_col
    target_row = current_row + 1 if ally_pawn == 'P' else current_row - 1
    if board.get(target_row, target_col) is not None:
        return False

    pawn = piece_from_str(ally_pawn)
    return _piece_attacks_square(board, pawn, current_row, next_col, target_row, target_col)


def get_en_passant(board: Board, status: Status):
    target = _get_en_passant_target(board, status)
    if target is None:
        return []

    current_row, current_col, target_pawn = target
    result = []
    for next_col in (current_col - 1, current_col + 1):
        if not (0 <= next_col < 8):
            continue
        if not _can_en_passant_capture(board, current_row, current_col, next_col, target_pawn):
            continue

        target_row = current_row + 1 if board.get(current_row, next_col) == 'P' else current_row - 1
        target_col = current_col
        moving, captured = _make_move(board, (current_row, next_col), (target_row, target_col), (current_row, current_col))

        if not is_in_check(board, status.side):
            result.append(((current_row, next_col), [(target_row, target_col)]))

        _unmake_move(board, moving, captured, (current_row, next_col), (target_row, target_col), (current_row, current_col))

    return result