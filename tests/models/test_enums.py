import pytest

from app.models.enums import AlertStatus, Location, SeverityLevel, TriState


def test_location_enum() -> None:
    assert Location.TAIPEI.value == "Taipei"
    assert Location("Hsinchu") == Location.HSINCHU
    with pytest.raises(ValueError):
        Location("UnknownCity")


def test_severity_level_enum() -> None:
    assert SeverityLevel.L1 == 1
    assert SeverityLevel(2) == SeverityLevel.L2
    with pytest.raises(ValueError):
        SeverityLevel(3)


def test_tristate_enum() -> None:
    assert TriState.TRUE == 1
    assert TriState.FALSE == 0
    assert TriState.UNKNOWN == -1
    with pytest.raises(ValueError):
        TriState(5)


def test_alert_status_enum() -> None:
    assert AlertStatus.OPEN == "OPEN"
    assert AlertStatus("PROCESSED") == AlertStatus.PROCESSED
    with pytest.raises(ValueError):
        AlertStatus("CLOSED")
