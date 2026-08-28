from state import Status
from pieces import Side

def coords(algebraic):
    """Converte notação algébrica (ex: 'e2') para (row, col) 0-indexado."""
    if not isinstance(algebraic, str) or len(algebraic) != 2:
        raise ValueError(f"Posição inválida: {algebraic!r}")

    file, rank = algebraic[0].lower(), algebraic[1]
    if not ("a" <= file <= "h" and "1" <= rank <= "8"):
        raise ValueError(f"Posição inválida: {algebraic!r}")

    row = int(rank) - 1
    col = ord(file) - ord("a")
    return row, col

def square(row, col):
    """Converte coordenadas para notação algébrica das casas"""
    if not (0 <= col < 8 and 0 <= row < 8):
        raise ValueError("Posição inválida")
       
    match col:
        case 0: return f"a{row + 1}"
        case 1: return f"b{row + 1}"
        case 2: return f"c{row + 1}"
        case 3: return f"d{row + 1}"
        case 4: return f"e{row + 1}"
        case 5: return f"f{row + 1}"
        case 6: return f"g{row + 1}"
        case 7: return f"h{row + 1}"
        case _:
            raise ValueError('Posição inválida')
        
def generate_fen(grid, status: Status):
    def serialize_rank(rank):
        empty = 0
        rank_fen = []

        for piece in rank:
            if piece is None:
                empty += 1
                continue

            if empty:
                rank_fen.append(str(empty))
                empty = 0
            rank_fen.append(piece)

        if empty:
            rank_fen.append(str(empty))

        return "".join(rank_fen)

    rows = [serialize_rank(grid[row]) for row in range(7, -1, -1)]
    fen = "/".join(rows)
    side = "w" if status.side == Side.WHITE else "b"
    castle = status.castle if status.castle else "-"
    ep_target = status.ep_target if status.ep_target is not None else "-"
    half_moves = str(status.half_moves)

    return f"{fen} {side} {castle} {ep_target} {half_moves} {status.move}"


def parse_fen(fen: str):
    """Converte um FEN em (grid 8x8, Status). Inverso de generate_fen()."""
    parts = fen.split()
    if len(parts) < 4:
        raise ValueError(f"FEN incompleto: {fen!r}")

    placement, side_char, castle, ep = parts[:4]
    if side_char not in ("w", "b"):
        raise ValueError(f"Lado a jogar inválido no FEN: {side_char!r}")

    ranks = placement.split("/")
    if len(ranks) != 8:
        raise ValueError(f"FEN precisa de 8 fileiras: {placement!r}")

    grid = [[None] * 8 for _ in range(8)]
    for index, rank in enumerate(ranks):
        row = 7 - index
        col = 0
        for char in rank:
            if char.isdigit():
                col += int(char)
            elif col < 8:
                grid[row][col] = char
                col += 1
            else:
                col += 1
        if col != 8:
            raise ValueError(f"Fileira inválida no FEN: {rank!r}")

    status = Status(
        side=Side.WHITE if side_char == "w" else Side.BLACK,
        move=int(parts[5]) if len(parts) > 5 else 1,
        half_moves=int(parts[4]) if len(parts) > 4 else 0,
        castle="" if castle == "-" else castle,
    )

    if ep != "-":
        # O FEN guarda a casa-alvo; o peão capturável fica na casa seguinte,
        # do ponto de vista de quem está a jogar.
        ep_row, ep_col = coords(ep)
        status.ep_target = ep
        status.ep_pawn = square(ep_row - 1 if status.side == Side.WHITE else ep_row + 1, ep_col)

    return grid, status


# def get_notation(piece, orig, dest):
           