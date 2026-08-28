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
    ep_target: str | None = None   # casa-alvo do en passant (convenção FEN: atrás do peão)
    ep_pawn: str | None = None     # casa do peão que acabou de avançar duas e pode ser capturado
    check_mate: Side | None = None
    draw: Draw | None = None
    finished: bool = False
    