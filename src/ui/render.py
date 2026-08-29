"""Desenha o tabuleiro. Recebe o que mostrar e não consulta o motor."""

import pygame

from ui import theme

CONTROLS = ['<<','','<','','','>','','>>']

# Só os glifos cheios: o vazado (♔ e cia.) some na casa clara. A peça branca
# é o mesmo desenho pintado de branco, com contorno escuro por cima.
GLYPH = {'K': '♚', 'Q': '♛', 'R': '♜',
         'B': '♝', 'N': '♞', 'P': '♟'}

# As oito direções em volta do centro, onde o contorno é desenhado.
OFFSETS = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]

def square_rect(row, col):
    """Retângulo da casa em pixels. A linha 0 é o rank 1, desenhado embaixo."""
    x = theme.MARGIN + col * theme.SQUARE
    y = theme.MARGIN + (7 - row) * theme.SQUARE
    return pygame.Rect(x, y, theme.SQUARE, theme.SQUARE)


def square_at(pos):
    """Casa (row, col) sob o pixel clicado, ou None se for fora do tabuleiro."""
    x, y = pos
    col = (x - theme.MARGIN) // theme.SQUARE
    row = 7 - (y - theme.MARGIN) // theme.SQUARE

    if 0 <= row < 8 and 0 <= col < 8:
        return int(row), int(col)
    return None


def control_at(pos):
    """Controle do menu superior clicado, ou None se não for nenhum."""
    x, y = pos
    if not (0 <= y < theme.MARGIN):
        return None

    col = (x - theme.MARGIN) // theme.SQUARE
    if not (0 <= col < 8):
        return None

    # As colunas sem controle guardam '': viram None em vez de botão.
    return CONTROLS[col] or None


class Renderer:
    """Dono das fontes e do desenho. Só pode ser criado depois de pygame.init()."""

    def __init__(self):
        self.piece_font = pygame.font.SysFont(theme.PIECE_FONT_NAME, theme.PIECE_SIZE)
        self.label_font = pygame.font.SysFont(theme.FONT_NAME, theme.LABEL_SIZE)

    def draw(self, surface, grid, selected=None, targets=()):
        surface.fill(theme.BACKGROUND)
        self._draw_squares(surface, selected)
        self._draw_labels(surface)
        self._draw_controls(surface)
        self._draw_pieces(surface, grid)
        self._draw_targets(surface, grid, targets)

    def _draw_squares(self, surface, selected):
        for row in range(8):
            for col in range(8):
                # Casas claras e escuras se alternam; a1 (0, 0) é escura.
                color = theme.LIGHT if (row + col) % 2 else theme.DARK
                if (row, col) == selected:
                    color = theme.SELECTED
                pygame.draw.rect(surface, color, square_rect(row, col))

    def _draw_labels(self, surface):
        for col in range(8):
            rect = square_rect(0, col)
            self._blit_centered(surface, self.label_font, "abcdefgh"[col], theme.LABEL,
                                (rect.centerx, rect.bottom + theme.MARGIN // 2))
        for row in range(8):
            rect = square_rect(row, 0)
            self._blit_centered(surface, self.label_font, str(row + 1), theme.LABEL,
                                (rect.left - theme.MARGIN // 2, rect.centery))
            

    def _draw_controls(self, surface):
        
        for col in range(8):
            rect = square_rect(7, col)
            self._blit_centered(surface, self.label_font, CONTROLS[col], theme.LABEL,
                                (rect.centerx, rect.top // 2))
        

    def _draw_pieces(self, surface, grid):
        for row in range(8):
            for col in range(8):
                piece = grid[row][col]
                if piece is None:
                    continue

                self._draw_piece(surface, piece, square_rect(row, col).center)

    def _draw_piece(self, surface, piece, center):
        """Glifo na cor do lado, contorno na cor oposta: o que separa branca de preta."""
        fill = theme.WHITE_PIECE if piece.isupper() else theme.BLACK_PIECE
        outline = theme.BLACK_PIECE if piece.isupper() else theme.WHITE_PIECE

        glyph = GLYPH[piece.upper()]
        # O contorno é o mesmo glifo repetido em volta, e o preenchimento por cima.
        for dx, dy in OFFSETS:
            self._blit_glyph(surface, self.piece_font, glyph, outline,
                             (center[0] + dx * theme.OUTLINE, center[1] + dy * theme.OUTLINE))
        self._blit_glyph(surface, self.piece_font, glyph, fill, center)

    def _draw_targets(self, surface, grid, targets):
        for row, col in targets:
            rect = square_rect(row, col)
            piece = grid[row][col]
            if piece is None:
                pygame.draw.circle(surface, theme.TARGET_DARK, rect.center, theme.DOT_RADIUS)
                continue

            # Captura: anel em volta da peça, para não escondê-la. A cor
            # acompanha a peça, senão o anel some sobre a peça preta.
            color = theme.TARGET_DARK if piece.isupper() else theme.TARGET_LIGHT
            pygame.draw.circle(surface, color, rect.center,
                               theme.SQUARE // 2 - theme.RING_WIDTH // 2, theme.RING_WIDTH)

    @staticmethod
    def _blit_centered(surface, font, text, color, center):
        image = font.render(text, True, color)
        surface.blit(image, image.get_rect(center=center))

    @staticmethod
    def _blit_glyph(surface, font, glyph, color, center):
        """Centra pelo desenho, e não pela caixa: o glifo tem folga em cima e embaixo."""
        image = font.render(glyph, True, color)
        ink = image.get_bounding_rect()
        surface.blit(image, (center[0] - ink.centerx, center[1] - ink.centery))
