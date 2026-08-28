# Perft — o teste de regras do motor

> Referência de apoio a [`tests/test_perft.py`](tests/test_perft.py).
> Rodar com `python tests/test_perft.py` (~40s).

## O que é

Perft (*performance test*) conta **quantas folhas** tem a árvore de lances a partir de uma
posição, até uma profundidade N. Da posição inicial:

- profundidade 1 → 20 (as 20 primeiras jogadas das brancas)
- profundidade 2 → 400 (cada uma das 20 tem 20 respostas)
- profundidade 3 → 8.902

Esses números são conhecidos e publicados. É aí que está a graça: **perft é um teste de
regras disfarçado de contagem**. Se o gerador de lances produzir exatamente o conjunto
certo de lances legais em cada um dos 8.902 nós, o total bate. Se em *um único* nó lá no
fundo da árvore um lance ilegal passar, ou um legal for bloqueado, o total sai errado.

É por isso que compensa tanto: um `assert` sobre um inteiro cobre milhares de posições que
ninguém teria paciência de escrever à mão. Não é preciso escrever um teste "cavalo cravado
não pode se mover" — se estivesse errado, o número não bateria.

## Como ler uma falha

O sinal do erro já aponta a direção:

| Sintoma | Significado | Onde olhar |
|---|---|---|
| contagem **maior** que a esperada | algo **ilegal** está passando | filtro de xeque em `legal_moves`, roque através de casa atacada, peça cravada |
| contagem **menor** que a esperada | algo **legal** está sendo bloqueado | en passant não encontrado, roque negado à toa, raio interrompido cedo demais |

Se a profundidade 1 bate mas a 2 não, o bug não está na posição inicial — está em alguma
posição que só aparece depois de um lance. Daí a técnica de *divide*, mais abaixo.

## As posições

Não são aleatórias: são as posições de referência clássicas, cada uma desenhada para
quebrar um tipo de motor.

| # | Posição | O que estressa |
|---|---|---|
| 1 | inicial | sanidade geral |
| 2 | Kiwipete | roque dos dois lados, peças cravadas, muitas capturas — a mais famosa para achar bugs |
| 3 | final de torres | en passant |
| 4 | — | promoção combinada com direitos de roque |
| 5 | — | roque e promoção em posição travada |

FENs, como estão em `POSICOES`:

```
2  r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq -
3  8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - -
4  r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq -
5  rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ -
```

### Números de referência

As profundidades marcadas com ✅ são as que a suíte roda hoje — escolhidas para o teste
terminar em tempo tolerável. As demais vêm das tabelas publicadas e ficam aqui para quando
o perft ficar rápido o bastante (ver "Por que 40 segundos", abaixo).

| Posição | d1 | d2 | d3 | d4 | d5 |
|---|---|---|---|---|---|
| inicial | 20 ✅ | 400 ✅ | 8.902 ✅ | 197.281 | 4.865.609 |
| Kiwipete | 48 ✅ | 2.039 ✅ | 97.862 | 4.085.603 | 193.690.690 |
| posição 3 | 14 ✅ | 191 ✅ | 2.812 ✅ | 43.238 | 674.624 |
| posição 4 | 6 ✅ | 264 ✅ | 9.467 | 422.333 | 15.833.292 |
| posição 5 | 44 ✅ | 1.486 ✅ | 62.379 | 2.103.487 | 89.941.194 |

## Como o teste funciona

O núcleo é a recursão em `perft()`:

```python
def perft(game, depth):
    if depth == 0:
        return 1          # cheguei numa folha: conta 1
    total = 0
    for origem, destinos in game.legal_moves.items():
        ...
                seguinte = copy.deepcopy(game)
                seguinte.play(orig, dest, promocao)
                total += perft(seguinte, depth - 1)
    return total
```

Três pontos que não são óbvios:

### O `deepcopy`

Perft precisa jogar um lance, contar a subárvore e **voltar**. Como o `Game` não tem
desfazer, o teste copia o jogo inteiro antes de cada lance e joga na cópia — o original
fica intacto.

### As promoções contam quatro vezes

Perft conta cada peça de promoção como um lance **distinto**: chegar a e8 virando dama,
torre, bispo ou cavalo são 4 lances, não 1. Mas `legal_moves` devolve só o destino — a
escolha da peça vem depois, em `play(orig, dest, promocao)`. Por isso:

```python
opcoes = PROMOCOES if game.will_promote(orig, dest) else ("q",)
```

Sem essa linha a posição 4 daria contagem baixa, e pareceria um bug no motor quando na
verdade seria um bug no teste.

### O `_caminho.py`

Só um `sys.path.insert` para os testes acharem `src/` sem transformar o projeto num pacote
instalável. Necessário porque os módulos se importam por nome (`from board import Board`).

## Por que 40 segundos

O `deepcopy` é o gargalo: 8.902 folhas significam milhares de cópias do tabuleiro inteiro.

`moves.py` já tem `unmake_move`, e o próprio `legal_moves` usa essa técnica internamente
(joga, testa xeque, desfaz). O que falta é um **desfazer no nível do `Game`**, que
precisaria restaurar também roques, en passant e o relógio dos 50 lances. Com ele o perft
fica ordens de magnitude mais rápido — e a interface ganha botão de "voltar lance" de
graça, porque é exatamente a mesma operação.

## Perft divide — localizando o bug

Quando algo quebrar, o teste vai dizer apenas *"posição 3, profundidade 3: 2811 != 2812"*.
Falta um lance em algum lugar de uma árvore de 2.812 folhas.

A técnica padrão é o **divide**: em vez do total, imprimir a contagem **por primeiro
lance**.

```python
def perft_divide(game, depth):
    """Contagem por primeiro lance — para localizar onde o motor diverge."""
    for origem, destinos in sorted(game.legal_moves.items()):
        for destino in sorted(destinos):
            orig, dest = square(*origem), square(*destino)
            opcoes = PROMOCOES if game.will_promote(orig, dest) else ("q",)
            for promocao in opcoes:
                seguinte = copy.deepcopy(game)
                seguinte.play(orig, dest, promocao)
                rotulo = orig + dest + (promocao if len(opcoes) > 1 else "")
                print(f"{rotulo}: {perft(seguinte, depth - 1)}")
```

Compare a saída com a de um motor de referência. O `python-chess` serve de gabarito —
o `PLANO.md` já sugere usá-lo assim: nunca para escrever as regras, sempre para conferir.

```python
import chess

def perft_ref(board, depth):
    if depth == 0:
        return 1
    total = 0
    for move in board.legal_moves:
        board.push(move)
        total += perft_ref(board, depth - 1)
        board.pop()
    return total

board = chess.Board(FEN)
for move in board.legal_moves:
    board.push(move)
    print(f"{move.uci()}: {perft_ref(board, DEPTH - 1)}")
    board.pop()
```

O formato bate de propósito: o `rotulo` acima produz `g1f3` e `e7e8q`, que é exatamente o
UCI que o `python-chess` imprime. As duas saídas são diretamente comparáveis com um `diff`.

O procedimento então é:

1. Rodar os dois divides na posição que falhou e achar **o primeiro lance cuja subárvore
   diverge**.
2. Jogar aquele lance nas duas pontas e repetir o divide um nível abaixo.
3. Repetir até a profundidade 1 — aí a divergência é uma lista de lances legais, e dá para
   ver a olho qual lance sobra ou falta.

Em 3 ou 4 iterações você chega na posição exata e no lance exato onde o motor discorda, em
vez de caçar às cegas.

## Referências

- Chess Programming Wiki — [Perft](https://www.chessprogramming.org/Perft) e
  [Perft Results](https://www.chessprogramming.org/Perft_Results) (origem das tabelas acima)
- [python-chess](https://python-chess.readthedocs.io/) — gabarito para o divide
