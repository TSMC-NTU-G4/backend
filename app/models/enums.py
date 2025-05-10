from enum import Enum


class Location(str, Enum):
    TAIPEI = "Taipei"
    HSINCHU = "Hsinchu"
    TAICHUNG = "Taichung"
    TAINAN = "Tainan"


class SeverityLevel(int, Enum):
    NA = 0
    L1 = 1
    L2 = 2


class TriState(int, Enum):
    TRUE = 1
    FALSE = 0
    UNKNOWN = -1


class AlertStatus(str, Enum):
    OPEN = "OPEN"
    PROCESSED = "PROCESSED"
    AUTOCLOSED = "AUTOCLOSED"
