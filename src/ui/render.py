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


def is_light(row, col):
    """Se a casa é clara. As casas se alternam, e a1 (0, 0) é escura."""
    return (row + col) % 2 == 1


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
        self.message_font = pygame.font.SysFont(theme.FONT_NAME, theme.MESSAGE_FONT_SIZE)

    def draw(self, surface, grid, check=None, selected=None, targets=()):
        surface.fill(theme.BACKGROUND)
        self._draw_squares(surface, selected)
        self._draw_labels(surface)
        self._draw_controls(surface)
        self._draw_pieces(surface, grid)
        self._draw_targets(surface, grid, targets)
        self._draw_check(surface, grid, check)

    def _draw_squares(self, surface, selected):
        for row in range(8):
            for col in range(8):
                color = theme.LIGHT if is_light(row, col) else theme.DARK
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

            # Captura: anel na borda da casa, para não esconder a peça. Por isso
            # a cor acompanha a casa, e não a peça: sobre a casa é que ele precisa
            # aparecer.
            color = theme.TARGET_DARK if is_light(row, col) else theme.TARGET_LIGHT
            pygame.draw.circle(surface, color, rect.center,
                               theme.SQUARE // 2 - theme.RING_WIDTH // 2, theme.RING_WIDTH)
            
            
    def _draw_check(self, surface, grid, check):
        if check is not None:
            row, col = check
            king = grid[row][col]
            if king is None or king.upper() != 'K':
                return
            rect = square_rect(row, col)
            pygame.draw.circle(surface, theme.TARGET_RED, rect.center,
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

    def draw_message(self, surface, text):
        """Desenha uma mensagem fixa centralizada na tela."""
        center = (theme.WIDTH // 2, theme.HEIGHT // 2)
        padding = theme.MESSAGE_PADDING

        text_surface = self.message_font.render(text, True, theme.MESSAGE_TEXT)
        text_rect = text_surface.get_rect(center=center)

        bg_rect = text_rect.inflate(padding * 2, padding * 2)
        pygame.draw.rect(surface, theme.MESSAGE_BG, bg_rect, border_radius=6)
        pygame.draw.rect(surface, theme.MESSAGE_BORDER, bg_rect, width=2, border_radius=6)

        surface.blit(text_surface, text_rect)

    def draw_dialog(self, surface, title, options, hover_index=None):
        """Desenha um diálogo com opções clicáveis. Retorna lista de rects das opções."""
        center_x = theme.WIDTH // 2
        center_y = theme.HEIGHT // 2
        padding = theme.MESSAGE_PADDING
        option_height = theme.MESSAGE_FONT_SIZE + padding
        spacing = 8

        # Renderiza título e opções para calcular largura
        title_surface = self.message_font.render(title, True, theme.MESSAGE_TEXT)
        option_surfaces = [self.message_font.render(opt, True, theme.MESSAGE_TEXT) for opt in options]

        max_width = max(title_surface.get_width(), max(s.get_width() for s in option_surfaces))
        dialog_width = max_width + padding * 4

        # Altura total: título + espaço + opções
        total_height = (title_surface.get_height() + padding * 2 +
                        len(options) * option_height + (len(options) - 1) * spacing + padding)

        # Fundo do diálogo
        dialog_rect = pygame.Rect(0, 0, dialog_width, total_height)
        dialog_rect.center = (center_x, center_y)
        pygame.draw.rect(surface, theme.MESSAGE_BG, dialog_rect, border_radius=8)
        pygame.draw.rect(surface, theme.MESSAGE_BORDER, dialog_rect, width=2, border_radius=8)

        # Título
        title_rect = title_surface.get_rect(centerx=center_x, top=dialog_rect.top + padding)
        surface.blit(title_surface, title_rect)

        # Opções
        option_rects = []
        y = title_rect.bottom + padding
        for i, (opt_surface, opt_text) in enumerate(zip(option_surfaces, options)):
            opt_rect = pygame.Rect(dialog_rect.left + padding, y,
                                   dialog_width - padding * 2, option_height)

            bg_color = theme.DIALOG_OPTION_HOVER if i == hover_index else theme.DIALOG_OPTION_BG
            pygame.draw.rect(surface, bg_color, opt_rect, border_radius=4)

            text_pos = opt_surface.get_rect(center=opt_rect.center)
            surface.blit(opt_surface, text_pos)

            option_rects.append(opt_rect)
            y += option_height + spacing

        return option_rects
