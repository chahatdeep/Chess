from abc import ABCMeta, abstractmethod
from typing import Type, Optional, TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from chess.interface.piece import Piece
    from chess.interface.position import Position


class Board(metaclass=ABCMeta):
    """
    Base board object
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Board type name
        """
        pass

    @property
    @abstractmethod
    def array(self):
        """
        Read-only, direct access to the board array
        :return: n-dimensional array
        """
        pass

    @abstractmethod
    def get_piece(self, position: Type['Position']) -> Optional[Type['Piece']]:
        """
        Get Piece on given Position
        :param position: Position object
        :return: Piece on given Position
        """
        pass

    @abstractmethod
    def put_piece(self, piece, position: Type['Position']) -> Optional[Type['Piece']]:
        """
        Put Piece on given Position
        :param piece: Just any kind of Piece
        :param position: Position object
        :return: Piece that was standing before putting new (None if none)
        """
        pass

    @abstractmethod
    def remove_piece(self, position: Type['Position']) -> Optional[Type['Piece']]:
        """
        Remove Piece from given Position
        :param position: Position object
        :return: Piece that are removed (None if none)
        """
        pass

    @abstractmethod
    def set_fen(self, board_fen: str):
        """
        Sets board state from FEN
        :param board_fen: string, min 15 letters (ranks separated by slash)
        """
        pass

    @abstractmethod
    def get_fen(self) -> str:
        """
        :return: FEN representation of board state
        """
        pass

    @property
    @abstractmethod
    def pieces(self) -> List[Tuple[Type['Position'], Type['Piece']]]:
        """
        :return: a sequence of tuples - (Piece, Position)
        """

    @abstractmethod
    def validate_position(self, position: Type['Position']) -> bool:
        """
        :return: bool, True if given position belongs to dimensions of this board ('eg. a1'), False if not ('eg. z9')
        """

    def __repr__(self):
        return "<%s>" % self.name

    def __str__(self):
        return self.name
