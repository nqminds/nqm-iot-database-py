import pytest
import nqm.iotdatabase._sqliteinfotable as infotable
import sqlalchemy.exc
import pathlib
import json
import itertools
import functools

@pytest.fixture
def in_mem_db():
    """Returns a new rwc in-memory SQLite SQLAlchemy connection"""
    import nqm.iotdatabase._sqliteutils as sqliteutils
    import sqlalchemy
    import sqlalchemy.engine.url
    import urllib.parse
    path = ""
    url = sqliteutils.sqlAlchemyURL(path, type="memory", mode="w+")
    return sqlalchemy.create_engine(url)

@pytest.fixture
def blank_table(in_mem_db):
    infotable.createInfoTable(in_mem_db)
    return in_mem_db

def test_createInfoTable(in_mem_db):
    infotable.createInfoTable(in_mem_db)
    with pytest.raises(
        Exception,
        message="Was expecting 2nd createInfoTable to fail"
    ):
        infotable.createInfoTable(in_mem_db)

def json_keys(jsonfilepath="infokeys.json"):
    with pathlib.Path(__file__).with_name(jsonfilepath).open() as jsonfile:
        return json.load(jsonfile)

key_parametrize = lambda: pytest.mark.parametrize(
    argnames="keys",
    argvalues=itertools.chain(
        [{}, {"hi": "test"}],
        json_keys(),
    )
)

@key_parametrize()
def test_getInfoKeys(blank_table, keys):
    assert infotable.setInfoKeys(blank_table, keys) == {"count": len(keys)}
    keyList = keys.keys()
    assert infotable.getInfoKeys(blank_table, keyList) == keys
