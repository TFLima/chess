from state import Status

def coords(square):
    """Converte notação algébrica (ex: 'e2') para (row, col) 0-indexado."""
    col = ord(square[0]) - ord("a")
    row = int(square[1]) - 1

    if not (0 <= col < 8 and 0 <= row < 8):
        raise ValueError("Posição inválida")

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
    from pieces import Side

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
    en_passant = status.en_passant if status.en_passant is not None else "-"
    half_moves = str(status.half_moves)

    return f"{fen} {side} {castle} {en_passant} {half_moves} {status.move}"


# def get_notation(piece, orig, dest):
           