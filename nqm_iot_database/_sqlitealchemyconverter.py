import typing as t
import sqlalchemy
import sqlalchemy.types
import sqlalchemy.engine
import sqlalchemy.event

import ._sqliteconstants as _sqliteconstants
import ._sqliteschemaconverter as schemaconverter

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
    _sqliteconstants.SQLITE_TYPE.NUMERIC: sqlalchemy.types.Numeric,
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
    table: sqlalchemy.Table,
    columns: t.Mapping[t.Text, sqlalchemy.sql.expression.ColumnElement],
    tdx_schema: schemaconverter.TDXSchema
):
    """Makes the unique and non-unique indexes for a table.

    Args:
        table: The uncreated SQLAlchemy table to add the indexes to.
        columns: A dict of {col: sqlalchemy columns}
        tdx_schema: The TDX Schema containing the index specification.
    """
    primary_index = t.cast(
        t.Sequence[SortCol], tdx_schema["uniqueIndex"])
    p_args = [makeIndexArg(x, columns) for x in primary_index]
    if p_args: # make primary key constraint if it exists
        table.append_constraint(sqlalchemy.PrimaryKeyConstraint(
            *p_args, name=str(_sqliteconstants.DATABASE_TABLE_INDEX_NAME)
        ))
    
    non_unique_indexes = t.cast(
        t.Sequence[t.Sequence[SortCol]],
        tdx_schema.get("nonUniqueIndexes", []))
    for index in non_unique_indexes:
        i_args = [makeIndexArg(x, columns) for x in index]
        table.append_constraint(sqlalchemy.schema.Index(
            *i_args
        ))

def makeDataTable(
    connection: sqlalchemy.engine.Engine,
    sqliteSchema: t.Mapping[t.Text, _sqliteconstants.SQLITE_TYPE],
    tdxSchema: schemaconverter.TDXSchema
) -> sqlalchemy.Table:
    """Makes an SQLAlchemy table for storing data based on a TDX Schema.

    Args:
        connection: The SQLAlchemy Engine that has the database information.
        sqliteSchema: The SQLite Schema of {column_name: column_type}
        tdxSchema: The TDX schema with the index specification.

    Returns:
        The uncreated SQLAlchemy table specification.
    """
    metadata = sqlalchemy.MetaData(connection)
    Data = sqlalchemy.Table(
        _sqliteconstants.DATABASE_DATA_TABLE_NAME, metadata, quote=True)
    # store the created columns for creating the indexes later
    columns = dict()
    for column, sqlite_type in sqliteSchema.items():
        new_col = sqlalchemy.schema.Column(
            name=column,
            type_=convertToSqlAlchemy(sqlite_type)
        )
        Data.append_column(new_col)
        columns[column] = Data.c.__getattr__(column)

    makeIndexes(Data, columns, tdxSchema)
    return Data
