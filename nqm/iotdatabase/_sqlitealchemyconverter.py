import typing as t
import sqlalchemy
import sqlalchemy.types
import sqlalchemy.engine

import nqm.iotdatabase._sqliteconstants as _sqliteconstants
import nqm.iotdatabase._sqliteschemaconverter as schemaconverter

sqlalchemyMap: t.Mapping[
    _sqliteconstants.SQLITE_TYPE, sqlalchemy.types.TypeEngine
] = {
    _sqliteconstants.SQLITE_TYPE.INTEGER: sqlalchemy.types.Integer,
    _sqliteconstants.SQLITE_TYPE.TEXT: sqlalchemy.types.String,
    _sqliteconstants.SQLITE_TYPE.NUMERIC: sqlalchemy.types.Numeric,
    _sqliteconstants.SQLITE_TYPE.INTEGER: sqlalchemy.types.Integer
}
def convertToSqlAlchemy(
    sqlite_type: _sqliteconstants.SQLITE_TYPE
): return sqlalchemyMap[sqlite_type]

def makeIndexArg(
    schema_column: t.Mapping[t.Text, t.Text],
    columns: t.Mapping[t.Text, sqlalchemy.sql.expression.ColumnElement]
):
    if len(schema_column) != 1:
        raise ValueError(("[sqlite-alchemy-converter] schema_column has {}"
            " values instead of the expected 1."
            " Should look like {{asc: column}}").format(len(schema_column)))
    order, column_name = next(schema_column.items())
    sort_order = None

    try:
        sort_order = _sqliteconstants.SQLITE_SORT_TYPE(order)
    except ValueError as e:
        raise ValueError(("[sqlite-alchemy-converter] schema_column "
            " sort_order='{}' did not match field in {}.").format(
                order, _sqliteconstants.SQLITE_SORT_TYPE))

    column = columns[column_name]
    if sort_order is _sqliteconstants.SQLITE_SORT_TYPE.DESC:
        return column.desc
    elif sort_order is _sqliteconstants.SQLITE_SORT_TYPE.ASC:
        return column.asc

def makeIndexes(
    table: sqlalchemy.Table,
    columns: t.Mapping[t.Text, sqlalchemy.sql.expression.ColumnElement],
    tdx_schema: schemaconverter.TDXSchema
):
    primary_index = tdx_schema["uniqueIndex"]
    p_args = [makeIndexArg(x, columns) for x in primary_index]
    table.append_constraint(sqlalchemy.PrimaryKeyConstraint(
        *p_args, name=_sqliteconstants.DATABASE_TABLE_INDEX_NAME
    ))
    
    non_unique_indexes = tdx_schema["nonUniqueIndexes"]
    for index in non_unique_indexes:
        i_args = [makeIndexArg(x, columns) for x in index]
        table.append_constraint(sqlalchemy.schema.Index(
            *i_args
        ))

def makeTable(
    connection: sqlalchemy.engine.Engine,
    sqliteSchema: t.Mapping[t.Text, _sqliteconstants.SQLITE_TYPE],
    tdxSchema: schemaconverter.TDXSchema
) -> sqlalchemy.Table:
    metadata = sqlalchemy.MetaData(connection)
    Data = sqlalchemy.Table(
        _sqliteconstants.DATABASE_DATA_TABLE_NAME, metadata, quote=True)
    # store the created columns for creating the indexes later
    columns = dict()
    for column, sqlite_type in sqliteSchema.items():
        new_col = sqlalchemy.schema.Column(
            name=column,
            type=convertToSqlAlchemy(sqlite_type)
        )
        Data.append_column(new_col)
        columns[column] = new_col

    makeIndexes(Data, columns, tdxSchema)
    return Data
