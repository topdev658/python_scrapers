from typing import Tuple


class Tile:
    def __init__(self, xy: Tuple[int, int]):
        self.xy = xy

    def __repr__(self):
        return str("Tile{}".format(self.xy))

    def __hash__(self):
        return self.xy.__hash__()

    def __eq__(self, other):
        return self.xy == other.xy
