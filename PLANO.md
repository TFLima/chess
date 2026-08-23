# Plano de Aprendizado — Jogo de Xadrez em Python

## Etapa 0 — Pré-requisitos
- Python OOP sólido: classes, herança, `__repr__`, listas/dicionários.
- Não precisa saber nada de xadrez avançado, só as regras de movimento das peças.

## Etapa 1 — Representar o tabuleiro
- Decidir a estrutura: matriz 8x8 (`list[list]`) é a mais didática para começar.
- Definir coordenadas (ex: `(linha, coluna)` ou notação algébrica `"e4"`) e já pensar em como converter entre as duas.
- Criar uma função para **imprimir o tabuleiro no terminal**. Ter feedback visual cedo ajuda muito a debugar.

## Etapa 2 — Representar as peças
- Uma classe base `Peca` (ou usar apenas caracteres/strings, se quiser começar mais simples) com atributos como cor e tipo.
- Decidir: peças como objetos (mais POO, permite herança tipo `Peao`, `Torre`, `Rei`) ou peças como strings/enums (mais simples, menos abstração). Começar simples — dá pra refatorar depois.

## Etapa 3 — Movimento básico (sem regras especiais)
- Para cada tipo de peça, implementar a lógica de "quais casas essa peça pode alcançar, ignorando o resto do tabuleiro" (ex: torre anda em linha reta).
- Depois, filtrar esses movimentos considerando peças no caminho e peças aliadas/inimigas no destino.
- Núcleo do projeto — vale testar cada peça isoladamente antes de seguir.

## Etapa 4 — Loop do jogo
- Alternância de turnos (branco/preto).
- Entrada do usuário via terminal (ex: digitar `"e2 e4"`).
- Validação: o movimento é legal? A peça é do jogador da vez?

## Etapa 5 — Regras especiais
Ordem de dificuldade crescente:
1. Promoção de peão
2. Roque (castling)
3. En passant
4. Xeque (detectar se o rei está ameaçado)
5. Movimentos que deixariam o próprio rei em xeque (ilegais)
6. Xeque-mate e afogamento (stalemate)

## Etapa 6 — Polimento de regras
- Empate por repetição de posição, regra dos 50 lances, material insuficiente (opcional, mais avançado).

## Etapa 7 — Interface
- Terminar bem o essencial em **texto no terminal** antes de partir pra GUI.
- Interface gráfica depois: `pygame` é o caminho mais comum e didático.

## Etapa 8 (opcional, avançado) — Um "adversário" simples
- Só depois que o motor de regras estiver 100% correto.
- Começar com jogada aleatória válida, depois evoluir pra minimax com poda alfa-beta e uma função de avaliação simples (contagem de material).

---

## Dicas de processo
- **Testar cada peça isoladamente** antes de integrar tudo — é fácil acumular bugs sutis nas regras de movimento.
- A lib `python-chess` implementa todas as regras — não usar pra "atalhar" o aprendizado, mas é ótima como **referência/gabarito** pra comparar resultados (ex: comparar lista de movimentos legais numa posição específica) quando surgir suspeita de bug.
- A parte mais difícil costuma ser "detectar se um movimento deixa o próprio rei em xeque" — não subestimar essa etapa.

---

## Estrutura de arquivos

```
xadrez/
├── main.py
├── board.py
├── pieces.py
├── moves.py
├── game.py
└── utils.py
```

### `board.py`
- Classe `Board` (ou `Tabuleiro`): guarda a matriz 8x8, sabe posicionar/remover peças, sabe imprimir a si mesma.
- Não sabe nada sobre "regras de xadrez" — só sobre o estado físico do tabuleiro.

### `pieces.py`
- Classe base `Piece` + subclasses (`Pawn`, `Rook`, `Knight`, `Bishop`, `Queen`, `King`).
- Cada peça sabe gerar seus **movimentos "pseudo-legais"** (ignorando se deixa o rei em xeque) — lógica da Etapa 3.
- Isolado porque é a parte testada peça por peça.

### `moves.py`
- Funções que pegam os movimentos pseudo-legais de `pieces.py` e aplicam os filtros "de verdade": bloqueio por peças no caminho, capturas, e principalmente **filtrar movimentos que deixam o próprio rei em xeque**.
- Lugar natural pra roque, en passant e promoção — regras especiais tendem a ficar mais organizadas aqui do que dentro da própria classe da peça.

### `game.py`
- Classe `Game`: dono do loop principal, turnos, histórico de lances, detecção de xeque-mate/afogamento/empate.
- Orquestra `board.py` + `moves.py`, mas não reimplementa a lógica delas.

### `utils.py`
- Conversões entre notação algébrica (`"e4"`) e índices de matriz (`(4, 4)`), e helpers de exibição no terminal.

### `main.py`
- Ponto de entrada: cria o `Game`, roda o loop.

### Por que separar assim
- **`pieces.py` isolado** permite testar "quais movimentos essa peça pode fazer nessa posição" sem precisar rodar o jogo inteiro — importante pra Etapa 3.
- **`moves.py` separado de `pieces.py`** evita que a lógica de "isso deixa o rei em xeque?" fique acoplada dentro de cada classe de peça — tende a virar bagunça se não separado cedo.
- **`game.py` fino**, sem lógica de regras — só orquestração — facilita trocar depois a interface (terminal → pygame) sem tocar nas regras.

Mais pra frente (Etapa 8), um `ai.py` separado seria o lugar natural pro minimax, sem misturar com a lógica de regras.
