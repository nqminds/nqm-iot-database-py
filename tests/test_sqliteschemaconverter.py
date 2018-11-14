import pytest

import nqm.iotdatabase._sqliteschemaconverter as sqliteschemaconverter

def test_convert_schema():
    # should return empty for an empty input
    assert sqliteschemaconverter.convertSchema({}) == {}
