import enum

class TDX_TYPE(enum.Enum):
    """Valid TDX schema types
    """
    NAME = "__tdxType"
    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"
    INT = "INT"
    REAL = "/*REAL|FLOA|DOUB"
    DATE = "date"

class SQLITE_TYPE(enum.Enum):
    """Valid sqlite schema types
    """
    NUMERIC = "NUMERIC"
    INTEGER = "INTEGER"
    REAL = "REAL"
    TEXT = "TEXT"

class SQLITE_SORT_TYPE(enum.Enum):
    ASC = "ASC"
    DESC = "DESC"

class TDX(enum.Enum):
    TYPE = TDX_TYPE

class SQLITE(enum.Enum):
    TYPE = SQLITE_TYPE
    SORT_TYPE = SQLITE_SORT_TYPE
    QUERY_LIMIT = 1000
    NULL = "null"

class SqliteConstants(enum.Enum):
    DATABASE_INFO_TABLE_NAME = "info"
    DATABASE_DATA_TABLE_NAME = "data"
    DATABASE_TABLE_INDEX_NAME = "dataindex"
    TDX = TDX
    SQLITE = SQLITE

# exports all the enum members to the module namespace
globals().update(SqliteConstants.__members__)
