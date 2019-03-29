import typing as t

import pathlib
import os
from .database import Database
from . import _sqliteutils
from . import _sqliteinfotable
from . import _sqliteschemaconverter as schemaconverter
import sqlite3
import sqlalchemy
import sqlalchemy.engine

DbTypeEnum = _sqliteutils.DbTypeEnum

def openDatabase(path: t.Union([t.Text, os.PathLike]),
        type: t.Union([t.Text, DbTypeEnum]),
        mode: t.Union([t.Text, _sqliteutils.DbModeEnum])
    ) -> Database:
    """ Opens an SQLite database. Creates if none exists.

    Args:
        path: The path of the db.
        type: The type of the db: `"file"` or `"memory"`
        mode: The open mode of the db: `"w+"`, `"rw"`, or `"r"`
    
    Returns:
        The open Database
    """
    return Database().openDatabase(path=path, type=type, mode=mode)
