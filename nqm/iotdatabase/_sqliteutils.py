"""Stores util functions for SQLite"""
import urllib.parse
import os
import typing
import re
from ._sqliteconstants import ConstEnum
import sqlite3

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

    See https://www.sqlite.org/uri.html.

    Args:
        path: The path of the db.
        type: The type of the db: `"file"` or `"memory"`.
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
    if not path:
        if dbType is DbTypeEnum.memory:
            path = ":memory:" # make an unshared in-memory db
        else:
            raise TypeError(
                f"path={path} is must be a truthy value of type={type}.")
    if dbType is DbTypeEnum.file:
        path = os.path.abspath(path)
    return urllib.parse.urlunparse(urllib.parse.ParseResult(
        scheme="file",
        netloc="localhost",
        path=urllib.parse.quote(str(path)),
        params="",
        query=urllib.parse.urlencode({
            # set mode to memory in type is memory, else use the types
            "mode": modeMap[dbType] if dbType in modeMap else modeMap[dbMode]
        }),
        fragment=""
    ))

def sqlAlchemyEngineCreator(
    path: typing.Union[os.PathLike, typing.Text] = None,
    type: typing.Union[DbTypeEnum, typing.Text] = DbTypeEnum.file,
    mode: typing.Union[DbModeEnum, typing.Text] = DbModeEnum.readwritecreate
) -> typing.Callable[[], sqlite3.Connection]:
    """ Creates an SQLAlchemy Engine creator for opening an SQLite Connection.

    Arguments:
        path:
            The path to the desired file.
            One can leave this empty if an in-memory db is wanted.
        type: If this is a file db or an in-memory db.
        mode:
            Whether to open this in readonly, read-write,
            or read-write-create mode.

    Returns:
        A function that can be passed as the ``creator`` ``kwarg`` in
        `sqlalchemy.create_engine`.

    Example:

        > import sqlalchemy
        > from nqm.iotdatabase._sqliteutils import sqlAlchemyEngineCreator
        > creator = sqlAlchemyEngineCreator("/tmp/example.sqlite", "file", "rw")
        > db = sqlalchemy.create_engine("sqlite:///", creator=creator)
    """

    uri = sqliteURI(path=path, type=type, mode=mode)
    def create_connection():
        try:
            return sqlite3.connect(uri, uri=True)
        except sqlite3.OperationalError as error:
            raise sqlite3.OperationalError(
                f"Opening database with uri {uri} failed with issue {error}")

    return create_connection

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
