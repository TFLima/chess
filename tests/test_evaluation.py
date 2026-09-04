"""Testes da estrutura de peões da avaliação.

Rodar com: python tests/test_evaluation.py
"""
import _caminho  # noqa: F401  (ajusta o sys.path)
from game import Game
from pieces import Side
from bot.evaluation import (
    evaluation, pawn_structure, _taper,
    PASSED_BONUS, PASSED_WEIGHT, ISLAND_PENALTY, ISLAND_WEIGHT,
    CONNECTED_BONUS, CONNECTED_WEIGHT, DEFENDED_EXTRA,
    DOUBLED_PENALTY, ISOLATED_PENALTY, BACKWARD_PENALTY,
)

MEIO_JOGO = 1.0
FINAL = 0.0

# Peões inimigos em todas as colunas, longe o bastante para não interferir:
# bloqueiam qualquer peão passado sem gerar bloqueio nem atraso.
MURO_PRETO = {col: [6] for col in range(8)}


def _colunas(brancas, pretas):
    return {Side.WHITE: brancas, Side.BLACK: pretas}


def _espelha(pawn_columns):
    """Troca os lados e reflete as fileiras, para comparar brancas com pretas."""
    return {
        Side.WHITE: {col: [7 - row for row in rows]
                     for col, rows in pawn_columns[Side.BLACK].items()},
        Side.BLACK: {col: [7 - row for row in rows]
                     for col, rows in pawn_columns[Side.WHITE].items()},
    }


def _brancas(colunas_brancas, phase, colunas_pretas=None):
    colunas = _colunas(colunas_brancas, colunas_pretas or MURO_PRETO)
    return pawn_structure(Side.WHITE, colunas, phase)


# Os valores esperados são derivados das próprias constantes: os testes
# continuam válidos enquanto os pesos forem calibrados.
def _dobrado(phase):
    return _taper(*DOUBLED_PENALTY, phase)


def _isolado(phase):
    return _taper(*ISOLATED_PENALTY, phase)


def _atrasado(phase):
    return _taper(*BACKWARD_PENALTY, phase)


def _defendido(phase):
    return _taper(*DEFENDED_EXTRA, phase)


def _passado(row, phase):
    return PASSED_BONUS[row] * _taper(*PASSED_WEIGHT, phase)


def _falange(row, phase):
    return CONNECTED_BONUS[row] * _taper(*CONNECTED_WEIGHT, phase)


def _ilhas(quantidade, phase):
    return ISLAND_PENALTY[quantidade] * _taper(*ISLAND_WEIGHT, phase)


# --- peões dobrados e isolados ---------------------------------------------

def test_peoes_dobrados_penalizam_cada_peao_extra():
    """d6 acompanha a coluna e sem conectar com ela: tira o isolamento da conta."""
    def coluna_e(rows, phase):
        return _brancas({3: [5], 4: rows}, phase)

    for phase in (MEIO_JOGO, FINAL):
        assert coluna_e([1], phase) == 0
        assert coluna_e([1, 3], phase) == -_dobrado(phase)
        assert coluna_e([1, 2, 3], phase) == -2 * _dobrado(phase)


def test_peao_isolado_penaliza_cada_peao_da_coluna():
    """O isolamento conta por peão: dobrado E isolado soma as duas fraquezas."""
    for phase in (MEIO_JOGO, FINAL):
        so_isolado = _brancas({4: [1]}, phase, {3: [6], 5: [6]})
        dobrado_isolado = _brancas({4: [1, 3]}, phase, {3: [6], 5: [6]})

        assert so_isolado == -_isolado(phase)
        assert dobrado_isolado == -_dobrado(phase) - 2 * _isolado(phase)


def test_fraquezas_de_peao_pesam_mais_no_final():
    """Regressão: a fase já esteve invertida e zerava as fraquezas no final."""
    colunas = {2: [1, 3]}  # dobrado e isolado
    meio = _brancas(colunas, MEIO_JOGO, {1: [6], 3: [6]})
    final = _brancas(colunas, FINAL, {1: [6], 3: [6]})

    assert final < meio < 0
    for peso in (DOUBLED_PENALTY, ISOLATED_PENALTY, BACKWARD_PENALTY):
        mg, eg = peso
        assert 0 < mg < eg, f"{peso} deveria crescer do meio-jogo para o final"


# --- peões passados ---------------------------------------------------------

def test_peao_passado_premia_conforme_o_avanco():
    # O peao da coluna a esta isolado nos dois casos: a penalidade e constante.
    for row in range(1, 7):
        esperado = _passado(row, FINAL) - _isolado(FINAL)
        assert _brancas({0: [row]}, FINAL, {3: [6]}) == esperado

    valores = [_brancas({0: [row]}, FINAL, {3: [6]}) for row in range(1, 7)]
    assert valores == sorted(valores)


def test_passado_vale_mais_no_final_mas_nao_zera_no_meio_jogo():
    """Regressão: com o peso zerado, um passado na 7ª fileira pontuava negativo."""
    meio = _brancas({0: [6]}, MEIO_JOGO, {3: [6]})
    final = _brancas({0: [6]}, FINAL, {3: [6]})

    assert 0 < meio < final


def test_peao_passado_das_pretas_usa_a_fileira_espelhada():
    branco = pawn_structure(Side.WHITE, _colunas({0: [5]}, {3: [6]}), FINAL)
    preto = pawn_structure(Side.BLACK, _colunas({3: [1]}, {0: [2]}), FINAL)

    assert branco == preto == _passado(5, FINAL) - _isolado(FINAL)


def test_peao_travado_por_inimigo_a_frente_nao_e_passado():
    assert _brancas({4: [3]}, FINAL, {4: [5]}) == -_isolado(FINAL)
    assert _brancas({4: [3]}, FINAL, {5: [4]}) == -_isolado(FINAL)


def test_inimigo_atras_do_peao_nao_impede_o_passado():
    """Peão inimigo na coluna vizinha, mas atrás: não alcança mais o nosso peão."""
    assert _brancas({4: [5]}, FINAL, {5: [2]}) == _passado(5, FINAL) - _isolado(FINAL)


# --- peões conectados -------------------------------------------------------

def test_falange_cresce_com_a_fileira():
    """Regressão: o bônus era uma constante plana, igual na 2ª e na 7ª fileira."""
    valores = [_brancas({0: [row], 1: [row]}, FINAL) for row in range(1, 7)]

    assert valores == sorted(valores)
    assert valores[0] < valores[-1]


def test_falange_e_defesa_somam_em_vez_de_competir():
    """Regressão: o max() colapsava as duas relações numa só."""
    so_falange = _brancas({1: [3], 2: [3]}, FINAL)          # b4 e c4 lado a lado
    so_defesa = _brancas({0: [2], 1: [3]}, FINAL)           # a3 defende b4
    ambos = _brancas({0: [2], 1: [3], 2: [3]}, FINAL)       # b4 tem as duas coisas

    assert so_falange == 2 * _falange(3, FINAL)
    assert so_defesa == _defendido(FINAL)
    assert ambos == so_falange + so_defesa


def test_conectados_valem_mais_no_final():
    colunas = {3: [4], 4: [4]}

    assert _brancas(colunas, MEIO_JOGO) < _brancas(colunas, FINAL)


# --- ilhas ------------------------------------------------------------------

def test_ilhas_de_peoes_penalizam_por_grupo():
    # Colunas alternadas: cada peão é uma ilha, sem bônus de conexão.
    for quantidade in range(1, 5):
        colunas = {col * 2: [1] for col in range(quantidade)}
        esperado = -_ilhas(quantidade, FINAL) - quantidade * _isolado(FINAL)

        assert _brancas(colunas, FINAL) == esperado


def test_colunas_contiguas_formam_uma_ilha_so():
    assert _brancas({0: [1], 1: [1], 2: [1]}, FINAL) == 3 * _falange(1, FINAL)


def test_ilhas_pesam_mais_no_final():
    colunas = {0: [1], 2: [1], 4: [1]}

    assert _brancas(colunas, FINAL) < _brancas(colunas, MEIO_JOGO) < 0


# --- peões atrasados --------------------------------------------------------

def test_peao_atrasado_e_bloqueado_leva_penalidade():
    """b2 atrás de a4, com peão inimigo em b3 travando o avanço."""
    colunas = _colunas({0: [3], 1: [1]}, {0: [6], 1: [2], 2: [6]})

    assert pawn_structure(Side.WHITE, colunas, FINAL) == -_atrasado(FINAL)


def test_peao_atrasado_com_casa_de_avanco_guardada():
    """b2 atrás de a3, com peão inimigo em c4 controlando b3."""
    colunas = _colunas({0: [2], 1: [1]}, {0: [6], 1: [6], 2: [3]})

    assert (pawn_structure(Side.WHITE, colunas, FINAL)
            == _defendido(FINAL) - _atrasado(FINAL))


def test_peao_alinhado_com_os_vizinhos_nao_e_atrasado():
    """Mesmo bloqueado, b2 não está atrás de a2: sem penalidade de atraso."""
    colunas = _colunas({0: [1], 1: [1]}, {0: [6], 1: [2], 2: [6]})

    assert pawn_structure(Side.WHITE, colunas, FINAL) == 2 * _falange(1, FINAL)


def test_peao_isolado_nao_conta_como_atrasado():
    """Sem vizinhos não há com o que comparar o atraso; só o isolamento conta."""
    colunas = _colunas({4: [1]}, {3: [6], 4: [2], 5: [6]})

    assert pawn_structure(Side.WHITE, colunas, FINAL) == -_isolado(FINAL)


# --- casos de borda e integração --------------------------------------------

def test_lado_sem_peoes_nao_quebra():
    for phase in (MEIO_JOGO, FINAL):
        assert pawn_structure(Side.WHITE, _colunas({}, MURO_PRETO), phase) == 0
        assert pawn_structure(Side.BLACK, _colunas(MURO_PRETO, {}), phase) == 0


def test_estrutura_e_simetrica_entre_os_lados():
    colunas = _colunas(
        {0: [1], 1: [1, 3], 3: [4], 4: [1], 6: [2], 7: [1]},
        {0: [6], 2: [5], 3: [6], 5: [6], 6: [6], 7: [4]},
    )
    for phase in (MEIO_JOGO, 0.5, FINAL):
        assert (pawn_structure(Side.WHITE, colunas, phase)
                == pawn_structure(Side.BLACK, _espelha(colunas), phase))


def test_avaliacao_e_zero_na_posicao_inicial():
    assert evaluation(Game().board) == 0


def test_avaliacao_roda_em_posicoes_com_colunas_semiabertas():
    """Regressão: colunas sem peão inimigo já derrubaram a estrutura de peões."""
    posicoes = [
        "rnbqkbnr/ppp1pppp/8/3P4/8/8/PPPP1PPP/RNBQKBNR b KQkq - 0 2",
        "8/5k2/8/2p5/8/4K3/6P1/8 w - - 0 1",
        "4k3/pppppppp/8/8/8/8/8/4K3 w - - 0 1",  # brancas sem nenhum peão
        "4k3/8/8/8/8/8/PPPPPPPP/4K3 w - - 0 1",  # pretas sem nenhum peão
        "8/8/4k3/8/8/4K3/8/8 w - - 0 1",         # nenhum peão no tabuleiro
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    ]
    for fen in posicoes:
        assert isinstance(evaluation(Game(fen).board), (int, float))


if __name__ == "__main__":
    for nome, teste in sorted(list(globals().items())):
        if nome.startswith("test_"):
            teste()
            print(f"{nome}: ok")
