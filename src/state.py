from dataclasses import dataclass
from pieces import Side


@dataclass
class Status:
    side: Side = Side.WHITE
    castle: str = 'KQkq'    
    en_passant: str | None = None