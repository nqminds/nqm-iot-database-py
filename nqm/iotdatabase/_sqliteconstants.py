# pylint: disable=invalid-name
"""Stores constants for library"""
import enum
import re

class ConstEnum(enum.Enum):
    """Same as a ConstEnum, except __str__ is the value not the name"""
    def __str__(self):
        return self.value

class TDX_TYPE(ConstEnum):
    """Valid TDX schema types
    """
    NAME = "__tdxType"
    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"
    INT = "INT"
    REAL = re.compile(r"REAL|FLOA|DOUB")
    DATE = "date"
    NDARRAY = "ndarray"
    OBJECT = "object"
    ARRAY = "array"

class SQLITE_TYPE(ConstEnum):
    """Valid sqlite schema types
    """
    NUMERIC = "NUMERIC"
    INTEGER = "INTEGER"
    REAL = "REAL"
    TEXT = "TEXT"

class SQLITE_GENERAL_TYPE(ConstEnum):
    """General sqlite schema types added for conversion purposes
    """
    OBJECT = "OBJECT"
    ARRAY = "ARRAY"
    NDARRAY = "NDARRAY"

class SQLITE_SORT_TYPE(ConstEnum):
    """Stores the SQLite string used to determine the sort direction"""
    ASC = "ASC"
    DESC = "DESC"

class TDX_SORT_TYPE(ConstEnum):
    """Stores the TDX string used to determine the sort direction"""
    ASC = "asc"
    DESC = "desc"

class TDX(ConstEnum):
    """Namespace class so TDX_TYPE can be used as TDX.TYPE"""
    TYPE = TDX_TYPE
    SORT_TYPE = TDX_SORT_TYPE

class SQLITE(ConstEnum):
    """Stores Enums releated to SQLITE"""
    TYPE = SQLITE_TYPE
    SORT_TYPE = SQLITE_SORT_TYPE
    GENERAL_TYPE = SQLITE_GENERAL_TYPE
    QUERY_LIMIT = 1000
    NULL = "null"

class DATABASE(ConstEnum):
    """Stores database constants"""
    INFO_TABLE_NAME = "info"
    SCHEMA_KEY = "schema" # the metadata key to store the schema def
    DATA_TABLE_NAME = "data"
    DATA_FOLDER_SUFFIX = ".d"
    TABLE_INDEX_NAME = "dataindex"

# exports all the enum members to the module namespace
DATABASE_INFO_TABLE_NAME = DATABASE.INFO_TABLE_NAME
DATABASE_DATA_TABLE_NAME = DATABASE.DATA_TABLE_NAME
DATABASE_TABLE_INDEX_NAME = DATABASE.TABLE_INDEX_NAME
SCHEMA_KEY = DATABASE.SCHEMA_KEY
