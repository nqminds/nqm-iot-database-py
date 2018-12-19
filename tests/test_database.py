import json
import itertools
import functools
import pathlib
import random
import sqlalchemy.exc
import os.path

import pytest
from nqm.iotdatabase.database import Database
import nqm.iotdatabase._sqliteconstants as _sqliteconstants
import nqm.iotdatabase._sqliteschemaconverter as _sqliteschemaconverter

def json_dbinfo(jsonfilepath="tdx-schemas.json"):
    with pathlib.Path(__file__).with_name(jsonfilepath).open() as jsonfile:
        return json.load(jsonfile)

def schemas():
    return itertools.chain(
        [x["schema"] for x in json_dbinfo()],
        [{}]
    )

@pytest.fixture(params=schemas())
def schema(request):
    return request.param

def unique_schemas():
    return [x for x in schemas() if x.get("uniqueIndex", [])]

@pytest.fixture(params=unique_schemas())
def unique_schema(request):
    return request.param

GENERAL_TYPES = _sqliteconstants.SQLITE_GENERAL_TYPE
SQL_TYPES = _sqliteconstants.SQLITE_TYPE
def make_val(gen_type, number):
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
    elif typ in {SQL_TYPES.NUMERIC, SQL_TYPES.INTEGER, SQL_TYPES.REAL}:
        return number
    elif typ is SQL_TYPES.TEXT:
        return f"randomText{number:.2f}"
    else:
        raise NotImplementedError(f"Huh, {typ} did not match anything...")

def make_data(schema, number=100):
    gen_schema = _sqliteschemaconverter.convertSchema(
        schema.get("dataSchema", {}))

    def make_row(row_no):
        return {key: make_val(typ, row_no) for key, typ in gen_schema.items()}

    for i in range(number):
        return [make_row(i) for i in range(number)]

@pytest.fixture()
def inmemdb():
    return Database("", "memory", "w+")

@pytest.fixture()
def db(inmemdb, schema):
    inmemdb.createDatabase(schema=schema)
    return inmemdb

@pytest.mark.dependency(depends=["test_create_dataset"])
def test_insert_dataset(db, schema):
    number = 100
    data = make_data(schema, number)
    if schema.get("dataSchema", []):
        assert db.addData(data) == {"count": number}
    else:
        # no table should be created
        with pytest.raises(ValueError):
            db.addData(data)

@pytest.mark.dependency(depends=["test_insert_dataset"])
def test_insert_nonunique_error(inmemdb, unique_schema):
    inmemdb.createDatabase(schema=unique_schema)
    number = 100
    data = make_data(unique_schema, number)
    assert inmemdb.addData(data) == {"count": number}
    repeatNum = random.randint(0, number)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        inmemdb.addData([data[repeatNum]])

def make_filedb(filepath):
    return Database(filepath, "file", "w+")

def test_file_db(tmpdir):
    filedb = make_filedb(os.path.join(tmpdir, "testdb.sqlite"))
    schema = next(schemas())
    filedb.createDatabase(schema=schema)
    number = 100
    data = make_data(schema, number=number)
    assert filedb.addData(data) == {"count": number}

    # reload database
    filedb = make_filedb(os.path.join(tmpdir, "testdb.sqlite"))
    filedb.createDatabase(schema=schema)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        filedb.addData([data[0]]) # should cause uniqueIndex error