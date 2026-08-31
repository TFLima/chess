from notation import coords, square, parse_fen
from state import Status, Draw
from board import Board
from pieces import Side
from history import History
from moves import legal_moves, make_move, is_in_check, find_king

class Game:
    
    board: Board
    status: Status
    legal_moves: dict
    history: History
    checked: tuple | None

    # Casas iniciais das torres e o direito de roque que cada uma sustenta.
    CASTLE_BY_SQUARE = {(0, 0): 'Q', (0, 7): 'K', (7, 0): 'q', (7, 7): 'k'}
    
    def __init__(self, fen: str | None = None):
        self.history = History()
        self.status, self.board = self._setup(fen)
        self.legal_moves = legal_moves(self.board, self.status)
        self._can_continue()
        self.checked = None


    def _setup(self, fen: str | None):
        """Posição inicial padrão, ou a posição descrita pelo FEN."""
        if fen is None:
            return Status(), self._initialize_board()

        grid, status = parse_fen(fen)
        board = Board()
        for row in range(Board.SIZE):
            for col in range(Board.SIZE):
                if grid[row][col] is not None:
                    board.place(grid[row][col], row, col)

        return status, board
        
        
    def _initialize_board(self):
        
        board = Board()
        #Pretas
        board.place("r", *coords("a8"))
        board.place("n", *coords("b8"))
        board.place("b", *coords("c8"))
        board.place("q", *coords("d8"))
        board.place("k", *coords("e8"))
        board.place("b", *coords("f8"))
        board.place("n", *coords("g8"))
        board.place("r", *coords("h8"))
        board.place("p", *coords("a7"))
        board.place("p", *coords("b7"))
        board.place("p", *coords("c7"))
        board.place("p", *coords("d7"))
        board.place("p", *coords("e7"))
        board.place("p", *coords("f7"))
        board.place("p", *coords("g7"))
        board.place("p", *coords("h7"))
        #Brancas
        board.place("R", *coords("a1"))
        board.place("N", *coords("b1"))
        board.place("B", *coords("c1"))
        board.place("Q", *coords("d1"))
        board.place("K", *coords("e1"))
        board.place("B", *coords("f1"))
        board.place("N", *coords("g1"))
        board.place("R", *coords("h1"))
        board.place("P", *coords("a2"))
        board.place("P", *coords("b2"))
        board.place("P", *coords("c2"))
        board.place("P", *coords("d2"))
        board.place("P", *coords("e2"))
        board.place("P", *coords("f2"))
        board.place("P", *coords("g2"))
        board.place("P", *coords("h2"))
        
        return board     
    
    
    def next_turn(self):
        self.status.side = Side.BLACK if self.status.side == Side.WHITE else Side.WHITE
        self.checked = self._checked_king()
        if self.status.side == Side.WHITE:
            self.status.move = self.status.move + 1
        self.legal_moves = legal_moves(self.board, self.status)        
        self._can_continue()
        
        
    def play(self, orig: str, dest: str, promotion: str = 'q'):
        
        if self.status.finished:
            raise SystemError("Partida finalizada!")
        
        c_orig = coords(orig)
        c_dest = coords(dest)

        destinations = self.legal_moves.get(c_orig)
        if destinations is None:
            raise ValueError("Posição de origem inválida")

        if c_dest not in destinations:
            raise ValueError("Posição de destino inválida")
        
        self.history.update(self.board, self.status, orig, dest)

        piece = self.board.get(*c_orig)
        is_pawn = piece in ('P', 'p')
        promoted = self._promoted_piece(piece, c_dest, promotion)
        c_captured = self._ep_captured_square(c_orig, c_dest, dest, is_pawn)

        _, captured = make_move(self.board, c_orig, c_dest, c_captured)
        
        self.status.half_moves = 0 if is_pawn or captured is not None else self.status.half_moves+1
        
        self._after_move(piece, c_orig, c_dest, is_pawn, promoted)              


    def _after_move(self, piece: str, c_orig: tuple[int, int], c_dest: tuple[int, int], is_pawn: bool, promoted: str | None):
        self.status.ep_pawn = None
        self.status.ep_target = None

        if is_pawn:
            if abs(c_dest[0] - c_orig[0]) == 2:
                self.status.ep_pawn = square(*c_dest)
                step = -1 if piece == 'P' else 1
                self.status.ep_target = square(c_dest[0] + step, c_dest[1])
            elif promoted is not None:
                self.board.place(promoted, *c_dest)

        if piece in ('K', 'k'):
            self._revoke_castle('KQ' if piece == 'K' else 'kq')
            if abs(c_dest[1] - c_orig[1]) == 2:
                self._move_castle_rook(c_dest)

        self._revoke_castle(self.CASTLE_BY_SQUARE.get(c_orig, ''))
        self._revoke_castle(self.CASTLE_BY_SQUARE.get(c_dest, ''))
        self.next_turn()

    def _promoted_piece(self, piece: str, c_dest: tuple[int, int], promotion: str):
        if piece not in ('P', 'p') or c_dest[0] not in (0, 7):
            return None
        return self._promoted(piece, promotion)

    def _ep_captured_square(self, c_orig: tuple[int, int], c_dest: tuple[int, int], dest: str, is_pawn: bool):
        if not is_pawn:
            return None

        if dest != self.status.ep_target or c_dest[1] == c_orig[1]:
            return None

        return coords(self.status.ep_pawn)


    def _revoke_castle(self, rights: str):
        """Remove os direitos de roque informados, um caractere por vez."""
        for right in rights:
            self.status.castle = self.status.castle.replace(right, '')


    def _move_castle_rook(self, c_king_dest):
        """Completa o roque movendo a torre do lado correspondente."""
        row, col = c_king_dest
        match col:
            case 2:
                rook_orig, rook_dest = (row, 0), (row, 3)
            case 6:
                rook_orig, rook_dest = (row, 7), (row, 5)
            case _:
                raise ValueError("Torre não encontrada")

        make_move(self.board, rook_orig, rook_dest)     


    def _promoted(self, pawn: str, promotion: str):
        """Peça escolhida na promoção, no caso (maiúscula/minúscula) do peão."""
        if promotion.lower() not in ('q', 'r', 'b', 'n'):
            raise ValueError(f"Peça de promoção inválida: {promotion!r}")

        return promotion.upper() if pawn == 'P' else promotion.lower()


    def will_promote(self, orig: str, dest: str):
        c_orig = coords(orig)
        c_dest = coords(dest)

        destinations = self.legal_moves.get(c_orig)
        if destinations is None or c_dest not in destinations:
            return False
        
        piece = self.board.get(*c_orig)
        if piece not in ('P', 'p'):
            return False
        
        final_row = 7 if piece == 'P' else 0        
        row, _ = c_dest
        
        return row == final_row
 
                    
    def _can_continue(self):
        # Encadeado: o mate tem precedência sobre qualquer critério de empate.
        if not self.legal_moves:
            if is_in_check(self.board, self.status.side):
                self.status.check_mate = Side.WHITE if self.status.side is Side.BLACK else Side.BLACK
            else:
                self.status.draw = Draw.stalemate
            self.status.finished = True

        elif self.status.half_moves >= 100:
            self.status.draw = Draw.fiftymoves
            self.status.finished = True

        elif self._insufficient_material():
            self.status.draw = Draw.material
            self.status.finished = True

        # A posição atual ainda não está no histórico: 2 registros + a atual = tripla repetição.
        elif self.history.find_position(repr(self.board), self.status) >= 2:
            self.status.draw = Draw.repeated
            self.status.finished = True

        if self.status.finished:
            self.history.update(self.board, self.status)
        
        
    def _insufficient_material(self):
        pieces = self._material_pieces()
        if pieces is None:
            return False

        if len(pieces) <= 3:
            return True

        bishops = [sq_color for piece, sq_color in pieces if piece in ('B', 'b')]
        return len(bishops) == 2 and bishops[0] == bishops[1]


    def _material_pieces(self):
        """Retorna peças e cores das casas dos bispos, ou None se o material não for insuficiente."""
        pieces = []
        for row in range(self.board.SIZE):
            for col in range(self.board.SIZE):
                piece = self.board.get(row, col)
                if piece is None:
                    continue
                if len(pieces) == 4 or piece.lower() in ('q', 'r', 'p'):
                    return None

                bishop_square = (row + col) % 2 if piece.lower() == 'b' else None
                pieces.append((piece, bishop_square))

        return pieces
                
                
    def _checked_king(self):        
        if is_in_check(self.board, self.status.side):
            return find_king(self.board, self.status.side)   
        return None             