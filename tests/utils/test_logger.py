import logging

from _pytest.logging import LogCaptureFixture

from app.utils.logger import logger


def test_logger_outputs_info_level(caplog: LogCaptureFixture) -> None:
    # Set logger level to INFO and enable caplog capturing
    with caplog.at_level(logging.INFO, logger="backend"):
        logger.info("This is a test log message.")

    # Check that message appears in logs
    assert "This is a test log message." in caplog.text
    assert "INFO" in caplog.text
    assert "backend" in caplog.text


def test_logger_does_not_output_debug_by_default(caplog: LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="backend"):
        logger.debug("This debug message should not appear.")

    assert "This debug message should not appear." not in caplog.text
