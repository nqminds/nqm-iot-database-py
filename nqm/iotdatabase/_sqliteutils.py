import sys
if sys.version_info >= (3, 7):
    from __future__ import annotations
import urllib.parse
import os
import enum
class DbTypeEnum(enum.Enum):
    memory = "memory"
    file = "file"

class DbModeEnum(enum.Enum):
    readonly = "r"
    readwrite = "rw"
    readwrite2 = "wr"
    readwritecreate = "w+"

def sqliteURI(
    path: os.PathLike,
    type: DbTypeEnum,
    mode: DbModeEnum):
    """ Creates a URI for opening an SQLite Connection

    See https://www.sqlite.org/uri.html
    
    Args:
        path: The path of the db.
        type: The type of the db: `"file"` or `"memory"`
        mode: The open mode of the db: `"w+"`, `"rw"`, or `"r"`
    """
    modeMap = {
        DbTypeEnum.memory: "memory",
        DbModeEnum.readonly: "ro",
        DbTypeEnum.readwrite: "rw",
        DbTypeEnum.readwrite2: "rw",
        DbTypeEnum.readwritecreate: "rwc"
    }
    return urllib.parse.urlunparse(urllib.parse.ParseResult(
        scheme="file",
        netloc="",
        path=urllib.parse.quote(path),
        params="",
        query=urllib.parse.urlencode({
            # set mode to memory in type is memory, else use the types
            mode: modeMap[type] if type in modeMap else modeMap[mode]
        })
    ))
