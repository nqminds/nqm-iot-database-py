"""
"""
import sys
if sys.version_info >= (3, 7):
    from __future__ import annotations

import typings
import enum
import os
import _sqliteutils
import _sqliteinfotable
import sqlite3

class DbTypeEnum(enum):
    memory = "memory"
    file = "file"

class DbModeEnum(enum):
    readonly = "r"
    readwrite = "rw"
    readwrite2 = "wr"
    readwritecreate = "w+"

class Database(object):
    def __init__(self,
        path: typings.Union([str, os.PathLike]),
        type: typings.Union([DbTypeEnum, str]),
        mode: typings.Union([DbModeEnum, str])
    ):
        """ Opens an SQLite database. Creates if none exists.

        Args:
            path: The path of the db.
            type: The type of the db: `"file"` or `"memory"`
            mode: The open mode of the db: `"w+"`, `"rw"`, or `"r"`
        """
        typeEnum = DbTypeEnum(type)
        if typeEnum == DbTypeEnum.file:
            # makes the directory the sqlite db is in
            os.makedirs(os.path.dirname(path))

        uri = _sqliteutils.sqliteURI(
            os.Path(path), typeEnum, DbModeEnum(mode))
        # creates the sqlite3 connection
        connection = sqlite3.connect(uri)
        
        id = shortid.generate()
        schema = dict()
        if _sqliteinfotable.checkInfoTable(connection):
            
