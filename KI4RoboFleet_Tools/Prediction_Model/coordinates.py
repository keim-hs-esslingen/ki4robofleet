class Coordinates:
    def __init__(self, lat: float, lon: float):
        self.__lat = lat
        self.__lon = lon

    @classmethod
    def from_tuple(cls, coords: tuple):
        return cls(coords[0], coords[1])

    def __str__(self):
        return f"Coordinates(lat={self.__lat}, lon={self.__lon})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return repr(self) == repr(other)

    def __call__(self):
        return (self.__lat, self.__lon)

    def lat(self):
        return self.__lat

    def lon(self):
        return self.__lon