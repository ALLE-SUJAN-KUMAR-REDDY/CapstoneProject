import os
import pytest
from utils.excel_utils import read_test_data

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "test_data", "test_data.xlsx")


@pytest.fixture(scope="module")
def oneway_data() -> dict:
    """Load first row from OneWayFlight sheet."""
    records = read_test_data(TEST_DATA_PATH, "OneWayFlight")
    return records[0]


@pytest.fixture(scope="module")
def roundtrip_data() -> dict:
    """Load first row from RoundTripFlight sheet."""
    records = read_test_data(TEST_DATA_PATH, "RoundTripFlight")
    return records[0]
