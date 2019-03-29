import json
import itertools
import functools
import pathlib
import random
import os.path
import json

import pytest

import sqlalchemy.exc
from nqm.iotdatabase.database import Database

def json_dbinfo(jsonfilepath="tdx-schemas.json"):
    with pathlib.Path(__file__).with_name(jsonfilepath).open() as jsonfile:
        return json.load(jsonfile)

def test_getResource():
    for info in json_dbinfo():
        inmemdb = Database("", "memory", "w+")
        inmemdb.createDatabase(**info)

        saved_info = inmemdb.getResource()

        # every getResource() needs metadata
        assert "schemaDefinition" in saved_info

        for key in info.keys():
            if key == "schema":
                # I don't know why it is like this, but this is how the TDX
                # works?
                assert saved_info["schemaDefinition"] == info[key]
            else:
                # check everything in info is saved in the infotable.
                assert saved_info[key] == info[key]

def schemas():
    return itertools.chain(
        [x["schema"] for x in json_dbinfo()],
        [{}] # empty schema
    )

@pytest.fixture(params=schemas())
def schema(request):
    return request.param

def unique_schemas():
    """ Returns a list of schemas that have a uniqueIndex """
    return [x for x in schemas() if x.get("uniqueIndex", [])]

@pytest.fixture(params=unique_schemas())
def unique_schema(request):
    """Runs unique_schema test once for each schema with a uniqueIndex."""
    return request.param

@pytest.fixture()
def inmemdb():
    """Returns a new in-memory db"""
    return Database("", "memory", "w+")

@pytest.fixture()
def db(inmemdb, schema):
    """When used as a fixture, creates a db with every schema in schema()"""
    inmemdb.createDatabase(schema=schema)
    return inmemdb

@pytest.mark.dependency(depends=["test_create_dataset"])
def test_insert_dataset(db, schema, make_data):
    number = 100
    data = make_data(schema, number)
    if schema.get("dataSchema", []):
        assert db.addData(data) == {"count": number}
    else:
        # no table should be created
        with pytest.raises(ValueError):
            db.addData(data)

@pytest.mark.dependency(depends=["test_insert_dataset"])
def test_insert_nonunique_error(inmemdb, unique_schema, row_equal, make_data):
    inmemdb.createDatabase(schema=unique_schema)
    number = 100
    data = make_data(unique_schema, number+1)
    assert inmemdb.addData(data[:number]) == {"count": number}
    # TODO: Maybe make our own Error type if something goes wrong?
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        inmemdb.addData([data[0]]) # adding invalid same data again
    # check that inserting more data works after an exception
    assert inmemdb.addData([data[number]]) == {"count": 1}

    # check that data is correctly stored
    if len(unique_schema.get("uniqueIndex", [])) == 1:
        uniqueIndex = list(unique_schema["uniqueIndex"][0].values())[0]
        for row in data:
            query_val = row[uniqueIndex]
            ret = inmemdb.getData({uniqueIndex: query_val}).data[0]
            row_equal(row, ret)

def make_filedb(filepath):
    return Database(filepath, "file", "w+")

def test_file_db(tmpdir, make_data):
    """Make sures that a file db actually saves and loads data correctly"""
    filepath = os.path.join(tmpdir, "testdb.sqlite")
    filedb = make_filedb(filepath)
    schema = next(schemas())
    filedb.createDatabase(schema=schema)
    number = 100
    data = make_data(schema, number=number)
    assert filedb.addData(data) == {"count": number}

    # reload database
    filedb = make_filedb(filepath)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        filedb.addData([data[0]]) # should cause uniqueIndex error

    uniqueIndex = [list(x.values())[0] for x in schema["uniqueIndex"]]
    for row in data:
        savedData = filedb.getData(
            {key: row[key] for key in uniqueIndex}).data
