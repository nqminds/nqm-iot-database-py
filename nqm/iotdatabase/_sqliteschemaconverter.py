"""Module to convert a tdx schema into a sqlite schema.
"""
import typing
import numbers
import nqm.iotdatabase._sqliteconstants as _sqliteconstants
import json
import collections

SQLITE_TYPE = _sqliteconstants.SQLITE_TYPE

# types that can be inserted in SQLite
sqlite_types = typing.Union[int, float, typing.Text, numbers.Real]

# type of storage of general SQLite types or SQLite types.
general_sqlite_types = typing.Union[
    SQLITE_TYPE,
    _sqliteconstants.SQLITE_GENERAL_TYPE
]
# type of storage of general SQLite types or SQLite types or str
general_sqlite_types_or_str = typing.Union[
    SQLITE_TYPE,
    _sqliteconstants.SQLITE_GENERAL_TYPE,
    typing.Text,
]
# types that can be JSON.stringified
jsonifiable_types = typing.Union[
    float, int, typing.Text, numbers.Real, typing.Mapping, typing.Sequence]

def getBasicType(tdx_types: typing.Sequence[
    typing.Union[_sqliteconstants.TDX_TYPE, typing.Text]
]) -> SQLITE_TYPE:
    """Returns a basic SQLite type from a list of tdx types.

    Args:
        tdx_types: The list of tdx types.
    Returns:
        The SQLite basic type.
    """
    tdx_base_type = tdx_types[0]
    try:
        tdx_base_type = tdx_base_type.lower() # make sure we are using lowercase
    except:
        pass
    tdx_base_type = _sqliteconstants.TDX_TYPE(tdx_base_type)
    
    TDX_TYPE = _sqliteconstants.TDX_TYPE
    SQLITE_TYPE = SQLITE_TYPE

    def number():
        tdx_derived_type = tdx_types[1]
        if TDX_TYPE.INT in tdx_derived_type:
            return SQLITE_TYPE.INTEGER
        elif TDX_TYPE.REAL.match(tdx_derived_type):
            return SQLITE_TYPE.REAL
        else: return SQLITE_TYPE.TEXT

    mapping: typing.Dict[TDX_TYPE, typing.Callable[[], SQLITE_TYPE]] = {
        TDX_TYPE.STRING: lambda: SQLITE_TYPE.TEXT,
        TDX_TYPE.BOOLEAN: lambda: SQLITE_TYPE.NUMERIC,
        TDX_TYPE.DATE: lambda: SQLITE_TYPE.NUMERIC,
        TDX_TYPE.NUMBER: number
    }

    return mapping.get(tdx_base_type, d=lambda: SQLITE_TYPE.TEXT)()

def _toGeneralSqliteType(general_sqlite_type: general_sqlite_types_or_str
) -> general_sqlite_types:
    """Converts a string to the enum types"""
    try:
        return SQLITE_TYPE(type)
    except ValueError:
        return _sqliteconstants.SQLITE_GENERAL_TYPE(type)

def _mapVal(type: general_sqlite_types_or_str) -> SQLITE_TYPE:
    """Maps a general sqlite type to a valid sqlite type"""
    enum_type = _toGeneralSqliteType(type)
    if isinstance(enum_type, _sqliteconstants.SQLITE_GENERAL_TYPE):
        return SQLITE_TYPE.TEXT # arrays and objects are jsonified
    else:
        return enum_type

def mapSchema(types: typing.Mapping[typing.Text, general_sqlite_types_or_str]
) -> typing.Dict[typing.Text, SQLITE_TYPE]:
    """Maps a general sqlite schema type into a valid sqlite schema.

    Args:
        types: The general sqlite schema type
    
    Returns:
        The mapped valid sqlite schema
    """
    return {name: _mapVal(val) for name, val in types.items()}

def _convertSchemaOne(value: typing.Union[typing.Sequence, typing.Mapping]
) -> general_sqlite_types:
    """Used in convertSchema"""
    if isinstance(value, collections.Sequence):
        return _sqliteconstants.SQLITE_GENERAL_TYPE.ARRAY
    elif isinstance(value, collections.Mapping):
        real_type = value.get(_sqliteconstants.TDX_TYPE.NAME, d=None)
        if real_type is not None:
            return getBasicType(real_type)
        else:
            return _sqliteconstants.SQLITE_GENERAL_TYPE.OBJECT

def convertSchema(schema: typing.Mapping[
    str, typing.Union[typing.Sequence, typing.Mapping]]
) -> typing.Dict[str, general_sqlite_types]:
    """Converts a tdx schema into a sqlite schema.
    
    """
    return {name: _convertSchemaOne(value) for name, value in schema.items()}

def convertToSqlite(
    type: general_sqlite_types_or_str,
    value: typing.Any,
    only_stringify: bool = False
) -> sqlite_types:
    """Converts a tdx value to a sqlite value based on a sqlite type.

    Args:
        type: Sqlite type to convert the value to
        value: TDX value to convert
        only_stringify: Set to `True` to turn off escaping single-quotes and
            delimiter addition.
            This shouldn't be required as one should bind strings to SQLite
            statements to avoid SQL injections anyway.

    Raises:
        TypeError: If `value` is a Python type that cannot be converted t
            `type`.
    Returns:
        The converted value.
    """
    fixed_type = _toGeneralSqliteType(type)

    if only_stringify:
        def to_text(value):
            return str(value)
    else:
        def to_text(value):
            # escape ' and quote
            return "'{}'".format(str(value).replace("'", "''"))

    def jsonify(value):
        return to_text(json.dumps(value))

    converter = {
        SQLITE_TYPE.INTEGER: int,
        SQLITE_TYPE.REAL: float,
        SQLITE_TYPE.NUMERIC: float,
        SQLITE_TYPE.TEXT: to_text,
        _sqliteconstants.SQLITE_GENERAL_TYPE.ARRAY: jsonify,
        _sqliteconstants.SQLITE_GENERAL_TYPE.OBJECT: jsonify
    }

    return converter[fixed_type](value)

def convertToTdx(
    type: general_sqlite_types_or_str,
    value: str
) -> typing.Union[int, float, list, dict, str]:
    """Converts a sqlite value to a tdx value based on a sqlite type.

    Args:
        type: SQLite type to convert the value from
        value: SQLite value to convert from
    
    Returns:
        The converted value.
    """

    fixed_type = _toGeneralSqliteType(type)

    converter = {
        SQLITE_TYPE.INTEGER: int,
        SQLITE_TYPE.REAL: float,
        SQLITE_TYPE.NUMERIC: float,
        SQLITE_TYPE.TEXT: lambda x: x,
        _sqliteconstants.SQLITE_GENERAL_TYPE.ARRAY: json.loads,
        _sqliteconstants.SQLITE_GENERAL_TYPE.OBJECT: json.loads
    }

    return converter[fixed_type](value)
