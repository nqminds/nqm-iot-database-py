""" Manages the info table in a dataset
"""
import sys
import typing
# sqlalchemy core is much faster than the monqosql/sqlalchemy.orm stuff
# but doesn't support the amazing query language
import sqlalchemy
# used for cool mongosql queries
import sqlalchemy.orm
import sqlalchemy.ext.declarative
import mongosql
from . import _sqliteschemaconverter as schemaconverter
from . import _sqliteconstants

DATABASE_INFO_TABLE_NAME = _sqliteconstants.DATABASE_INFO_TABLE_NAME
SQLITE_TXT = _sqliteconstants.SQLITE_TYPE.TEXT
SQLITE_OBJ = _sqliteconstants.SQLITE_GENERAL_TYPE.OBJECT

Base = sqlalchemy.ext.declarative.declarative_base(
    cls=(mongosql.MongoSqlBase,))

class Info(Base): # type: ignore
    __tablename__ = DATABASE_INFO_TABLE_NAME
    # need to set quote=True else key might be converted to KEY
    key = sqlalchemy.Column(sqlalchemy.String, name="key",
        primary_key=True, quote=True)
    value = sqlalchemy.Column(sqlalchemy.String, name="value", quote=True)

info_table = Info.__table__

def createInfoTable(db: sqlalchemy.engine.Engine) -> None:
    """Creates the info table."""
    info_table.create(db)

def checkInfoTable(db: sqlalchemy.engine.Engine) -> bool:
    """Checks if info table exists.

    Args:
        db: The sqlite3 db Engine from sqlalchemy
    """
    return info_table.exists(db) # type: ignore

def getInfoKeys(
    db: sqlalchemy.engine.Engine,
    keys: typing.Iterable[typing.Text],
    sessionMaker: typing.Callable[[], sqlalchemy.orm.session.Session] = None
) -> typing.Dict[typing.Text, schemaconverter.JSONified]:
    """Gets some rows from the info table.

    Args:
        db: The sqlite3 db Engine from sqlalchemy
        keys: A list of the primary keys of the row you want to get.
            If this is false-y (ie empty), return all rows.
        sessionMaker: Function to that returns an sqlalchemy Session to use
            for querying data.
    Returns:
        A dict of the row keys to the rows
    """
    if not sessionMaker:
        sessionMaker = sqlalchemy.orm.sessionmaker(bind=db)
    session = sessionMaker()

    if keys:
        filterquery = {"key": {"$in": list(keys)}}
    else:
        filterquery = {} # get all keys

    query = Info.mongoquery(session.query(Info.key, Info.value)
        ).query(filter=filterquery).end()

    results = {
        key: schemaconverter.convertToTdx(SQLITE_OBJ, str(val))
        for key, val in query.all()}

    session.close()
    return results

def setInfoKeys(
    db: sqlalchemy.engine.Engine,
    keys: typing.Mapping[typing.Text, typing.Text]
):
    rowcount = 0
    sqlite_keys = {
        schemaconverter.convertToSqlite(SQLITE_TXT, key, True):
            schemaconverter.convertToSqlite(SQLITE_OBJ, val, True)
        for key, val in keys.items()
    }
    # if empty keys do nothing
    if len(keys) > 0:
        conn = db.connect()
        res = conn.execute(
            info_table.insert(),
            [{"key": key, "value": value} for key, value in sqlite_keys.items()]
        )
        rowcount = res.rowcount
        conn.close()
    return {"count": rowcount}
