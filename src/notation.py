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
        case 0: return f"a{col + 1}"
        case 1: return f"b{col + 1}"
        case 2: return f"c{col + 1}"
        case 3: return f"d{col + 1}"
        case 4: return f"e{col + 1}"
        case 5: return f"f{col + 1}"
        case 6: return f"g{col + 1}"
        case 7: return f"h{col + 1}"
        case _:
            raise ValueError('Posição inválida')
        
    
