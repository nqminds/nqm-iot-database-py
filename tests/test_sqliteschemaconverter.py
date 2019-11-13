import pytest
import itertools
import typing
import json
import pathlib

import nqm.iotdatabase._sqliteschemaconverter as sqliteschemaconverter

# stores the params needed for a call of test_convertSchema()
class ConvertSchemaParam(typing.NamedTuple):
    tdx: typing.Mapping
    general: typing.Mapping
    sqlite: typing.Mapping

def _convertSchemaParams():
    """Returns an iterator containing the params for test_convertSchema()"""
    # empty objects should convert to empty objects with no errors
    # TODO: Maybe make a warning here?
    empty_test = ConvertSchemaParam(tdx={}, general={}, sqlite={})
    tests: typing.List[ConvertSchemaParam] = [ # list of ConvertSchemaParam
        empty_test
    ]

    def load_from_json():
        """Iterates over a file with the params for test_convertSchema()"""
        jsonfilepath = "tdx-schemas.json"
        # request.node.fspath is the location of this test file
        contents = None

        # opens jsonfilepath relative to this file
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
