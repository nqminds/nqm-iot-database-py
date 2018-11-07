"""Module to convert a tdx schema into a sqlite schema.
"""
import sys
if sys.version_info >= (3, 7):
    from __future__ import annotations
import typing
import numbers
import _sqliteconstants

sqlite_types = typing.Union([int, float, typing.Text, numbers.Real])

def convertToSqlite(
    type: _sqliteconstants.SQLITE_TYPE,
    value: typing.Any,
    only_stringify = False: bool
    ) -> sqlite_types:
    """Converts a tdx value to a sqlite value based on a sqlite type.

    Args:
        type: Sqlite type to convert the value to
        value: TDX value to convert
        only_stringify: Set to `True` to turn off escaping single-quotes and
            delimiter addition.
            This shouldn't be required as one should bind strings to SQLite
            statements to avoid SQL injections anyway.
    """
    pass
