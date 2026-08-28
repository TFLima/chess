"""Perft: conta as folhas da árvore de lances até uma dada profundidade.

Os números esperados são os valores de referência publicados (chessprogramming.org).
Qualquer divergência aponta um bug na geração de lances: um lance a mais significa
que algo ilegal está passando; um a menos, que algo legal está sendo bloqueado.

Rodar com: python tests/test_perft.py
"""
import copy

import _caminho  # noqa: F401  (ajusta o sys.path)
from game import Game
from notation import square

# (nome, fen ou None para a posição inicial, {profundidade: nós esperados})
POSICOES = [
    ("inicial", None,
     {1: 20, 2: 400, 3: 8902}),
    ("kiwipete (roque e pinos)", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq -",
     {1: 48, 2: 2039}),
    ("posição 3 (en passant)", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - -",
     {1: 14, 2: 191, 3: 2812}),
    ("posição 4 (promoção)", "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq -",
     {1: 6, 2: 264}),
    ("posição 5", "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ -",
     {1: 44, 2: 1486}),
]

PROMOCOES = ("q", "r", "b", "n")


def perft(game: Game, depth: int) -> int:
    if depth == 0:
        return 1

    total = 0
    for origem, destinos in game.legal_moves.items():
        orig = square(*origem)
        for destino in destinos:
            dest = square(*destino)
            # Perft conta cada peça de promoção como um lance distinto.
            opcoes = PROMOCOES if game.will_promote(orig, dest) else ("q",)
            for promocao in opcoes:
                seguinte = copy.deepcopy(game)
                seguinte.play(orig, dest, promocao)
                total += perft(seguinte, depth - 1)

    return total


def test_perft():
    for nome, fen, esperados in POSICOES:
        base = Game() if fen is None else Game(fen)
        for depth, esperado in sorted(esperados.items()):
            obtido = perft(copy.deepcopy(base), depth)
            assert obtido == esperado, f"{nome}, profundidade {depth}: {obtido} != {esperado}"


if __name__ == "__main__":
    for nome, fen, esperados in POSICOES:
        base = Game() if fen is None else Game(fen)
        for depth, esperado in sorted(esperados.items()):
            obtido = perft(copy.deepcopy(base), depth)
            ok = "ok" if obtido == esperado else "FALHOU"
            print(f"{nome:28} profundidade {depth}: {obtido:6} (esperado {esperado:6}) {ok}")
