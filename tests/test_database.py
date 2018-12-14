import json
import itertools
import functools
import pathlib

import pytest
from nqm.iotdatabase.database import Database

def json_dbinfo(jsonfilepath="tdx-schemas.json"):
    with pathlib.Path(__file__).with_name(jsonfilepath).open() as jsonfile:
        return json.load(jsonfile)

schema_parametrize = lambda: pytest.mark.parametrize(
    argnames="schema",
    argvalues=itertools.chain(
        [{}],
        [x["schema"] for x in json_dbinfo()],
    )
)

@pytest.fixture()
def inmemdb():
    return Database("", "memory", "w+")

@schema_parametrize()
def test_create_dataset(inmemdb, schema):
    inmemdb.createDatabase(schema=schema)
