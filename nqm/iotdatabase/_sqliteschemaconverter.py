"""Module to convert a tdx schema into a sqlite schema.
"""
import typing as t
import numbers
import json
import collections.abc
import os

from . import _sqliteconstants
from . import ndarray as _ndarray

#TODO: Use snake_case names, instead of following JavaScript API names.
#pylint: disable=locally-disabled, invalid-name

#pylint: disable=locally-disabled, redefined-builtin

SQLITE_TYPE = _sqliteconstants.SQLITE_TYPE #pylint: disable=invalid-name
TDX_TYPE = _sqliteconstants.TDX_TYPE #pylint: disable=invalid-name

# types that can be inserted in SQLite
SQLVal = t.Union[int, float, t.Text, numbers.Real]

# type of storage of general SQLite types or SQLite types.
GeneralSQLiteVal = t.Union[
    SQLITE_TYPE,
    _sqliteconstants.SQLITE_GENERAL_TYPE
]
# type of storage of general SQLite types or SQLite types or str
GeneralSQLOrStr = t.Union[
    SQLITE_TYPE,
    _sqliteconstants.SQLITE_GENERAL_TYPE,
    t.Text,
]
# types that can be JSON.dumps
JSONable = t.Union[
    float, int, t.Text, numbers.Real, t.Mapping, t.Sequence, bool, None]

# json.loads could also return a bool but we don't store any
JSONified = t.Union[int, float, t.List, t.Dict, t.Text, None]

GeneralSchema = t.Mapping[t.Text, GeneralSQLiteVal]
"A SQLite General Schema Object"
TDXDataSchema = t.Mapping[t.Text, t.Union[t.Mapping, t.Sequence]]
"""A TDX Data Schema Object. Example: {"prop1": {"__tdxType": ["number"]}
"""
TDXSchema = t.NewType("TDXSchema", t.Mapping[t.Text, JSONable])
"A TDXSchema object."

def getBasicType(
        tdx_types: t.Sequence[t.Union[TDX_TYPE, t.Text]]) -> GeneralSQLiteVal:
    """Returns a general SQLite type from a list of tdx types.

    Args:
        tdx_types: The list of tdx types.
    Returns:
        The SQLite basic type.
    """
    tdx_base_type = tdx_types[0] # TDX Base Type is basically just JS types
    if isinstance(tdx_base_type, str):
        tdx_base_type = tdx_base_type.lower() # make sure we are using lowercase
    tdx_base_type = TDX_TYPE(tdx_base_type) # convert to enum

    def number():
        """If the base type is number, we need to use the derived type to
        find out whether it is a INT/REAL.
        """
        tdx_derived_type = tdx_types[1].upper() if len(tdx_types) > 1 else None
        if tdx_derived_type is None:
            pass
        elif str(TDX_TYPE.INT) in str(tdx_derived_type):
            return SQLITE_TYPE.INTEGER
        elif TDX_TYPE.REAL.value.match(tdx_derived_type):
            return SQLITE_TYPE.REAL

        return SQLITE_TYPE.NUMERIC

    # map of base types to functions that return the sqlite type
    mapping: t.Dict[TDX_TYPE, t.Callable[[], GeneralSQLiteVal]] = {
        TDX_TYPE.STRING: lambda: SQLITE_TYPE.TEXT,
        TDX_TYPE.BOOLEAN: lambda: SQLITE_TYPE.NUMERIC,
        TDX_TYPE.DATE: lambda: SQLITE_TYPE.NUMERIC,
        TDX_TYPE.NUMBER: number,
        TDX_TYPE.NDARRAY: lambda: _sqliteconstants.SQLITE_GENERAL_TYPE.NDARRAY,
    }

    # if the tdx type is not in mapping (ie array/obj), use TEXT by default
    return mapping.get(tdx_base_type, lambda: SQLITE_TYPE.TEXT)()

def _toGeneralSqliteValType(
        general_sqlite_type: GeneralSQLOrStr) -> GeneralSQLiteVal:
    """Converts a string to the enum types.

    Enums are better than strings since types and error messages.
    """
    try:
        return SQLITE_TYPE(general_sqlite_type)
    except ValueError:
        return _sqliteconstants.SQLITE_GENERAL_TYPE(general_sqlite_type)

def _mapVal(type: GeneralSQLOrStr) -> SQLITE_TYPE:
    """Maps a general sqlite type to a valid sqlite type"""
    enum_type = _toGeneralSqliteValType(type)
    if isinstance(enum_type, _sqliteconstants.SQLITE_GENERAL_TYPE):
        return SQLITE_TYPE.TEXT # arrays and objects are jsonified

    return enum_type

def mapSchema(
        types: t.Mapping[t.Text, GeneralSQLOrStr],
) -> t.Dict[t.Text, SQLITE_TYPE]:
    """Maps a general sqlite schema type into a valid sqlite schema.

    Args:
        types: The general sqlite schema type

    Returns:
        The mapped valid sqlite schema
    """
    return {name: _mapVal(val) for name, val in types.items()}

def _convertSchemaOne(
        value: t.Union[t.Sequence, t.Mapping]) -> GeneralSQLiteVal:
    """Used in convertSchema"""
    # I don't actually understand what this does, I just ported
    # it from @mereacre's code (🇲🇩 🧛 🔮 Moldovan Vampyre Magick)
    if isinstance(value, collections.abc.Sequence):
        return _sqliteconstants.SQLITE_GENERAL_TYPE.ARRAY
    if isinstance(value, collections.abc.Mapping):
        real_type = value.get(str(TDX_TYPE.NAME), None)
        if real_type is not None:
            return getBasicType(real_type)
        return _sqliteconstants.SQLITE_GENERAL_TYPE.OBJECT
    raise TypeError(
        f"type(value)={type(value)} should be a Sequence or Mapping.")

def convertSchema(schema: TDXDataSchema) -> GeneralSchema:
    """Converts a tdx data schema into a sqlite schema.
    """
    return {name: _convertSchemaOne(val) for name, val in schema.items()}

def convertRowToSqlite(
        schema: GeneralSchema,
        row: t.Mapping[t.Text, t.Any],
        throwOnExtraKeys: bool = False,
        data_dir: t.Union[t.Text, os.PathLike] = "",
) -> t.Mapping[t.Text, SQLVal]:
    """Converts a Python row to a row for SQLite insertion.

    Args:
        schema: The SQLite General Schema
        row: A dict of column_name: column_value specifying the row
        throwOnExtraKeys:
            Set to `True` to throw an error if row has keys that are not
            specified in the `schema`.
            For example, adding {"color": 1} will throw if the schema
            is expected {"colour": 1}.
        data_dir:
            The directory to store additional data. Used when saving ndarrays.

    Returns:
        The converted row in SQLite types.
    """
    converted_row = {}
    for col, val in row.items():
        try:
            sqlite_type = schema[col]
        except KeyError:
            if throwOnExtraKeys:
                raise KeyError(
                    f"Key {col} could not be found within the schema keys:"
                    f" {schema.keys()}")
        converted_row[col] = convertToSqlite(sqlite_type, val, True, data_dir)
    return converted_row

def convertToSqlite(
        type: GeneralSQLOrStr,
        value: t.Any,
        only_stringify: bool = False,
        data_dir: t.Union[t.Text, os.PathLike] = "",
) -> SQLVal:
    """Converts a tdx value to a sqlite value based on a sqlite type.

    Args:
        type: Sqlite type to convert the value to
        value: TDX value to convert
        only_stringify: Set to `True` to turn off escaping single-quotes and
            delimiter addition.
            This shouldn't be required as one should bind strings to SQLite
            statements to avoid SQL injections anyway.
        data_dir:
            The directory to store additional data. Used when saving ndarrays.

    Raises:
        TypeError: If `value` is a Python type that cannot be converted t
            `type`.
    Returns:
        The converted value.
    """
    fixed_type = _toGeneralSqliteValType(type)

    if only_stringify:
        def to_text(value) -> t.Text:
            return str(value)
    else:
        def to_text(value) -> t.Text:
            # escape ' and quote
            return "'{}'".format(str(value).replace("'", "''"))

    def jsonify(value) -> t.Text:
        return to_text(json.dumps(value))

    def ndarray(array):
        return _ndarray.saveNDArray(array, relative_loc=data_dir).tojson()

    # map of types to funcs that covert from that type
    converter: t.Dict[GeneralSQLiteVal, t.Callable] = {
        SQLITE_TYPE.INTEGER: int,
        SQLITE_TYPE.REAL: float,
        SQLITE_TYPE.NUMERIC: float,
        SQLITE_TYPE.TEXT: to_text,
        _sqliteconstants.SQLITE_GENERAL_TYPE.ARRAY: jsonify,
        _sqliteconstants.SQLITE_GENERAL_TYPE.OBJECT: jsonify,
        _sqliteconstants.SQLITE_GENERAL_TYPE.NDARRAY: ndarray,
    }

    return converter[fixed_type](value) # type: ignore

def convertRowToTdx(
        schema: GeneralSchema,
        row: t.Mapping[t.Text, SQLVal],
        data_dir: t.Union[t.Text, os.PathLike] = "",
) -> t.Mapping[t.Text, JSONified]:
    """Converts an sqlite row to a tdx row based on the tdx schema.

    Args:
        unfolded_schema: A Map of Column names to TDX types.
        row: A map of column to sqlite column value
        data_dir:
            The directory to store additional data. Used when saving ndarrays.

    Returns:
        a map of column to converted TDX values
    """
    return {
        col: convertToTdx(
            schema[col], # tdx_type
            val, # the sqlite value
            data_dir)
        for col, val in row.items() if col in schema}

def convertToTdx(
        type: GeneralSQLOrStr,
        value: SQLVal,
        data_dir: t.Union[t.Text, os.PathLike] = "",
) -> JSONified:
    """Converts a sqlite value to a tdx value based on a sqlite type.

    Args:
        type: SQLite type to convert the value from
        value: SQLite value to convert from
        data_dir:
            The directory to store additional data. Used when saving ndarrays.

    Returns:
        The converted value.
    """

    fixed_type = _toGeneralSqliteValType(type)

    # map of types to funcs that covert from that type
    converter: t.Dict[GeneralSQLiteVal, t.Callable] = {
        SQLITE_TYPE.INTEGER: int,
        SQLITE_TYPE.REAL: float,
        SQLITE_TYPE.NUMERIC: float,
        SQLITE_TYPE.TEXT: lambda x: x, # does nothing
        _sqliteconstants.SQLITE_GENERAL_TYPE.ARRAY: json.loads,
        _sqliteconstants.SQLITE_GENERAL_TYPE.OBJECT: json.loads,
        _sqliteconstants.SQLITE_GENERAL_TYPE.NDARRAY:
            lambda x: _ndarray.getNDArray(
                _ndarray.NDArray.fromjson(x),
                data_dir),
    }

    return converter[fixed_type](value) # type: ignore
