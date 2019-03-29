"""Stores util functions for SQLite"""
import urllib.parse
import os
import enum
import typing
import re
from ._sqliteconstants import ConstEnum
import sqlalchemy.engine.url

class DbTypeEnum(ConstEnum):
    memory = "memory"
    file = "file"

class DbModeEnum(ConstEnum):
    readonly = "r"
    readwrite = "rw"
    readwrite2 = "wr"
    readwritecreate = "w+"

def sqliteURI(
    path: typing.Union[os.PathLike, typing.Text] = None,
    type: typing.Union[DbTypeEnum, typing.Text] = DbTypeEnum.file,
    mode: typing.Union[DbModeEnum, typing.Text] = DbModeEnum.readwritecreate
) -> typing.Text:
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
        DbModeEnum.readwrite: "rw",
        DbModeEnum.readwrite2: "rw",
        DbModeEnum.readwritecreate: "rwc"
    }
    dbType = DbTypeEnum(type)
    dbMode = DbModeEnum(mode)
    return urllib.parse.urlunparse(urllib.parse.ParseResult(
        scheme="file",
        netloc="",
        path=urllib.parse.quote(str(path)),
        params="",
        query=urllib.parse.urlencode({
            # set mode to memory in type is memory, else use the types
            "mode": modeMap[dbType] if dbType in modeMap else modeMap[dbMode]
        }),
        fragment=""
    ))

def sqlAlchemyURL(
    path: typing.Union[os.PathLike, typing.Text] = None,
    type: typing.Union[DbTypeEnum, typing.Text] = DbTypeEnum.file,
    mode: typing.Union[DbModeEnum, typing.Text] = DbModeEnum.readwritecreate
) -> sqlalchemy.engine.url.URL:
    """ Creates an SQLAlchemy URL for opening an SQLite Connection
    """
    dbType = DbTypeEnum(type)
    dbMode = DbModeEnum(mode)
    if dbMode is not DbModeEnum.readwritecreate:
        raise NotImplementedError(
            "There is currently no way to set open modes in SQLAlchemy.")

    return sqlalchemy.engine.url.URL(
        drivername="sqlite",
        database=":memory:" if dbType is DbTypeEnum.memory else str(path)
    )

def escapeIdentifier(identifier: typing.Text) -> typing.Text:
    """Escapes an SQLite Identifier, e.g. a column name.

    This will prevent SQLite injections, and column names being incorrectly
    classified as string literal values.

    Mixing up the quotes (ie using ' instead of ")
    can cause unexpected behaviour,
    since SQLite guesses whether something is a column-name or a variable.

    Args:
        identifier: The identifier that you want to escape, ie the column name.

    Returns:
        The escaped identifier for using in an SQLite Statement String.
    """
    # escapes all " with "" and adds " at the beginning/end
    return '"{}"'.format(identifier.replace('"', '""'))

def _escapeChar(match) -> typing.Text:
    """Escapes a character using HTML standard.

    Args:
        char: The regex match containing the char to be escaped.

    Returns:
        The escaped char, ie "%4A" for "J"
    """
    return "%{:X}".format(ord(match.get(0)))

parameter_regex = re.compile(r"[\%\x09\x0a\x0c\x0d\x20\)]")
def makeNamedParameter(named_parameter: typing.Text) -> typing.Text:
    """Create a parameter for use in bind variables to SQLite statements.

    This creates a 1-to-1 mapping of column name to named parameter.
    It escapes the chars shown in
    <https://stackoverflow.com/a/51574648/10149169> using &hex style encoding.

    Args:
        named_parameter: The name of the parameter.

    Returns:
        The string to use when binding.
    """
    escaped_param = parameter_regex.sub(_escapeChar, named_parameter)
    return ":a({})".format(escaped_param)
