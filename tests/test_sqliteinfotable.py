"""
This code uses @pytest.fixutres
These functions are called everytime they are seen as an arg in a test.
"""
import pytest
import nqm.iotdatabase._sqliteinfotable as infotable
import sqlalchemy.exc
import pathlib
import json
import itertools
import functools

def test_sqlAlchemyEngineCreator():
    import nqm.iotdatabase._sqliteutils as sqliteutils
    with pytest.raises(TypeError):
        creator = sqliteutils.sqlAlchemyEngineCreator(
            "", type="file", mode="w+")
        pytest.fail(
            "Was expecting invalid path sqlAlchemyEngineCreator to fail")

@pytest.fixture
def in_mem_db():
    """Returns a new rwc in-memory SQLite SQLAlchemy connection"""
    import nqm.iotdatabase._sqliteutils as sqliteutils
    import sqlalchemy
    import sqlalchemy.engine.url
    import urllib.parse
    path = ""
    creator = sqliteutils.sqlAlchemyEngineCreator(
            path, type="memory", mode="w+")
    return sqlalchemy.create_engine("sqlite:///", creator=creator)

@pytest.fixture
def blank_table(in_mem_db):
    """Creates a new in-mem-db that has an info table"""
    infotable.createInfoTable(in_mem_db)
    return in_mem_db

def test_createInfoTable(in_mem_db):
    infotable.createInfoTable(in_mem_db)
    with pytest.raises(Exception):
        infotable.createInfoTable(in_mem_db)
        pytest.fail("Was expecting 2nd createInfoTable to fail")

def json_keys(jsonfilepath="infokeys.json"):
    with pathlib.Path(__file__).with_name(jsonfilepath).open() as jsonfile:
        return json.load(jsonfile)

def all_keys():
    return itertools.chain(
        [{}, {"hi": "test"}],
        json_keys(),
    )

@pytest.fixture(params=all_keys())
def keys(request):
    """All tests with the arg 'keys' will be run once for each key.
    """
    return request.param

def test_getInfoKeys(blank_table, keys):
    assert infotable.setInfoKeys(blank_table, keys) == {"count": len(keys)}
    keyList = keys.keys()
    assert infotable.getInfoKeys(blank_table, keyList) == keys
