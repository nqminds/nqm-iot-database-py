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
from nqm.iotdatabase._sqliteschemaconverter import convertToSqlite, convertToTdx
import nqm.iotdatabase._sqliteconstants as _sqliteconstants

DATABASE_INFO_TABLE_NAME = _sqliteconstants.DATABASE_INFO_TABLE_NAME
SQLITE_TXT = _sqliteconstants.SQLITE_TYPE.TEXT
SQLITE_OBJ = _sqliteconstants.SQLITE_GENERAL_TYPE.OBJECT

Base = sqlalchemy.ext.declarative.declarative_base(cls=(mongosql.MongoSqlBase,))

class Info(Base):
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
        db: The sqlite3 db connection from module sqlite3
    """
    return info_table.exists(db)

def getInfoKeys(
    db: sqlalchemy.engine.Engine,
    keys: typing.Iterable[typing.Text]
) -> typing.Dict[typing.Text, typing.Text]:
    session = sqlalchemy.orm.session.Session(db)
    query = Info.mongoquery(session.query(Info.key, Info.value)).filter(
        {"keys": {"$in": keys}}
    ).end()
    return {key: value for key, value in query.all()}

def setInfoKeys(
    db: sqlalchemy.engine.Engine,
    keys: typing.Mapping[typing.Text, typing.Text]
) -> typing.Dict["count", int]:
    rowcount = 0
    sqlite_keys = {
        convertToSqlite(SQLITE_TXT, key):
            convertToSqlite(SQLITE_OBJ, val)
        for key, val in keys.items()}
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
