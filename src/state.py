from dataclasses import dataclass
from pieces import Side


@dataclass
class Status:
    side: Side = Side.WHITE
    move: int = 1
    half_move: bool = False
    castle: str = 'KQkq'    
    en_passant: str | None = None
    ep_holder: str | None = None