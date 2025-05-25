from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

import app.services.metrics as metrics
from app.models.earthquake import (
    EarthquakeAlert,
    EarthquakeData,
    EarthquakeEvent,
    ShakingArea,
)
from app.models.enums import AlertStatus, Location, SeverityLevel, TriState


@pytest.fixture
def sample_earthquake_data() -> EarthquakeData:
    return EarthquakeData(
        id=str(uuid4()),
        source="CWB",
        origin_time=datetime.utcnow(),
        magnitude_value=5.2,
        focal_depth=10.0,
        epicenter_location="25.03,121.57",
        shaking_area=[
            ShakingArea(county_name=Location.TAIPEI, area_intensity=3),
            ShakingArea(county_name=Location.TAINAN, area_intensity=2),
        ],
    )


@pytest.fixture
def sample_earthquake_event() -> EarthquakeEvent:
    return EarthquakeEvent(
        id=str(uuid4()),
        source="CWB",
        location=Location.TAIPEI,
        origin_time=datetime.utcnow(),
        severity_level=SeverityLevel.L2,
    )


@pytest.fixture
def sample_earthquake_alert() -> EarthquakeAlert:
    return EarthquakeAlert(
        id=str(uuid4()),
        source="CWB",
        location=Location.TAIPEI,
        origin_time=datetime.utcnow(),
        severity_level=SeverityLevel.L2,
        has_damage=TriState.FALSE,
        needs_command_center=TriState.FALSE,
        processing_duration=120,
        status=AlertStatus.OPEN,
    )


def test_observe_earthquake_data(sample_earthquake_data: EarthquakeData) -> None:
    with (
        patch.object(
            metrics.earthquake_occurrences_total.labels(source="test_source"),
            "inc",
        ) as mock_inc,
        patch.object(
            metrics.earthquake_magnitude.labels(
                source="test_source",
                id="test_id",
                epicenter="test_epicenter",
            ),
            "set",
        ) as mock_mag_set,
        patch.object(
            metrics.earthquake_depth.labels(
                source="test_source",
                id="test_id",
                epicenter="test_epicenter",
            ),
            "set",
        ) as mock_depth_set,
        patch.object(
            metrics.earthquake_intensity.labels(
                source="test_source",
                id="test_id",
                area="test_area",
            ),
            "set",
        ) as mock_intensity_set,
        patch.object(
            metrics.earthquake_occurrences_total,
            "labels",
            return_value=MagicMock(inc=mock_inc),
        ) as labels_counter_mock,
        patch.object(
            metrics.earthquake_magnitude,
            "labels",
            return_value=MagicMock(set=mock_mag_set),
        ) as labels_mag_mock,
        patch.object(
            metrics.earthquake_depth,
            "labels",
            return_value=MagicMock(set=mock_depth_set),
        ) as labels_depth_mock,
        patch.object(
            metrics.earthquake_intensity,
            "labels",
            return_value=MagicMock(set=mock_intensity_set),
        ),
    ):
        metrics.observe_earthquake_data(sample_earthquake_data)

        labels_counter_mock.assert_called_once_with(
            source=sample_earthquake_data.source,
        )
        mock_inc.assert_called_once()

        labels_mag_mock.assert_called_once_with(
            id=str(sample_earthquake_data.id),
            source=sample_earthquake_data.source,
            epicenter=sample_earthquake_data.epicenter_location,
        )
        mock_mag_set.assert_called_once_with(sample_earthquake_data.magnitude_value)

        labels_depth_mock.assert_called_once_with(
            id=str(sample_earthquake_data.id),
            source=sample_earthquake_data.source,
            epicenter=sample_earthquake_data.epicenter_location,
        )
        mock_depth_set.assert_called_once_with(sample_earthquake_data.focal_depth)

        assert mock_intensity_set.call_count == len(sample_earthquake_data.shaking_area)


def test_observe_earthquake_events(sample_earthquake_event: EarthquakeEvent) -> None:
    with (
        patch.object(
            metrics.earthquake_events_total,
            "labels",
            return_value=MagicMock(inc=MagicMock()),
        ) as total_labels_mock,
        patch.object(
            metrics.earthquake_events_severity,
            "labels",
            return_value=MagicMock(set=MagicMock()),
        ) as severity_labels_mock,
    ):
        metrics.observe_earthquake_events([sample_earthquake_event])

        total_labels_mock.assert_called_once_with(source=sample_earthquake_event.source)
        severity_labels_mock.assert_called_once_with(
            id=str(sample_earthquake_event.id),
            source=sample_earthquake_event.source,
            location=sample_earthquake_event.location.value,
        )


def test_observe_earthquake_alerts(sample_earthquake_alert: EarthquakeAlert) -> None:
    with (
        patch.object(
            metrics.earthquake_alerts_total,
            "labels",
            return_value=MagicMock(inc=MagicMock()),
        ) as total_labels_mock,
        patch.object(
            metrics.earthquake_alerts_damage,
            "labels",
            return_value=MagicMock(set=MagicMock()),
        ) as damage_labels_mock,
        patch.object(
            metrics.earthquake_alerts_command_center,
            "labels",
            return_value=MagicMock(set=MagicMock()),
        ) as cmd_labels_mock,
        patch.object(
            metrics.earthquake_alerts_processing_duration,
            "labels",
            return_value=MagicMock(set=MagicMock()),
        ) as proc_labels_mock,
    ):
        metrics.observe_earthquake_alerts([sample_earthquake_alert])

        total_labels_mock.assert_called_once_with(source=sample_earthquake_alert.source)

        for mock_labels, expected_value in [
            (damage_labels_mock, sample_earthquake_alert.has_damage.value),
            (cmd_labels_mock, sample_earthquake_alert.needs_command_center.value),
            (proc_labels_mock, sample_earthquake_alert.processing_duration),
        ]:
            mock_labels.assert_called_once_with(
                id=str(sample_earthquake_alert.id),
                source=sample_earthquake_alert.source,
                location=sample_earthquake_alert.location.value,
                origin_time=sample_earthquake_alert.origin_time.isoformat(),
            )
            mock_labels().set.assert_called_once_with(expected_value)


def test_observe_earthquake_alerts_autoclose(
    sample_earthquake_alert: EarthquakeAlert,
) -> None:
    with patch.object(
        metrics.earthquake_alerts_autoclosed_total,
        "labels",
        return_value=MagicMock(inc=MagicMock()),
    ) as autoclosed_total_mock:
        metrics.observe_earthquake_alerts_autoclose(sample_earthquake_alert)

        autoclosed_total_mock.assert_called_once_with(
            source=sample_earthquake_alert.source,
        )
        autoclosed_total_mock().inc.assert_called_once()
