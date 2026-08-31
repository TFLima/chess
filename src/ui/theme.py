"""Medidas e cores da interface. Nada aqui sabe de xadrez."""

SQUARE = 72                  # lado de uma casa, em pixels
MARGIN = 28                  # borda onde ficam as letras/números das casas
BOARD = SQUARE * 8
WIDTH = HEIGHT = BOARD + MARGIN * 2

BACKGROUND = (38, 36, 33)
LIGHT = (238, 238, 210)
DARK = (118, 150, 86)
SELECTED = (246, 246, 105)
LABEL = (150, 148, 140)

WHITE_PIECE = (250, 250, 248)
BLACK_PIECE = (28, 28, 26)
# Marcas de destino, em duas versões: cada uma é usada sobre o fundo oposto.
TARGET_DARK = (60, 60, 55)
TARGET_LIGHT = (235, 235, 228)
TARGET_RED = (220, 20, 60)  # para marcar o xeque

FONT_NAME = "consolas,couriernew,dejavusansmono,monospace"
# Fonte separada para as peças: precisa ter os glifos de xadrez do Unicode.
PIECE_FONT_NAME = "dejavusans,segoeuisymbol,freeserif,symbola"
PIECE_SIZE = int(SQUARE * 0.82)
LABEL_SIZE = int(MARGIN * 0.55)

OUTLINE = max(1, SQUARE // 36)   # espessura do contorno da peça
DOT_RADIUS = SQUARE // 8     # destino vazio
RING_WIDTH = SQUARE // 12    # destino com captura

# Mensagens e diálogos
MESSAGE_BG = (50, 48, 45)
MESSAGE_BORDER = (80, 78, 72)
MESSAGE_TEXT = (240, 240, 235)
MESSAGE_PADDING = 20
MESSAGE_FONT_SIZE = int(SQUARE * 0.28)
DIALOG_OPTION_BG = (70, 68, 62)
DIALOG_OPTION_HOVER = (100, 98, 90)
