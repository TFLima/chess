from notation import coords
from pieces import Piece, Side, piece_from_str
from board import Board
from state import Status

def legal_moves(board: Board, status: Status):
    """Filtra os pseudo-legais, testando cada lance na posição resultante."""
    result = {}
    for origin, destinations in pseudo_legal_moves(board, status.side):
        ok = []
        for dest in destinations:
            moving = board.get(*origin)
            captured = board.get(*dest)

            board.place(moving, *dest)      # make
            board.place(None, *origin)

            if not is_in_check(board, status.side):
                ok.append(dest)               
            
            board.place(moving, *origin)    # unmake
            board.place(captured, *dest)

        if ok:
            result[origin] = ok
        
    for origin, destinations in castle_moves(board, status):
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


def castle_moves(board: Board, status: Status):
    """Verifica e valida todas as opções de roque"""
    k_castle = 'K' if status.side == Side.WHITE else 'k'
    q_castle = 'Q' if status.side == Side.WHITE else 'q'
    rook = 'R' if status.side == Side.WHITE else 'r'
    row = '1' if status.side == Side.WHITE else '8'
    
    if not (k_castle in status.castle or q_castle in status.castle):
        return []
    king = board.get(*coords('e'+row))        
    k_rook = board.get(*coords('h'+row)) if k_castle in status.castle else None
    q_rook = board.get(*coords('a'+row)) if q_castle in status.castle else None
        
    if king is None:
        return []
    if k_rook is None and q_rook is None:
        return []
    
    enemy = Side.BLACK if status.side == Side.WHITE else Side.WHITE
    if king != k_castle or is_square_attacked(board, *coords('e'+row), enemy):
        return []
    
    result = []
    if k_rook == rook:
        if board.get(*coords('f'+row)) is None and board.get(*coords('g'+row)) is None:            
            if not(is_square_attacked(board, *coords('f'+row), enemy) or is_square_attacked(board, *coords('g'+row), enemy)):
                result.append((coords('e'+row), [coords('g'+row)]))
    if q_rook == rook:
        if board.get(*coords('d'+row)) is None and board.get(*coords('c'+row)) is None and board.get(*coords('b'+row)) is None:
            if not(is_square_attacked(board, *coords('d'+row), enemy) or is_square_attacked(board, *coords('c'+row), enemy)):
                result.append((coords('e'+row), [coords('c'+row)]))
            
    return result
        
    
    
        