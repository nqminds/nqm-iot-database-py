"""Stores util functions for SQLite"""
import urllib.parse
import os
import enum
import typing
import re
from nqm.iotdatabase._sqliteconstants import ConstEnum

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
    mode: typing.Union[DbModeEnum, typing.Text] = DbModeEnum.readwrite):
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

def _escapeChar(char: typing.Text) -> typing.Text:
    """Escapes a character using HTML standard.

    Args:
        char: The string contain the char to be escaped.

    Returns:
        The escaped char, ie "%4A" for "J"
    """
    return "%{:X}".format(ord(char))

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
