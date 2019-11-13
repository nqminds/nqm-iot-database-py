import numpy as np
import pytest

import nqm.iotdatabase._sqliteconstants as _sqliteconstants
import nqm.iotdatabase._sqliteschemaconverter as _sqliteschemaconverter

def _data_equal(actual_data, expected_data):
    actual_data_length = len(actual_data)
    try:
        expected_data_length = len(expected_data)
    except TypeError:
        expected_data = tuple(expected_data)
        expected_data_length = len(expected_data)

    assert actual_data_length == expected_data_length
    for row, expected_row in zip(actual_data, expected_data):
        _row_equal(row, expected_row)

@pytest.fixture(scope="session")
def data_equal():
    return _data_equal

def _row_equal(row1, row2):
    assert len(row1) == len(row2)
    for col, val in row1.items():
        if isinstance(val, np.ndarray):
            assert np.array_equal(val, row2[col])
        else:
            assert val == row2[col]

@pytest.fixture(scope="session")
def row_equal():
    return _row_equal

GENERAL_TYPES = _sqliteconstants.SQLITE_GENERAL_TYPE
SQL_TYPES = _sqliteconstants.SQLITE_TYPE
def _make_val(gen_type, number):
    """Generate a unique value of a specific type"""

    typ = _sqliteschemaconverter._toGeneralSqliteValType(gen_type)
    if typ is GENERAL_TYPES.OBJECT:
        return {
            "testObjectPleaseIgnore": "whyareyoureadingthis",
            "stopreadingthesestrings": {
                "theyaresecret": 1337 + number,
                "supersecret": ["hi", 2, "hi again\n"],
            }
        }
    elif typ is GENERAL_TYPES.ARRAY:
        return [number, 2, 3, 4, 5, 6, "test", {"a": 1, "b": "test"}]
    elif typ is GENERAL_TYPES.NDARRAY:
        return np.array(((number, 2), (3, 4)))
    elif typ in {SQL_TYPES.NUMERIC, SQL_TYPES.INTEGER, SQL_TYPES.REAL}:
        return number
    elif typ is SQL_TYPES.TEXT:
        return f"randomText{number:.2f}"
    else:
        raise NotImplementedError(f"Huh, {typ} did not match anything...")

def _make_data(schema, number=100):
    """Makes some unique rows of data to put into a dataset."""
    gen_schema = _sqliteschemaconverter.convertSchema(
        schema.get("dataSchema", {}))

    def make_row(row_no):
        return {key: _make_val(typ, row_no) for key, typ in gen_schema.items()}

    for i in range(number):
        return [make_row(i) for i in range(number)]

@pytest.fixture(scope="session")
def make_data():
    return _make_data
