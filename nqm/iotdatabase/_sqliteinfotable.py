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
import nqm.iotdatabase._sqliteschemaconverter as _sqliteschemaconverter
import nqm.iotdatabase._sqliteconstants as _sqliteconstants

DATABASE_INFO_TABLE_NAME = "info"

Base = sqlalchemy.ext.declarative.declarative_base(cls=(mongosql.MongoSqlBase,))

class Info(Base):
    __tablename__ = DATABASE_INFO_TABLE_NAME
    # need to set quote=True else key might be converted to KEY
    key = sqlalchemy.Column(sqlalchemy.String, primary_key=True, quote=True),
    value = sqlalchemy.Column(sqlalchemy.String, quote=True)

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
    keys: typing.Mapping[typing.Text, typing.Text]):
    conn = db.connect()
    conn.execute(
        info_table.insert(),
        [{"key": key, "value": value} for key, value in keys.items()]
    )
    conn.close()
