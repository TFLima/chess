def coords(square):
    """Converte notação algébrica (ex: 'e2') para (row, col) 0-indexado."""
    col = ord(square[0]) - ord("a")
    row = int(square[1]) - 1
    return row, col
