import pytest
from datetime import datetime, timedelta
from utils.calculation.time import calculate_start_time

def test_calculate_start_time():
    timeframe = '1y'
    data_points_back = 1
    expected_start_time = datetime.now() - timedelta(days=365)
    assert calculate_start_time(timeframe, data_points_back).date() == expected_start_time.date()

    timeframe = '1d'
    expected_start_time = datetime.now() - timedelta(days=1)
    assert calculate_start_time(timeframe, data_points_back).date() == expected_start_time.date()

    timeframe = '1h'
    expected_start_time = datetime.now() - timedelta(hours=1)
    assert calculate_start_time(timeframe, data_points_back).hour == expected_start_time.hour

    timeframe = '1m'
    expected_start_time = datetime.now() - timedelta(minutes=1)
    assert calculate_start_time(timeframe, data_points_back).minute == expected_start_time.minute