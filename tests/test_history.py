"""Testes do histórico: o que cada lance registra e como a repetição é contada.

Rodar com: python tests/test_history.py
"""
import _caminho  # noqa: F401  (ajusta o sys.path)
from dataclasses import replace

from board import Board
from game import Game
from history import History
from notation import coords, generate_fen
from pieces import Side
from state import Draw, Status

INICIAL = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

# 1.Cf3 Cf6 2.Cg1 Cg8 devolve a posição inicial; repetido, dá tripla repetição.
IDA_E_VOLTA = [("g1", "f3"), ("g8", "f6"), ("f3", "g1"), ("f6", "g8")]

# Mate do pastor mais curto: 1.f3 e5 2.g4 Dh4#
MATE_DO_LOUCO = [("f2", "f3"), ("e7", "e5"), ("g2", "g4"), ("d8", "h4")]


def _posicao(fen=None):
    """Um History vazio junto com o tabuleiro e o status descritos pelo FEN."""
    jogo = Game(fen)
    return History(), jogo.board, jogo.status


def test_update_registra_a_posicao_anterior_ao_lance():
    """O registro é a fotografia de ANTES do lance, não do resultado dele."""
    jogo = Game()
    jogo.play("e2", "e4")

    registro = jogo.history.registry["1.w"]

    assert registro.fen == INICIAL
    assert registro.position == repr(Game().board)
    assert registro.move == ("e2", "e4")
    # O tabuleiro do jogo já andou; o registro não.
    assert registro.position != repr(jogo.board)


def test_chave_do_registro_combina_lance_e_lado():
    jogo = Game()
    jogo.play("e2", "e4")
    jogo.play("e7", "e5")
    jogo.play("g1", "f3")

    assert sorted(jogo.history.registry) == ["1.b", "1.w", "2.w"]
    assert jogo.history.registry["1.b"].status.side is Side.BLACK
    assert jogo.history.registry["2.w"].status.move == 2


def test_status_do_registro_e_uma_copia():
    """Game altera o Status no lugar; o histórico não pode andar junto."""
    jogo = Game()
    jogo.play("e2", "e4")

    registro = jogo.history.registry["1.w"]
    assert (registro.status.side, registro.status.move) == (Side.WHITE, 1)

    jogo.play("e7", "e5")
    jogo.play("g1", "f3")

    assert (registro.status.side, registro.status.move) == (Side.WHITE, 1)
    assert registro.status is not jogo.status


def test_find_position_conta_cada_registro_da_mesma_posicao():
    history, board, status = _posicao()

    assert history.find_position(repr(board), status) == 0

    history.update(board, status)
    assert history.find_position(repr(board), status) == 1

    # Mesma posição, chave de registro diferente: conta como segunda ocorrência.
    history.update(board, replace(status, move=2))
    assert history.find_position(repr(board), status) == 2


def test_find_position_exige_o_mesmo_lado_a_jogar():
    history, board, status = _posicao()
    history.update(board, status)

    assert history.find_position(repr(board), replace(status, side=Side.BLACK)) == 0


def test_find_position_exige_os_mesmos_direitos_de_roque():
    """Torre ou rei que já se mexeram mudam a posição, mesmo com as peças nas mesmas casas."""
    history, board, status = _posicao()
    history.update(board, status)

    assert history.find_position(repr(board), replace(status, castle="kq")) == 0


def test_find_position_exige_o_mesmo_en_passant():
    history, board, status = _posicao("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2")
    history.update(board, status)

    assert history.find_position(repr(board), status) == 1
    assert history.find_position(repr(board), replace(status, ep_target=None)) == 0


def test_find_position_ignora_o_contador_de_lances():
    """Só tabuleiro, lado, roques e en passant contam — nem o número do lance, nem os 50 lances."""
    history, board, status = _posicao()
    history.update(board, status)

    outro = replace(status, move=7, half_moves=13)
    assert history.find_position(repr(board), outro) == 1


def test_empate_por_repeticao_encerra_a_partida():
    jogo = Game()

    for orig, dest in IDA_E_VOLTA:
        jogo.play(orig, dest)

    # Segunda ocorrência da posição inicial: ainda não é empate.
    assert not jogo.status.finished
    assert jogo.history.find_position(repr(jogo.board), jogo.status) == 1

    for orig, dest in IDA_E_VOLTA:
        jogo.play(orig, dest)

    assert jogo.status.finished
    assert jogo.status.draw is Draw.repeated


def test_partida_encerrada_registra_a_posicao_final():
    jogo = Game()

    for orig, dest in MATE_DO_LOUCO:
        jogo.play(orig, dest)

    final = jogo.history.registry["3.w"]

    assert final.fen == generate_fen(jogo.board.grid, jogo.status)
    assert final.status.check_mate is Side.BLACK
    assert final.status.finished
    # O registro de fim de partida não vem de um lance.
    assert final.move == (None, None)


def test_partida_iniciada_ja_terminada_registra_a_posicao():
    """Um FEN que já é mate entra no histórico antes do primeiro lance."""
    jogo = Game("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")

    assert jogo.status.finished
    assert sorted(jogo.history.registry) == ["3.w"]
    assert jogo.history.registry["3.w"].status.check_mate is Side.BLACK


def test_lance_recusado_nao_entra_no_historico():
    jogo = Game()

    for orig, dest in [("e2", "e5"), ("e4", "e5"), ("a1", "a3")]:
        try:
            jogo.play(orig, dest)
        except ValueError:
            continue
        raise AssertionError(f"play({orig!r}, {dest!r}) deveria ter levantado ValueError")

    assert jogo.history.registry == {}


def test_history_nasce_vazio():
    history = History()

    assert history.registry == {}
    assert history.find_position(repr(Board()), Status()) == 0


if __name__ == "__main__":
    for nome, teste in sorted(list(globals().items())):
        if nome.startswith("test_"):
            teste()
            print(f"{nome}: ok")
