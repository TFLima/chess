"""Testes de notação: conversão de casas e ida-e-volta de FEN.

Rodar com: python tests/test_notation.py
"""
import _caminho  # noqa: F401  (ajusta o sys.path)
from game import Game
from notation import coords, square, generate_fen, parse_fen

CASAS_INVALIDAS = ["", "e", "e2e4", "z2", "e9", "e0", "22", None, 42]


def test_coords_rejeita_entrada_invalida():
    for entrada in CASAS_INVALIDAS:
        try:
            coords(entrada)
        except ValueError:
            continue
        raise AssertionError(f"coords({entrada!r}) deveria ter levantado ValueError")


def test_coords_e_square_sao_inversas():
    for row in range(8):
        for col in range(8):
            assert coords(square(row, col)) == (row, col)

    assert coords("a1") == (0, 0)
    assert coords("h8") == (7, 7)
    assert coords("E2") == coords("e2")


def test_fen_usa_a_casa_alvo_do_en_passant():
    """O FEN registra a casa ATRÁS do peão, não a casa onde ele parou."""
    jogo = Game()

    jogo.play("e2", "e4")
    assert generate_fen(jogo.board.grid, jogo.status).split()[3] == "e3"

    jogo.play("e7", "e5")
    assert generate_fen(jogo.board.grid, jogo.status).split()[3] == "e6"

    jogo.play("g1", "f3")
    assert generate_fen(jogo.board.grid, jogo.status).split()[3] == "-"


def test_fen_ida_e_volta():
    posicoes = [
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    ]
    for fen in posicoes:
        grid, status = parse_fen(fen)
        assert generate_fen(grid, status) == fen


def test_game_carrega_de_fen():
    fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    jogo = Game(fen)

    assert generate_fen(jogo.board.grid, jogo.status) == fen
    # Roque dos dois lados disponível para as brancas nessa posição.
    assert coords("g1") in jogo.legal_moves[coords("e1")]
    assert coords("c1") in jogo.legal_moves[coords("e1")]


if __name__ == "__main__":
    for nome, teste in sorted(list(globals().items())):
        if nome.startswith("test_"):
            teste()
            print(f"{nome}: ok")
