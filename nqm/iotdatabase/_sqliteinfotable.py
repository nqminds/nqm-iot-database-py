""" Manages the info table in a dataset
"""
import sys
if sys.version_info >= (3, 7):
    from __future__ import annotations

import typing
import sqlite3

import _sqliteschemaconverter
import _sqliteconstants

DATABASE_INFO_TABLE_NAME = "info"

def checkInfoTable(db: sqlite3.Connection) -> bool:
    """Checks if info table exists.

    Args:
        db: The sqlite3 db connection from module sqlite3
    """
    cursor = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")
    for row in cursor:
        if row["name"] == DATABASE_INFO_TABLE_NAME:
            return True
    return False

def getInfoKeys(
    db: sqlite3.Connection, keys: typing.Iterable[str]
) -> typing.Iterable[typing.Mapping[str]]:
    _sqliteschemaconverter.convertToSqlite(_sqliteconstants.SQLITE_TYPE_TEXT)
    pass
