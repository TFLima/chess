"""Loop do pygame: traduz cliques em lances. Não desenha e não conhece as regras."""

import pygame  # type: ignore[import-not-found]

from game import Game
from replay import Replay
from notation import square
from pieces import Side
from ui import theme
from ui.render import Renderer, square_at, control_at

FPS = 60


class App:

    def __init__(self, game: Game | None = None):
        self.game = game if game is not None else Game()
        self.selected: tuple[int, int] | None = None
        self.replay = None
        self.message: str | None = None
        self.dialog: dict | None = None  # {'title': str, 'options': list, 'callback': func}
        self.dialog_rects: list = []
        self.dialog_hover: int | None = None
        self.promotion = None

    def run(self):
        pygame.init()
        surface = pygame.display.set_mode((theme.WIDTH, theme.HEIGHT))
        renderer = Renderer()
        clock = pygame.time.Clock()

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.click(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    self._update_hover(event.pos)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._dismiss()
            
            pygame.display.set_caption(f"Xadrez — {self.caption()}")
            self.draw(surface, renderer)
            pygame.display.flip()
            clock.tick(FPS)

        pygame.quit()                       
        

    def draw(self, surface, renderer: Renderer):
        if self.replay is None:
            renderer.draw(surface, self.game.board.grid, self.game.checked, self.selected, self.targets())
        else:
            renderer.draw(surface, self.replay.board.grid, self.replay.checked)

        if self.message:
            renderer.draw_message(surface, self.message)
        elif self.dialog:
            self.dialog_rects = renderer.draw_dialog(
                surface, self.dialog['title'], self.dialog['options'], self.dialog_hover)


    def click(self, pos):
        if self.message:
            self.message = None
            return

        if self.dialog:
            self._dialog_clicked(pos)
            return

        casa = square_at(pos)
        if casa is not None and self.replay is None:
            self._board_clicked(casa)
        else:
            control = control_at(pos)
            if control is not None:
                self._control_clicked(control)
                

    def _board_clicked(self, casa):
        """Primeiro clique escolhe a peça; o segundo, num destino válido, joga."""
        if casa in self.targets():
            self.play(self.selected, casa)
        elif casa in self.game.legal_moves:
            self.selected = casa
        else:
            self.selected = None
            
    def _control_clicked(self, control):
        entrando = self.replay is None
        if entrando:
            self.replay = Replay(self.game)

        match control:
            case '<':
                self.replay.back()
            case '>':
                self.replay.next()
            case '<<':
                self.replay.first()
            case '>>':
                self.replay.last()

        # Voltar ao fim do histórico é voltar ao 'agora': o replay sai de cena.
        # Na entrada não vale: o cursor já nasce no fim, e '>' sairia sem mostrar nada.
        if not entrando and self.replay.is_end():
            self.replay = None


    def targets(self):
        """Destinos legais da peça selecionada."""
        if self.selected is None:
            return []
        return self.game.legal_moves.get(self.selected, [])

    def play(self, orig, dest):
        # if self.game.will_promote(square(*orig), square(*dest)):
        #     self.show_dialog('Promover peão', ['Dama', 'Torre', 'Bispo', 'Cavalo'], self.choose_promotion)            
        self.game.play(square(*orig), square(*dest))
        self.selected = None
                
    # def choose_promotion(app, index, orig, dest):
    #     options = ['Q','R','B','N']
    #     app.game.play(square(*orig), square(*dest))

    def caption(self):
        if self.replay is not None:
            return f"replay {self.replay.header()} (ESC para voltar)"

        status = self.game.status

        if status.check_mate is not None:
            vencedor = 'brancas' if status.check_mate == Side.WHITE else 'pretas'
            return f"xeque-mate, vitória das {vencedor}"

        if status.draw is not None:
            return f"empate: {status.draw.value}"

        lado = 'brancas' if status.side == Side.WHITE else 'pretas'
        return f"lance {status.move}, jogam as {lado}"

    def show_message(self, text: str):
        """Exibe uma mensagem fixa na tela. Clique para fechar."""
        self.message = text

    def show_dialog(self, title: str, options: list[str], callback):
        """Exibe um diálogo com opções. callback(index) é chamado ao escolher."""
        self.dialog = {'title': title, 'options': options, 'callback': callback}
        self.dialog_hover = None

    def _dialog_clicked(self, pos):
        for i, rect in enumerate(self.dialog_rects):
            if rect.collidepoint(pos):
                callback = self.dialog['callback']
                self.dialog = None
                self.dialog_rects = []
                self.dialog_hover = None
                callback(i)
                return

    def _update_hover(self, pos):
        if not self.dialog:
            return
        self.dialog_hover = None
        for i, rect in enumerate(self.dialog_rects):
            if rect.collidepoint(pos):
                self.dialog_hover = i
                break

    def _dismiss(self):
        """ESC fecha mensagem, diálogo ou replay."""
        if self.message:
            self.message = None
        elif self.dialog:
            self.dialog = None
            self.dialog_rects = []
            self.dialog_hover = None
        else:
            self.replay = None
