from dataclasses import replace

from board import Board
from game import Game
from history import Record
from notation import generate_fen, parse_fen
from pieces import Side
from state import Status


class Replay:
    """Percorre as posições guardadas no histórico, sem tocar na partida."""

    board: Board
    status: Status
    cursor: int

    def __init__(self, game: Game):
        self.records = list(game.history.registry.values())

        # Só o fim de partida registra a posição resultante do último lance:
        # numa partida em curso, a posição atual ainda não está no histórico.
        if not game.status.finished:
            self.records.append(Record(repr(game.board),
                                       replace(game.status),
                                       (None, None),
                                       generate_fen(game.board.grid, game.status)))

        if not self.records:
            raise ValueError("Histórico vazio: não há o que rever.")

        self.board = Board()
        self.cursor = len(self.records) - 1
        self._load()

    def back(self):
        self._go_to(self.cursor - 1)

    def next(self):
        self._go_to(self.cursor + 1)

    def first(self):
        self._go_to(0)

    def last(self):
        self._go_to(len(self.records) - 1)

    def _go_to(self, index):
        """Nas pontas, avançar ou voltar não faz nada."""
        self.cursor = max(0, min(index, len(self.records) - 1))
        self._load()

    def _load(self):
        self.board.grid, self.status = parse_fen(self.records[self.cursor].fen)

    def __repr__(self):
        record = self.records[self.cursor]
        lado = 'brancas' if self.status.side == Side.WHITE else 'pretas'

        # O último registro não tem lance: é a posição em que a partida parou.
        orig, dest = record.move
        if orig is not None:
            lance = f"{orig} {dest}"
        else:
            lance = "fim de partida" if record.status.finished else "posição atual"

        return (f"[{self.cursor + 1}/{len(self.records)}] "
                f"lance {self.status.move}, {lado} — {lance}\n{self.board}")
