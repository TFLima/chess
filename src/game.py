from notation import coords, square
from state import Status
from board import Board
from pieces import Side
from moves import legal_moves, make_move, unmake_move

class Game:
    
    board: Board
    status: Status
    legal_moves: dict

    # Casas iniciais das torres e o direito de roque que cada uma sustenta.
    CASTLE_BY_SQUARE = {(0, 0): 'Q', (0, 7): 'K', (7, 0): 'q', (7, 7): 'k'}
    
    def __init__(self):
        self.status = Status()
        self.board = self._initialize_board()                
        self.legal_moves = legal_moves(self.board, self.status)
        
        
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
        self.status.half_move = self.status.side == Side.BLACK
        if self.status.side == Side.WHITE:
            self.status.move = self.status.move + 1
        self.legal_moves = legal_moves(self.board, self.status)
        
        
    def play(self, orig: str, dest: str, promotion: str = 'q'):
        c_orig = coords(orig)
        c_dest = coords(dest)

        destinations = self.legal_moves.get(c_orig)
        if destinations is None:
            raise ValueError("Posição de origem inválida")

        if c_dest not in destinations:
            raise ValueError("Posição de destino inválida")

        piece = self.board.get(*c_orig)
        is_pawn = piece in ('P', 'p')
        promoted = self._promoted_piece(piece, c_dest, promotion)
        c_target = self._en_passant_target(c_orig, c_dest, dest, is_pawn)

        make_move(self.board, c_orig, c_dest, c_target)
        self._after_move(piece, c_orig, c_dest, is_pawn, promoted)

    def _after_move(self, piece: str, c_orig: tuple[int, int], c_dest: tuple[int, int], is_pawn: bool, promoted: str | None):
        self.status.en_passant = None
        self.status.ep_holder = None

        if is_pawn:
            if abs(c_dest[0] - c_orig[0]) == 2:
                self.status.en_passant = square(*c_dest)
                step = -1 if piece == 'P' else 1
                self.status.ep_holder = square(c_dest[0] + step, c_dest[1])
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

    def _en_passant_target(self, c_orig: tuple[int, int], c_dest: tuple[int, int], dest: str, is_pawn: bool):
        if not is_pawn:
            return None

        if dest != self.status.ep_holder or c_dest[1] == c_orig[1]:
            return None

        return coords(self.status.en_passant)


    def _promoted(self, pawn: str, promotion: str):
        """Peça escolhida na promoção, no caso (maiúscula/minúscula) do peão."""
        if promotion.lower() not in ('q', 'r', 'b', 'n'):
            raise ValueError(f"Peça de promoção inválida: {promotion!r}")

        return promotion.upper() if pawn == 'P' else promotion.lower()


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
