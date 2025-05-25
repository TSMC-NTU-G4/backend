from app.models.settings import Settings


def test_settings_model() -> None:
    settings = Settings(alert_suppress_time=30)
    assert settings.alert_suppress_time == 30

    # Test camelCase serialization if alias generator is used
    dumped = settings.model_dump(by_alias=True)
    assert "alertSuppressTime" in dumped
    assert dumped["alertSuppressTime"] == 30
