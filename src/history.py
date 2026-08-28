from dataclasses import dataclass, replace
from state import Status


@dataclass
class Record:
    position: str
    status: Status
    move: tuple[str | None, str | None]


class History:

    def __init__(self):
        self.registry: dict[str, Record] = {}

    def update(self, position, status: Status, orig = None, dest = None):
        # Cópia do status: Game altera o original no lugar a cada lance.
        record = Record(position, replace(status), (orig, dest))

        record_id = str(status.move)+'.'+status.side.value
        self.registry[record_id] = record

    def find_position(self, position, status: Status):
        """Quantas vezes a posição já foi registrada com os mesmos direitos e lado a jogar."""
        key = self._key(position, status)

        return sum(1 for record in self.registry.values()
                   if self._key(record.position, record.status) == key)

    @staticmethod
    def _key(position, status: Status):
        """Uma repetição exige tabuleiro, lado a jogar, roques e en passant iguais."""
        return (position, status.side, status.castle, status.ep_target)
