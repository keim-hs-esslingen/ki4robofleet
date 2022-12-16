class Sector:
    def __init__(self, row: int, col: int):
        self.__row = int(row)
        self.__col = int(col)

    @classmethod
    def from_tuple(cls, sector: tuple):
        return cls(sector[0], sector[1])

    def __str__(self):
        return f"Sector(row={self.__row}, col={self.__col})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return repr(self) == repr(other)

    def row(self):
        return self.__row

    def col(self):
        return self.__col