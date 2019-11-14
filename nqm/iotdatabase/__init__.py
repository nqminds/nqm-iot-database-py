"""Library for accessing a local nqm-iot-database

Supports Mongo-style queries.

See :mod:`nqm.iotdatabase.database` for more API documentation.

Example:
    >>> from nqm.iotdatabase import Database
    >>> import numpy as np
    >>> # opens a in-memory Database, creating it if it does not exist
    >>> # use Database("./path/to/file.sqlite", "file", "w+") for files
    >>> db = Database("", "memory", "w+")
    >>> schema = {
    ...     "dataSchema":
    ...         {"a": {"__tdxType": ["ndarray"]}, # column a type ndarray
    ...          "b": {"__tdxType": ["string"]}}, # column b type string
    ...     "uniqueIndex": [{"asc": "b"}], # unique index (primary key)
    ... }
    >>> # makes new db if it does not exist, otherwise checks for valid schema
    >>> db_id = db.createDatabase(schema=schema)
    >>> row = {"a": np.array([[0, 1],[2, 3]]), "b": "hello world"}
    >>> db.addData([row]) == {"count": 1} # insert data into dataset
    True
    >>> rows = db.getData(filter={"b": "hello world"}).data # get data from db
    >>> rows[0]["b"] == row["b"] and np.array_equal(rows[0]["a"], row["a"])
    True
"""
from .database import Database

__version__ = "1.1.5"
