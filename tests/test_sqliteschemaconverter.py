import pytest
import collections
import itertools
import typing
import json
import pathlib

import nqm.iotdatabase._sqliteschemaconverter as sqliteschemaconverter

ConvertSchemaParam = collections.namedtuple(
    "ConvertSchemaParam",
    field_names="tdx,general,sqlite")

def _convertSchemaParams():
    empty_test = ConvertSchemaParam(tdx={}, general={}, sqlite={})
    tests: typing.List[ConvertSchemaParam] = [ # list of ConvertSchemaParam
        empty_test
    ]

    def load_from_json():
        """Loads ConvertSchemaParam from a JSON file"""
        jsonfilepath = "tdx-schemas.json"
        # request.node.fspath is the location of this test file
        contents = None

        with pathlib.Path(__file__).with_name(jsonfilepath).open() as jsonfile:
            contents = json.load(jsonfile)

        for testCase in contents:
            yield ConvertSchemaParam(
                tdx=testCase["schema"]["dataSchema"],
                general=testCase["generalSchema"],
                sqlite=testCase["sqliteSchema"])

    return itertools.chain(tests, load_from_json())

@pytest.mark.parametrize(
    argnames="tdx_schema,general_schema,sqlite_schema",
    argvalues=_convertSchemaParams()
)
def test_convertSchema(tdx_schema,general_schema,sqlite_schema):
    def s(val): return {a: str(b) for a,b in val.items()}
    assert s(sqliteschemaconverter.convertSchema(tdx_schema)) == general_schema
    assert s(sqliteschemaconverter.mapSchema(general_schema)) == sqlite_schema
