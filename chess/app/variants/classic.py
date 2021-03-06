import itertools
from collections import defaultdict
from copy import deepcopy
from math import inf as infinity
from typing import List, Dict, Optional, Set, Type, Tuple, TYPE_CHECKING

from chess.app.board import StandardBoard
from chess.app.move import StandardMove
from chess.app.pieces import King, Queen, Rook, Bishop, Knight, Pawn
from chess.app.position import StandardPosition
from chess.app.sides import White, Black
from chess.exceptions.variant import NoPiece, NotAValidMove, CausesCheck, NotAValidPromotion, WrongMoveOrder
from chess.interface.variant import Variant

if TYPE_CHECKING:
    from chess.interface.piece import Piece
    from chess.interface.side import Side


class Normal(Variant):
    """
    This is a base classic chess implementation, it could be inherited to implement similar chess variants
    """

    def __init__(self, init_board_state: bool = True):
        self.__board = StandardBoard()
        if init_board_state:
            self.init_board_state()

        self.__half_moves: int = 1
        self.__moves_history: List['StandardMove'] = []
        self.__board_history = []
        self.__position_occurence: Dict[int] = defaultdict(int)
        self.__en_passant: Optional[StandardPosition] = None
        self.__half_moves_since_pawn_moved: int = 0
        self.__half_moves_since_capture: int = 0
        self.__castling: Set['Side'] = {piece(side) for side in self.sides for piece in (King, Queen)}
        self.__pocket: Dict[Type['Side'], List[Type['Piece']]] = {side: [] for side in self.sides}

    @property
    def name(self) -> str:
        """
        return Variant name
        """
        return "Classic Chess"

    @property
    def en_passant(self) -> Optional[StandardPosition]:
        """
        return en passant position
        """
        return self.__en_passant

    @property
    def half_moves(self) -> int:
        """
        return half-move counter value, starts from 1 and increments with every side move
        """
        return self.__half_moves

    @property
    def moves(self) -> int:
        """
        return full-move counter value, starts from 1 and increments with every first player move (white in that case)
        """
        return (self.__half_moves + 1) // len(self.sides)

    @property
    def moves_history(self) -> List['StandardMove']:
        """
        return list of executed moves during the game
        """
        return self.__moves_history

    @property
    def on_move(self) -> Type['Side']:
        """
        return side which is actually on the move
        """
        return self.sides[(self.__half_moves - 1) % len(self.sides)]

    @property
    def pocket(self) -> Dict[Type['Side'], List[Type['Piece']]]:
        """
        return dict where key is a side and value is a list of captured pieces by that side
        """
        return self.__pocket

    @property
    def board(self) -> StandardBoard:
        """
        return board object which are holding pieces positions
        """
        return self.__board

    @property
    def sides(self) -> List[Type['Side']]:
        """
        return ordered list of sides, order of list means order of executing moves in the game
        """
        return [White, Black]

    @property
    def pieces(self) -> Set[Type['Piece']]:
        # TODO: not used, to remove or something
        return {King, Queen, Rook, Bishop, Knight, Pawn}

    @property
    def is_check(self) -> bool:
        """
        returns if current, on move player is in check
        """
        # TODO: return all pieces and positions which causes check
        pos, king = self.board.find_pieces(King(self.on_move))[0]
        if pos in self.attacked_fields_by_sides(set(self.sides) - {self.on_move}):
            return True
        return False

    @property
    def last_move(self) -> Optional['StandardMove']:
        """
        return last executed move from move history
        """
        # TODO: useless when full history can be read directly?
        try:
            return self.moves_history[-1]
        except IndexError:
            return None

    @property
    def game_state(self) -> Tuple[Optional[Set[Type['Side']]], Optional[str]]:
        """
        return tuple where first element is an optional set of winning sides (if is there more than one that meanse
        these players get a draw). and second element is an optional verdict explanation
        """
        pieces = {piece for _, piece in self.board.pieces}
        if len(pieces) < 4:
            if pieces == {King(White), King(Black)}:
                return set(self.sides), 'insufficient material'
            if pieces == {King(White), King(Black), Knight(White)} and not self.can_i_make_a_move():
                return set(self.sides), 'insufficient material'
            if pieces == {King(White), King(Black), Knight(Black)} and not self.can_i_make_a_move():
                return set(self.sides), 'insufficient material'
            if pieces == {King(White), King(Black), Bishop(White)} and not self.can_i_make_a_move():
                return set(self.sides), 'insufficient material'
            if pieces == {King(White), King(Black), Bishop(Black)} and not self.can_i_make_a_move():
                return set(self.sides), 'insufficient material'

        if self.__half_moves_since_pawn_moved >= 50 and self.__half_moves_since_capture >= 50:
            return set(self.sides), 'fifty-move rule'
        for hash_pos, occurence in self.__position_occurence.items():
            if occurence >= 3:
                return set(self.sides), 'threefold repetition'
        if not self.can_i_make_a_move():
            king_pos, _ = self.board.find_pieces(King(self.on_move))[0]
            if king_pos in self.attacked_fields_by_sides(set(self.sides) - {self.on_move}):
                return set(self.sides) - {self.on_move}, 'check mate'
            else:
                return set(self.sides), 'stalemate'
        return None, None

    def init_board_state(self):
        """
        Set board start position for classic chess variant
        """
        self.board.put_piece(piece=Rook(White), position=StandardPosition((0, 0)))
        self.board.put_piece(piece=Rook(White), position=StandardPosition((7, 0)))
        self.board.put_piece(piece=Knight(White), position=StandardPosition((1, 0)))
        self.board.put_piece(piece=Knight(White), position=StandardPosition((6, 0)))
        self.board.put_piece(piece=Bishop(White), position=StandardPosition((2, 0)))
        self.board.put_piece(piece=Bishop(White), position=StandardPosition((5, 0)))
        self.board.put_piece(piece=Queen(White), position=StandardPosition((3, 0)))
        self.board.put_piece(piece=King(White), position=StandardPosition((4, 0)))

        for i in range(8):
            self.board.put_piece(piece=Pawn(White), position=StandardPosition((i, 1)))

        for i in range(8):
            self.board.put_piece(piece=Pawn(Black), position=StandardPosition((i, 6)))

        self.board.put_piece(piece=Rook(Black), position=StandardPosition((0, 7)))
        self.board.put_piece(piece=Rook(Black), position=StandardPosition((7, 7)))
        self.board.put_piece(piece=Knight(Black), position=StandardPosition((1, 7)))
        self.board.put_piece(piece=Knight(Black), position=StandardPosition((6, 7)))
        self.board.put_piece(piece=Bishop(Black), position=StandardPosition((2, 7)))
        self.board.put_piece(piece=Bishop(Black), position=StandardPosition((5, 7)))
        self.board.put_piece(piece=Queen(Black), position=StandardPosition((3, 7)))
        self.board.put_piece(piece=King(Black), position=StandardPosition((4, 7)))

        return self.board.get_fen()

    def assert_move(self, move: 'StandardMove'):
        """
        verify if given move is valid in current game state, proper exception is raised when needed
        """
        source, destination = move.source, move.destination
        piece = self.board.get_piece(source)
        if not piece:
            raise NoPiece("Any piece on %s, you need to move pieces, not an air." % source)
        # check if requested destination field is in available fields generated by game logic
        available_dest = self.standard_moves(source) | self.standard_captures(source) | self.special_moves(source)
        if destination not in available_dest:
            raise NotAValidMove("%s is not a proper move for a %s %s\npositions available for that piece: %s" % (
                move, piece.side, piece.name, ', '.join({str(pos) for pos in available_dest})))
        # create test board for real validations
        test_board = deepcopy(self.board)
        test_piece = test_board.remove_piece(source)  # TODO: test special moves
        test_board.put_piece(test_piece, destination)
        if isinstance(test_piece, Pawn):  # TODO: here is an example of above TODO
            if destination == self.en_passant:
                test_board.remove_piece(StandardPosition((destination.file, source.rank)))
        # test on the copied board if move not causing any self-check
        king_pos, king = test_board.find_pieces(requested_piece=King(self.on_move))[0]
        if king_pos in self.attacked_fields_by_sides(set(self.sides) - {piece.side}, test_board):
            raise CausesCheck("{move} move causes {side} {name} ({pos}) check delivered by: [{atck}]".format(
                move=move, side=king.side, name=king.name, pos=king_pos,
                atck=', '.join(
                    ["%s: %s" % (position, '%s %s' % (piece.side, piece.name))
                     for position, piece
                     in self.who_can_step_here(king_pos, test_board).items()]
                )
            ))
        # simple validation when promotion was declared for promoted pawn
        if isinstance(piece, Pawn) and destination.rank in (7, 0):
            if not move.promotion:
                raise NotAValidPromotion("Proper promotion are required when promoting a pawn")

    def move(self, move: 'StandardMove') -> Optional['Piece']:
        """
        try to execute given move, return captured piece if not fails
        """
        self.assert_move(move)
        source, destination = move.source, move.destination
        moved_piece = self.board.get_piece(position=source)
        if moved_piece.side != self.on_move:
            raise WrongMoveOrder("You are trying to move %s when %s are on move" % (moved_piece.side, self.on_move))
        # move are accepted by the game logic, all below concerns game state (counters, history, proper move execution)
        self.save_history()
        moved_piece = self.board.remove_piece(position=source)
        taken_piece = self.board.put_piece(piece=moved_piece, position=destination)
        if isinstance(moved_piece, Pawn):
            if destination == self.en_passant:  # check if en passant move was involved
                taken_piece = self.board.remove_piece(StandardPosition((destination.file, source.rank)))

            # check if pawn was pushed by two fields, set needed en passant position if so
            if abs(source.rank - destination.rank) == 2:
                self.__en_passant = StandardPosition(
                    (source.file,
                     int((source.rank + destination.rank) / 2))
                )
            else:  # clear en passant position on any other pawn-move
                self.__en_passant = None
            self.__half_moves_since_pawn_moved = 0

            if destination.rank in (7, 0):  # handle promotion
                self.board.put_piece(move.promotion(self.on_move), destination)

        else:  # clear en passant position on any other piece-move
            if self.__en_passant:
                self.__en_passant = None
            self.__half_moves_since_pawn_moved += 1

        # simple and ugly check for castling execution
        if isinstance(moved_piece, King) and abs(source.file - destination.file) == 2:
            rank = source.rank
            if move.destination.file == 6:  # king-castle
                moved_rook = self.board.remove_piece(position=StandardPosition((7, rank)))
                self.board.put_piece(moved_rook, StandardPosition((5, rank)))
            elif destination.file == 2:  # queen-castle
                moved_rook = self.board.remove_piece(position=StandardPosition((0, rank)))
                self.board.put_piece(moved_rook, StandardPosition((3, rank)))

        if not taken_piece:
            self.__half_moves_since_capture += 1
        else:
            self.__half_moves_since_capture = 0
            self.__pocket[self.on_move].append(taken_piece)  # put taken piece to the side pocket!

        self.__update_castling_info(source, destination)
        self.__position_occurence[hash(self.board)] += 1

        self.moves_history.append(move)
        self.__half_moves += 1
        return taken_piece

    def __update_castling_info(self, source, destination):
        """
        simply removes castling ability if given move do so
        """
        if self.__castling:
            if StandardPosition.from_str('e1') in (source,):
                self.__castling = self.__castling - {King(White), Queen(White)}
            elif StandardPosition.from_str('a1') in (source, destination):
                self.__castling = self.__castling - {Queen(White)}
            elif StandardPosition.from_str('h1') in (source, destination):
                self.__castling = self.__castling - {King(White)}

            if StandardPosition.from_str('e8') in (source,):
                self.__castling = self.__castling - {King(Black), Queen(Black)}
            elif StandardPosition.from_str('a8') in (source, destination):
                self.__castling = self.__castling - {Queen(Black)}
            elif StandardPosition.from_str('h8') in (source, destination):
                self.__castling = self.__castling - {King(Black)}

    def save_history(self):
        """
        save complete variant state into history object
        """
        self.__board_history.append(deepcopy(
            (
                self.__board,
                self.__half_moves,
                self.__position_occurence,
                self.__en_passant,
                self.__half_moves_since_pawn_moved,
                self.__half_moves_since_capture,
                self.__castling,
            )
        ))

    def load_history(self, offset: int):
        """
        Back in time and recover game state from the past
        """
        index = self.half_moves - offset - 1
        self.__board, \
        self.__half_moves, \
        self.__position_occurence, \
        self.__en_passant, \
        self.__half_moves_since_pawn_moved, \
        self.__half_moves_since_capture, \
        self.__castling = self.__board_history[index]
        for _ in range(offset):
            self.__moves_history.pop()
            self.__board_history.pop()

    def standard_moves(self, position: 'StandardPosition', board: StandardBoard = None) -> Set['StandardPosition']:
        """
        return set of available moves
        """
        if not board:
            board = self.board
        piece = board.get_piece(position)
        if not piece:
            raise NoPiece('Any piece on %s' % position)

        new_positions = set()
        for m_desc in piece.movement.move:
            for vector in self.__transform_vector(m_desc.vector, m_desc.any_direction, piece.side):
                if m_desc.distance is infinity:
                    loop = itertools.count(1)
                else:
                    loop = range(1, m_desc.distance + 1)

                for distance in loop:
                    new_position = StandardPosition(
                        (position[0] + int(vector[0] * distance),
                         position[1] + int(vector[1] * distance))
                    )
                    if not board.validate_position(new_position):
                        break

                    new_piece = board.get_piece(new_position)
                    if new_piece is not None:
                        break
                    new_positions.add(new_position)

        return new_positions

    def special_moves(self, position: 'StandardPosition', board: StandardBoard = None) -> Set['StandardPosition']:
        """
        return set of available special moves (castling and en passant)
        """
        # TODO: replace for some more convenient solution
        if not board:
            board = self.board
        piece = board.get_piece(position)
        if not piece:
            raise NoPiece('Any piece on %s' % position)

        new_positions = set()
        if isinstance(piece, Pawn):
            new_position = None
            if piece == Pawn(Black) and position.rank == 6 and not board.get_piece(
                    StandardPosition((position.file, 5))):
                new_position = StandardPosition(
                    (position.file,
                     position.rank - 2)
                )
            elif piece == Pawn(White) and position.rank == 1 and not board.get_piece(
                    StandardPosition((position.file, 2))):
                new_position = StandardPosition(
                    (position.file,
                     position.rank + 2)
                )
            if new_position and board.validate_position(new_position):
                new_piece = board.get_piece(new_position)
                if new_piece is None:
                    new_positions.add(new_position)

        elif isinstance(piece, King) and self.__castling and position.file == 4:
            attacked_fields = self.attacked_fields_by_sides(set(self.sides) - {self.on_move})

            if King(self.on_move) in self.__castling:
                pos1 = StandardPosition((position.file + 1, position.rank))
                pos2 = StandardPosition((position.file + 2, position.rank))
                if not board.get_piece(pos1) and not board.get_piece(pos2) and not {pos1, pos2} & attacked_fields:
                    new_positions.add(pos2)
            if Queen(self.on_move) in self.__castling:
                pos1 = StandardPosition((position.file - 1, position.rank))
                pos2 = StandardPosition((position.file - 2, position.rank))
                pos3 = StandardPosition((position.file - 2, position.rank))
                if not board.get_piece(pos1) and not board.get_piece(pos2) and not board.get_piece(pos3) \
                        and not {pos1, pos2} & attacked_fields:
                    new_positions.add(pos2)

        return new_positions

    def standard_captures(self, position: 'StandardPosition', board: StandardBoard = None) -> Set['StandardPosition']:
        """
        return set of available captures
        """
        if not board:
            board = self.board
        piece = board.get_piece(position)
        if not piece:
            raise NoPiece('Any piece on %s' % position)

        new_positions = set()
        if isinstance(piece, Pawn) and self.en_passant and self.en_passant in self.attacked_fields(position, board):
            # TODO: move to "special captures" or something
            new_positions.add(self.en_passant)

        for c_desc in piece.movement.capture:
            for vector in self.__transform_vector(c_desc.vector, c_desc.any_direction, piece.side):
                if c_desc.distance is infinity:
                    loop = itertools.count(1)
                else:
                    loop = range(1, c_desc.distance + 1)

                for distance in loop:
                    new_position = StandardPosition(
                        (position[0] + int(vector[0] * distance),
                         position[1] + int(vector[1] * distance))
                    )
                    if not board.validate_position(new_position):
                        break

                    new_piece = board.get_piece(new_position)
                    if not new_piece:
                        continue
                    if new_piece and new_piece.side != piece.side:
                        new_positions.add(new_position)
                        if c_desc.capture_break:
                            break
                    elif new_piece and new_piece.side == piece.side:
                        break

        return new_positions

    def attacked_fields(self, position: 'StandardPosition', board: StandardBoard = None) -> Set['StandardPosition']:
        """
        return set of attacked positions which as coming from given position (piece on that position)
        """
        if not board:
            board = self.board
        piece = board.get_piece(position)
        if not piece:
            raise NoPiece('Any piece on %s' % position)

        new_positions = set()
        for c_desc in piece.movement.capture:
            for vector in self.__transform_vector(c_desc.vector, c_desc.any_direction, piece.side):
                if c_desc.distance is infinity:
                    loop = itertools.count(1)
                else:
                    loop = range(1, c_desc.distance + 1)

                for distance in loop:
                    new_position = StandardPosition(
                        (position[0] + int(vector[0] * distance),
                         position[1] + int(vector[1] * distance))
                    )
                    if not board.validate_position(new_position):
                        break

                    new_piece = board.get_piece(new_position)
                    if not new_piece:
                        new_positions.add(new_position)
                    elif new_piece and new_piece.side != piece.side:
                        new_positions.add(new_position)
                        break
                    elif new_piece and new_piece.side == piece.side:
                        break

        return new_positions

    def attacked_fields_by_sides(self, sides: Set[Type['Side']], board: 'StandardBoard' = None) \
            -> Set['StandardPosition']:
        """
        return attacked positions by the given set of sieds
        """
        if not board:
            board = self.board

        return {pos for position, piece in board.pieces
                for pos in self.attacked_fields(position, board)
                for side in sides if piece.side == side}

    def who_can_step_here(self, position: 'StandardPosition', board: 'StandardBoard' = None) \
            -> Dict['StandardPosition', 'Piece']:
        """
        return dict where key is a position of piece and value is that piece which can move/capture on given position
        """
        if not board:
            board = self.board

        return {pos: piece for pos, piece in board.pieces if position in self.attacked_fields(pos, board)}

    def all_available_moves(self, side: Type['Side'] = None) -> List[StandardMove]:
        """
        return list of all available and validated moves by the current "on move" side, very inefficient.
        """
        if not side:
            side = self.on_move

        moves = set()
        for pos, piece in self.board.pieces:
            if piece.side != side:
                continue
            for destination in self.standard_moves(pos) | self.standard_captures(pos) | self.special_moves(pos):
                move = StandardMove(pos, destination)
                try:
                    self.assert_move(move)
                except NotAValidMove:
                    continue
                else:
                    moves.add(move)
        return list(moves)

    @staticmethod
    def __transform_vector(vector: Tuple[int, int], all_directions: bool, side) -> Set[Tuple[int, int]]:
        """
        return set of vector variants to specify pieces and sides move directions
        """
        # TODO: standard interface for resolving all vector combinations and for transforming not-all-directions vector
        # TODO: eg. a pawn, for Whites move forward means incrementing rank value, for Black - decrementing
        if all_directions:
            return {
                (vector[0], vector[1]),
                (vector[1], vector[0]),
                (vector[1], vector[0] * -1),
                (vector[0], vector[1] * -1),
                (vector[0] * -1, vector[1] * -1),
                (vector[1] * -1, vector[0] * -1),
                (vector[1] * -1, vector[0]),
                (vector[0] * -1, vector[1]),
            }

        if side == Black:
            return {(vector[0] * -1, vector[1] * -1)}
        else:
            return {vector}

    def can_i_make_a_move(self) -> bool:
        """
        return True if some move is available, False if not (duh)
        """
        # TODO: improvement to check if piece that causes check can be captured
        for pos, piece in self.board.pieces:
            if piece and piece.side == self.on_move:
                for moves in [self.standard_captures(pos), self.standard_moves(pos), self.special_moves(pos)]:
                    for dest in moves:
                        try:
                            self.assert_move(StandardMove(pos, dest))
                        except NotAValidMove:
                            continue
                        return True
        return False

    def fen(self):
        """
        return FEN game-state notation
        """
        return str(self)

    def __hash__(self):
        return hash(tuple(self.__moves_history))

    def __str__(self):
        return "{board} {on_move} {castling} {en_passant} {half_since_pawn} {moves}".format(
            board=self.__board.get_fen(),
            on_move=self.on_move.char,
            castling=''.join(sorted((piece.fen for piece in self.__castling))) if self.__castling else "-",
            en_passant=str(self.__en_passant) if self.__en_passant else "-",
            half_since_pawn=min(self.__half_moves_since_pawn_moved, self.__half_moves_since_capture),
            moves=self.moves,
        )
