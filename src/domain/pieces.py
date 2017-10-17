import re
from abc import ABCMeta, abstractmethod
from string import ascii_lowercase
from typing import Union, Tuple, List, Optional, Iterator

location_regex = re.compile(r'^(?P<file>[a-zA-Z]+)(?P<rank>[0-9]+)$')


class Side(metaclass=ABCMeta):
    @property
    @abstractmethod
    def name(self) -> str:
        """return defined side name"""
        pass

    @property
    @abstractmethod
    def char(self) -> str:
        """return defined one-char side name"""
        pass

    @property
    @abstractmethod
    def capitalize(self) -> bool:
        """
        Return True if Piece char representation should be capitalized
        Should be implemented only for FEN boards representation purpose
        """
        pass

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, Side):
            return self.name == other.name


class Piece(metaclass=ABCMeta):
    def __init__(self, side: Side):
        self.__side = side

    @property
    @abstractmethod
    def name(self) -> str:
        """return piece name starts with uppercase, eg. Pawn"""
        pass

    @property
    @abstractmethod
    def char(self) -> str:
        """return one lowercase letter representation of piece, eg. p"""
        pass

    @property
    @abstractmethod
    def points(self) -> int:
        """return int piece value representation, eg. 1"""
        pass

    @property
    def side(self) -> Side:
        return self.__side

    def __repr__(self):
        return '%s %s' % (self.side, self.name)

    def __str__(self):
        return self.char.upper() if self.side.capitalize else self.char.lower()

    def __eq__(self, other):
        if isinstance(other, Piece):
            return isinstance(other, type(self)) and other.side == self.side

    def __ne__(self, other):
        if isinstance(other, Piece):
            return not (isinstance(other, type(self)) and other.side == self.side)
        return True


class Position(metaclass=ABCMeta):
    def __repr__(self):
        return '<Position: %s>' % self

    @abstractmethod
    def __str__(self):
        """Should be implemented for converting position to string purpose if possible, eg. 'e4'"""
        pass

    @abstractmethod
    def __iter__(self):
        """Should be implemented for converting to sequence purpose where first value is a X coordinate, second Y etc."""
        pass

    @abstractmethod
    def __getitem__(self, item):
        """Should be implemented for index access purpose (object[index]). 0 for X, 1 for Y, 2 for Z etc."""
        pass


class StandardPosition(Position):
    """
    tuple with two board coordinates is too simple of course, here is a standard 2D Position object implementation.
    """

    def __init__(self, pos: Union[str, Tuple[int, int], List[int]]):  # TODO: decide to support stable and one interface
        if isinstance(pos, tuple) or isinstance(pos, list):
            if len(pos) != 2:
                raise ValueError('Position should be given as tuple/list with only two ints')
            self.__file = pos[0]
            self.__rank = pos[1]
        elif isinstance(pos, str):
            output = location_regex.search(pos)
            if not output:
                raise ValueError('Position should be given as two letter coordinates (file, rank)')
            self.__rank = self.__rank_from_str_to_int(output.group('rank'))
            self.__file = self.__file_from_str_to_int(output.group('file'))

    @property
    def file(self) -> int:
        return self.__file

    @property
    def rank(self) -> int:
        return self.__rank

    @staticmethod
    def __rank_from_str_to_int(rank: str) -> int:
        """
        Converting rank from standard string format to internal int value (starts from 0 instead of 1),
        eg. 1 in standard string means 0 in internal int format (value is a second part of position, eg "a1")
        """
        return int(rank) - 1

    @staticmethod
    def __rank_from_int_to_str(rank: int) -> str:
        """
        Converting rank from internal value to standard string format (starts from 1 instead of 0),
        eg. 0 in internal int means 1 in standard string format (value is a second part of position, eg "a1")
        """
        return str(rank + 1)

    @staticmethod
    def __file_from_str_to_int(rank: str) -> int:
        """
        Converting file from standard string format to internal int value,
        eg. "A" means 0, "B": 1, "Z": 25, "BA": 26 (Note: 26 == "BA", not "AA" because "A" and "AA" is an equal value,
        just like 01 == 1 in decimal system)
        """
        # Warning, my own, not very well tested implementation of base26 converter
        values = []
        for letter in rank:
            values.append(ascii_lowercase.index(letter.lower()))
        index_value = 0
        counter = 0
        for value in reversed(values):
            if counter < 1:
                index_value += value
            else:
                index_value += (value * 26) ** counter
            counter += 1
        return index_value

    @staticmethod
    def __file_from_int_to_str(file: int) -> str:
        """
        Converting file from internal int value to standard string format,
        eg. 0 means "A", 1: "B", 25: "Z", 26: "BA" (Note: 26 == "BA", not "AA" because "A" and "AA" is an equal value,
        just like 01 == 1 in decimal system)
        """
        # Warning, my own, not very well tested implementation of base26 converter
        output_chars = 1
        while (len(ascii_lowercase)) ** output_chars <= file:
            output_chars += 1
        values = []
        for i in range(output_chars):
            val = (file // len(ascii_lowercase) ** i) % (len(ascii_lowercase))
            values.append(val)

        return "".join(ascii_lowercase[x] for x in reversed(values))

    def __str__(self):
        return '%s%s' % (self.__file_from_int_to_str(self.file),
                         self.__rank_from_int_to_str(self.rank))

    def __iter__(self) -> Iterator[int]:
        for coordinate in (self.file, self.rank):
            yield coordinate

    def __getitem__(self, item) -> int:
        if item == 0:
            return self.file
        elif item == 1:
            return self.rank
        else:
            raise IndexError("tuple index out of range")


class Move:  # TODO: Next to abstract? fix constructor
    """
    Two Position aggregator with optional pawn promotion information
    """

    def __init__(self, a: StandardPosition, b: StandardPosition, promotion: Optional[Piece] = None):
        self.__a = a
        self.__b = b
        self.__promotion = promotion

    @property
    def a(self):
        return self.__a

    @property
    def b(self):
        return self.__b

    @property
    def promotion(self):
        return self.__promotion

    def __repr__(self):
        if self.__promotion:
            return 'Move: %s to %s with promotion to %s' % (self.__a, self.__b, self.__promotion.name)
        else:
            return 'Move: %s to %s' % (self.__a, self.__b)

    def __str__(self):
        if self.__promotion:
            return '%s%s%s' % (self.__a, self.__b, self.__promotion.char)
        else:
            return '%s%s' % (self.__a, self.__b)
