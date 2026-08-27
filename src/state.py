from dataclasses import dataclass
from pieces import Side
from enum import Enum

class Draw(Enum):
    """Tipos de empate"""
    stalemate = 'Rei Afogado'
    repeated = 'Empate por repetição'
    fiftymoves = 'Regra dos 50 lances'
    material = 'Material insuficiente'
    agreement = 'Empate por comum acordo'

@dataclass
class Status:
    side: Side = Side.WHITE
    move: int = 1
    half_moves: int = 0
    castle: str = 'KQkq'    
    en_passant: str | None = None
    ep_holder: str | None = None
    check_mate: Side | None = None
    draw: Draw | None = None
    finished: bool = False
    