"""Module to convert a tdx schema into a sqlite schema.
"""
import typing as t
import numbers
import nqm.iotdatabase._sqliteconstants as _sqliteconstants
import json
import collections

SQLITE_TYPE = _sqliteconstants.SQLITE_TYPE
TDX_TYPE = _sqliteconstants.TDX_TYPE

# types that can be inserted in SQLite
sqlite_types = t.Union[int, float, t.Text, numbers.Real]

# type of storage of general SQLite types or SQLite types.
general_sqlite_types = t.Union[
    SQLITE_TYPE,
    _sqliteconstants.SQLITE_GENERAL_TYPE
]
# type of storage of general SQLite types or SQLite types or str
general_sqlite_types_or_str = t.Union[
    SQLITE_TYPE,
    _sqliteconstants.SQLITE_GENERAL_TYPE,
    t.Text,
]
# types that can be JSON.stringified
jsonifiable_types = t.Union[
    float, int, t.Text, numbers.Real, t.Mapping, t.Sequence]

def getBasicType(tdx_types: t.Sequence[
    t.Union[TDX_TYPE, t.Text]
]) -> SQLITE_TYPE:
    """Returns a basic SQLite type from a list of tdx types.

    Args:
        tdx_types: The list of tdx types.
    Returns:
        The SQLite basic type.
    """
    tdx_base_type = tdx_types[0]
    if isinstance(tdx_base_type, str):
        tdx_base_type = tdx_base_type.lower() # make sure we are using lowercase
    tdx_base_type = TDX_TYPE(tdx_base_type)

    def number():
        tdx_derived_type = tdx_types[1].upper() if len(tdx_types) > 1 else None
        if tdx_derived_type is None:
            pass
        elif TDX_TYPE.INT.value in str(tdx_derived_type):
            return SQLITE_TYPE.INTEGER
        elif TDX_TYPE.REAL.value.match(tdx_derived_type):
            return SQLITE_TYPE.REAL

        return SQLITE_TYPE.NUMERIC

    mapping: t.Dict[TDX_TYPE, t.Callable[[], SQLITE_TYPE]] = {
        TDX_TYPE.STRING: lambda: SQLITE_TYPE.TEXT,
        TDX_TYPE.BOOLEAN: lambda: SQLITE_TYPE.NUMERIC,
        TDX_TYPE.DATE: lambda: SQLITE_TYPE.NUMERIC,
        TDX_TYPE.NUMBER: number
    }

    return mapping.get(tdx_base_type, lambda: SQLITE_TYPE.TEXT)()

def _toGeneralSqliteType(general_sqlite_type: general_sqlite_types_or_str
) -> general_sqlite_types:
    """Converts a string to the enum types"""
    try:
        return SQLITE_TYPE(general_sqlite_type)
    except ValueError:
        return _sqliteconstants.SQLITE_GENERAL_TYPE(general_sqlite_type)

def _mapVal(type: general_sqlite_types_or_str) -> SQLITE_TYPE:
    """Maps a general sqlite type to a valid sqlite type"""
    enum_type = _toGeneralSqliteType(type)
    if isinstance(enum_type, _sqliteconstants.SQLITE_GENERAL_TYPE):
        return SQLITE_TYPE.TEXT # arrays and objects are jsonified
    else:
        return enum_type

def mapSchema(types: t.Mapping[t.Text, general_sqlite_types_or_str]
) -> t.Dict[t.Text, SQLITE_TYPE]:
    """Maps a general sqlite schema type into a valid sqlite schema.

    Args:
        types: The general sqlite schema type
    
    Returns:
        The mapped valid sqlite schema
    """
    return {name: _mapVal(val) for name, val in types.items()}

def _convertSchemaOne(value: t.Union[t.Sequence, t.Mapping]
) -> general_sqlite_types:
    """Used in convertSchema"""
    if isinstance(value, collections.Sequence):
        return _sqliteconstants.SQLITE_GENERAL_TYPE.ARRAY
    elif isinstance(value, collections.Mapping):
        real_type = value.get(str(TDX_TYPE.NAME), None)
        if real_type is not None:
            return getBasicType(real_type)
        else:
            return _sqliteconstants.SQLITE_GENERAL_TYPE.OBJECT

def convertSchema(schema: t.Mapping[
    t.Text, t.Union[t.Sequence, t.Mapping]]
) -> t.Dict[t.Text, general_sqlite_types]:
    """Converts a tdx schema into a sqlite schema.
    """
    return {name: _convertSchemaOne(value) for name, value in schema.items()}

def convertToSqlite(
    type: general_sqlite_types_or_str,
    value: t.Any,
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
        def to_text(value) -> t.Text:
            return str(value)
    else:
        def to_text(value) -> t.Text:
            # escape ' and quote
            return "'{}'".format(str(value).replace("'", "''"))

    def jsonify(value) -> t.Text:
        return to_text(json.dumps(value))

    converter: t.Dict[general_sqlite_types, t.Callable] = {
        SQLITE_TYPE.INTEGER: int,
        SQLITE_TYPE.REAL: float,
        SQLITE_TYPE.NUMERIC: float,
        SQLITE_TYPE.TEXT: to_text,
        _sqliteconstants.SQLITE_GENERAL_TYPE.ARRAY: jsonify,
        _sqliteconstants.SQLITE_GENERAL_TYPE.OBJECT: jsonify
    }

    return converter[fixed_type](value) # type: ignore

json_types = t.Union[int, float, t.List, t.Dict, t.Text]
def convertToTdx(
    type: general_sqlite_types_or_str,
    value: t.Text
) -> json_types:
    """Converts a sqlite value to a tdx value based on a sqlite type.

    Args:
        type: SQLite type to convert the value from
        value: SQLite value to convert from
    
    Returns:
        The converted value.
    """

    fixed_type = _toGeneralSqliteType(type)

    converter: t.Dict[general_sqlite_types, t.Callable] = {
        SQLITE_TYPE.INTEGER: int,
        SQLITE_TYPE.REAL: float,
        SQLITE_TYPE.NUMERIC: float,
        SQLITE_TYPE.TEXT: lambda x: x,
        _sqliteconstants.SQLITE_GENERAL_TYPE.ARRAY: json.loads,
        _sqliteconstants.SQLITE_GENERAL_TYPE.OBJECT: json.loads
    }

    return converter[fixed_type](value) # type: ignore
