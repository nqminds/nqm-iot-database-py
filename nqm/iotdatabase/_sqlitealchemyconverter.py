import typing as t
import sqlalchemy
import sqlalchemy.types
import sqlalchemy.engine
import sqlalchemy.event

import mongosql

from . import _sqliteconstants
from . import _sqliteschemaconverter as schemaconverter

@sqlalchemy.event.listens_for(sqlalchemy.engine.Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Sets the DB to WAL mode to boost speed on all connections."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()

sqlalchemyMap: t.Dict[
    _sqliteconstants.SQLITE_TYPE, sqlalchemy.types.TypeEngine
] = {
    _sqliteconstants.SQLITE_TYPE.INTEGER: sqlalchemy.types.Integer,
    _sqliteconstants.SQLITE_TYPE.TEXT: sqlalchemy.types.String,
    _sqliteconstants.SQLITE_TYPE.NUMERIC: sqlalchemy.types.REAL,
    _sqliteconstants.SQLITE_TYPE.REAL: sqlalchemy.types.REAL,
    _sqliteconstants.SQLITE_TYPE.INTEGER: sqlalchemy.types.Integer
}
"""Map of SQLITE_TYPE to their corresponding sqlalchemy type"""

SortCol = t.Mapping[t.Text, t.Text]
"""A dict of {"asc": col} or {"desc": col}"""

def convertToSqlAlchemy(
    sqlite_type: _sqliteconstants.SQLITE_TYPE
): return sqlalchemyMap[sqlite_type]

def makeIndexArg(
    schema_column: SortCol,
    columns: t.Mapping[t.Text, sqlalchemy.sql.expression.ColumnElement]
):
    """Return an arg that can be used for creating indexes

    Args:
        schema_column: A dict of {"asc": col} or {"desc": col}
        columns: A dict of {col: sqlalchemy columns}

    Returns:
        An arg that can be passed to sqlalchemy.PrimaryKeyConstraint
    """
    if len(schema_column) != 1:
        raise ValueError(("[sqlite-alchemy-converter] schema_column has {}"
            " values instead of the expected 1."
            " Should look like {{asc: column}}").format(len(schema_column)))
    order, column_name = next(iter(schema_column.items())) # first element
    sort_order = None

    try:
        sort_order = _sqliteconstants.TDX_SORT_TYPE(order)
    except ValueError as e:
        raise ValueError(("[sqlite-alchemy-converter] schema_column "
            " sort_order='{}' did not match field in {}.").format(
                order, _sqliteconstants.TDX_SORT_TYPE))

    column = columns[column_name]
    sort_condition = None
    # sorting is currently not supported by SQLAlchemy in primary keys
    # TODO: Make pull request/fork in SQLAlchemy
    if sort_order is _sqliteconstants.TDX_SORT_TYPE.DESC:
        sort_condition = column.desc()
    elif sort_order is _sqliteconstants.TDX_SORT_TYPE.ASC:
        sort_condition = column.asc()

    return column

def makeIndexes(
    columns: t.MutableMapping[t.Text, sqlalchemy.sql.expression.ColumnElement],
    tdx_schema: schemaconverter.TDXSchema
) -> None:
    """Makes the unique and non-unique indexes for a inplace.

    Args:
        columns: A dict of {col: sqlalchemy columns}. Mutated.
            These can then be passed as the attributes of a new
            ORM class.
            The ``"__table_args__"`` of the field will be modified to hold
            the indexes.
        tdx_schema: The TDX Schema containing the index specification.

    Example:
        >>> import nqm.iotdatabase._sqlitealchemyconverter as convert
        >>> from sqlalchemy.ext.declarative import declarative_base
        >>> from sqlalchemy import Column, String
        >>> Base = declarative_base()
        >>> columns = {"name": Column(String)}
        >>> schema = {"uniqueIndex": [{"asc": "name"}]}
        >>> convert.makeIndexes(columns, schema)
        >>> NameModel = type("NameModel", (Base,), columns)
    """
    table_args = []
    primary_index = t.cast(
        t.Sequence[SortCol], tdx_schema["uniqueIndex"])
    p_args = [makeIndexArg(x, columns) for x in primary_index]
    if p_args: # make primary key constraint if it exists
        table_args.append(sqlalchemy.PrimaryKeyConstraint(
            *p_args, name=str(_sqliteconstants.DATABASE_TABLE_INDEX_NAME)
        ))
    else:
        # make an interger primary key if no other primary key exists
        # SQLAlchemy ORM requires a primary key
        rowid_name = "_id"
        columns[rowid_name] = sqlalchemy.schema.Column(
            name=rowid_name,
            type_=sqlalchemy.INTEGER,
            primary_key=True, quote=True)

    non_unique_indexes = t.cast(
        t.Sequence[t.Sequence[SortCol]],
        tdx_schema.get("nonUniqueIndexes", []))
    for index in non_unique_indexes:
        i_args = [makeIndexArg(x, columns) for x in index]
        table_args.append(sqlalchemy.schema.Index(
            *i_args
        ))

    columns["__table_args__"] = tuple(table_args)

def makeDataModel(
    connection: sqlalchemy.engine.Engine,
    sqliteSchema: t.Mapping[t.Text, _sqliteconstants.SQLITE_TYPE],
    tdxSchema: schemaconverter.TDXSchema
) -> mongosql.MongoSqlBase:
    """Makes an SQLAlchemy ORM (model) for storing data based on a TDX Schema.

    Args:
        connection: The SQLAlchemy Engine that has the database information.
        sqliteSchema: The SQLite Schema of {column_name: column_type}
        tdxSchema: The TDX schema with the index specification.

    Returns:
        The SQLAlchemy ORM with table specification.
    """
    Base = sqlalchemy.ext.declarative.declarative_base(
        cls=(mongosql.MongoSqlBase,))
    columns = {
        "__tablename__": _sqliteconstants.DATABASE_DATA_TABLE_NAME
    }
    # store the created columns for creating the indexes later
    for column, sqlite_type in sqliteSchema.items():
        type_ = convertToSqlAlchemy(sqlite_type)
        new_col = sqlalchemy.schema.Column(
            name=column,
            type_=type_,
            quote=True, # make sure column name is exactly what is given
        )
        columns[column] = new_col

    makeIndexes(columns, tdxSchema)
    # makes a new class Data that inherits from Base that has the attrs
    # given in columns
    return type("Data", (Base,), columns)
