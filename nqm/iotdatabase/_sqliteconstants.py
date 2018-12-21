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

class SQLITE_SORT_TYPE(ConstEnum):
    ASC = "ASC"
    DESC = "DESC"

class TDX_SORT_TYPE(ConstEnum):
    ASC = "asc"
    DESC = "desc"

class TDX(ConstEnum):
    TYPE = TDX_TYPE

class SQLITE(ConstEnum):
    TYPE = SQLITE_TYPE
    SORT_TYPE = SQLITE_SORT_TYPE
    GENERAL_TYPE = SQLITE_GENERAL_TYPE
    QUERY_LIMIT = 1000
    NULL = "null"

class SqliteConstants(ConstEnum):
    DATABASE_INFO_TABLE_NAME = "info"
    DATABASE_DATA_TABLE_NAME = "data"
    DATABASE_TABLE_INDEX_NAME = "dataindex"

# exports all the enum members to the module namespace
DATABASE_INFO_TABLE_NAME = SqliteConstants.DATABASE_INFO_TABLE_NAME
DATABASE_DATA_TABLE_NAME = SqliteConstants.DATABASE_DATA_TABLE_NAME
DATABASE_TABLE_INDEX_NAME = SqliteConstants.DATABASE_TABLE_INDEX_NAME
