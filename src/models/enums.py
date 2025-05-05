from enum import Enum


class Location(str, Enum):
    TAIPEI = "Taipei"
    HSINCHU = "Hsinchu"
    TAICHUNG = "Taichung"
    TAINAN = "Tainan"


class SeverityLevel(str, Enum):
    NA = "NA"
    L1 = "L1"
    L2 = "L2"
