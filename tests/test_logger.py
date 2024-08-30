import pytest
from logger.custom_logger import get_logger

def test_get_logger():
    logger = get_logger(__file__)
    assert logger is not None
    assert logger.name == "test_logger"