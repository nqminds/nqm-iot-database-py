"""Module for controlling an NQM InterliNQ Database in Python

See the class `Database` for more info.
"""
import typing as t

import pathlib
import os
import tempfile # used for in-memory dbs
import sqlalchemy
import sqlalchemy.engine
import sqlalchemy.dialects.postgresql

import shortuuid

from . import _sqliteconstants
from . import _sqliteutils
from . import _sqliteinfotable
from . import _sqliteschemaconverter as schemaconverter
from . import _sqlitealchemyconverter

DbTypeEnum = _sqliteutils.DbTypeEnum
TDXSchema = schemaconverter.TDXSchema
AddDataResult = t.NewType("AddDataResult", dict)

class Database(object):
    """An instance of an NQM InterliNQ Database.

    Uses SQLite as a backend, but allows for TDX-style commands.

    Attributes:
        general: The SQLite General Schema.
        sqlEngine: The `sqlalchemy` engine used for this connection.
        table: The `sqlalchemy` data table.
        tdx_schema: The `TDXSchema` used by this dataset.
        tdx_data_schema: The `tdx_data_schema` for the data.
        data_dir:
            The location of the data directory (for saving ndarrays to file)
    """
    general_schema: schemaconverter.GeneralSchema
    sqlEngine: sqlalchemy.engine.Engine
    table: sqlalchemy.Table = None
    tdx_schema: schemaconverter.TDXSchema = TDXSchema(dict())
    tdx_data_schema: schemaconverter.TDXDataSchema = dict()
    data_dir: t.Union[t.Text, os.PathLike] = ""

    def __init__(self,
        path: t.Union[t.Text, os.PathLike],
        type: t.Union[t.Text, DbTypeEnum],
        mode: t.Union[t.Text, _sqliteutils.DbModeEnum]
    ):
        """Opens an SQLite database using `openDatabase()`.

        Args:
            path: The path of the db.
            type: The type of the db: `"file"` or `"memory"`
            mode: The open mode of the db: `"w+"`, `"rw"`, or `"r"`
        """
        self.openDatabase(path, type, mode)

    def _load_tdx_schema(self):
        """Loads the TDX Schema from the info table and stores.

        Updates ``self.tdx_schema`` and ``self.tdx_data_schema``.
        """
        tdx_schema: TDXSchema = TDXSchema(dict())
        if _sqliteinfotable.checkInfoTable(self.sqlEngine):
            info_keys = _sqliteinfotable.getInfoKeys(
                self.sqlEngine, ["schema"])
            if info_keys: # lists are False is empty
                info_keys.setdefault("schema", dict())
                # dataset schema definition
                tdx_schema = info_keys["schema"]
                # dataset data schema
                tdx_schema.setdefault("dataSchema", dict())
        self.tdx_schema = tdx_schema
        self.tdx_data_schema = t.cast(
            schemaconverter.TDXDataSchema, tdx_schema["dataSchema"])

    def createDatabase(self,
        id: t.Text = None,
        schema: schemaconverter.TDXSchema = TDXSchema({}),
        **kargs
    ) -> t.Text:
        """Creates a dataset in the SQLite Database

        Args:
            id:
                the requested ID of the new resource. Must be unique.
                Will be auto-generated if omitted (recommended).
                Will be replaced with the original one if the db already is
                created.
            schema:
                schema definition. Should contain two fields:

                * ``dataSchema``: A dict containing the TDX data schema.
                
                * ``uniqueIndex``:
                    List of ``{"asc": column}`` or ``{"desc": column}``
                    specifying the unique primary key index.
            **kargs:
                Other arguments to store in the info table.
        Returns:
            The id of the dataset.
        """
        id = shortuuid.uuid() if id is None else id
        db = self.sqlEngine

        copiedTDXSchema = dict(schema.items())

        copiedTDXSchema.setdefault("dataSchema", {})
        copiedTDXSchema.setdefault("uniqueIndex", {})

        tdxSchema = TDXSchema(copiedTDXSchema)

        if not tdxSchema["dataSchema"] and tdxSchema["uniqueIndex"]:
            raise ValueError(("schema.dataSchema was empty, but"
                    " schema.uniqueIndex has a non.empty value of {}"
                ).format(tdxSchema["uniqueIndex"]))

        # convert the TDX schema to an SQLite schema and save it
        self.general_schema = schemaconverter.convertSchema(
            t.cast(schemaconverter.TDXDataSchema, tdxSchema["dataSchema"]))

        if _sqliteinfotable.checkInfoTable(db):
            # check if old id exists
            infovals = _sqliteinfotable.getInfoKeys(db, ["id"])
            # use the original id if we can find it
            id = str(infovals.get("id", id))

            # will raise an error if the schemas aren't compatible
            self.compatibleSchema(TDXSchema(tdxSchema), raise_error=True)
        else:
            # create infotable
            _sqliteinfotable.createInfoTable(db)
            info = kargs
            info["schema"] = tdxSchema
            info["id"] = id
            
            _sqliteinfotable.setInfoKeys(db, info)

        self._load_tdx_schema()

        sqlite_schema = schemaconverter.mapSchema(self.general_schema)

        if not sqlite_schema:
            # TODO Maybe add error (none now matches nqm-iot-database-utils)
            return id

        self.table = alchemyconverter.makeDataTable(
            db, sqlite_schema, tdxSchema)
        self.table.create(checkfirst=True) # create unless already exists
        return id

    def openDatabase(self,
        path: t.Union[t.Text, os.PathLike],
        type: t.Union[t.Text, DbTypeEnum],
        mode: t.Union[t.Text, _sqliteutils.DbModeEnum]
    ):
        """ Opens an SQLite database.

        Args:
            path: The path of the db.
            type: The type of the db: `"file"` or `"memory"`
            mode: The open mode of the db: `"w+"`, `"rw"`, or `"r"`
        """
        path_to_db = pathlib.Path(path)

        typeEnum = DbTypeEnum(type)
        if typeEnum is DbTypeEnum.file:
            # makes the directory the sqlite db is in
            os.makedirs(os.path.dirname(path), exist_ok=True)
            self.data_dir = path_to_db.with_suffix(
                str(_sqliteconstants.DATABASE.DATA_FOLDER_SUFFIX))
        else: # in-memory db
            # autodeleted when self is deleted
            self.__tmpdir = tempfile.TemporaryDirectory()
            self.data_dir = self.__tmpdir.name

        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(
            name = os.path.join(
                self.data_dir,
                str(_sqliteconstants.DATABASE.NDARR_FOLDER)),
            exist_ok=True) # makes the NDArray folder

        uri = _sqliteutils.sqlAlchemyURL(path_to_db, typeEnum, mode)
        # creates the sqlite3 connection
        self.sqlEngine = sqlalchemy.create_engine(uri)
        
        self.connection = self.sqlEngine.connect().execution_options(
            autocommit=True)
        return self

    def compatibleSchema(self,
        schema: schemaconverter.TDXSchema,
        raise_error: bool = True
    ) -> bool:
        """Checks whether the given schema is a subset of the db schema.

        Args:
            schema: The TDX Schema.
            raise_error: If

                * ``True``: raise errors if anything goes wrong
                * ``False``: Catch errors and return ``False`` if anything goes
                    wrong

        Raises:
            ValueError: If the schemas are not compatible and `raise_error` is
                `True`.
        """
        db_tdx_schema = self.tdx_schema
        # see https://stackoverflow.com/a/41579450/10149169
        is_subset = db_tdx_schema.items() <= schema.items()
        if not is_subset and raise_error:
            raise ValueError((
                    "The given database schema is not compatible with the"
                    " existing database schema. The given schema was {}"
                    " but the existing schema was {}").format(
                        schema, db_tdx_schema))
        return is_subset

    def addData(self,
        data: t.Iterable[t.Mapping[t.Text, t.Any]]
    ) -> AddDataResult:
        """Add data to a database resource.

        Example:
            >>> from nqm_iot_database.database import Database
            >>> db = Database("", "memory", "w+");
            >>> id = db.createDatabase(schema={"dataSchema": {"a": []}})
            >>> db.addData([{"a": 1}, {"a": 2}]) == {"count": 2}
            True
            >>> #insert ndarray
            >>> import numpy as np
            >>> nd_db = Database("", "memory", "w+")
            >>> nd_dschema = {"a": {"__tdxType": ["ndarray"]}}
            >>> nd_id = nd_db.createDatabase(schema={"dataSchema": nd_dschema})
            >>> array = np.array([[0, 1],[2, 3]])
            >>> nd_db.addData([{"a": array}]) == {"count": 1}
            True

        Args:
            data: A list of rows, where each row is a mapping of ``{key: val}``

        Returns:
            The count of data inserted.
        """
        # self.* lookup is slow so do it once only
        general_schema = self.general_schema
        
        # convert all the data to SQLite types
        convertRow = schemaconverter.convertRowToSqlite
        sqlData = [
            convertRow(general_schema, r, data_dir=self.data_dir) for r in data]

        if self.table is None:
            raise ValueError("self.table has not been initialized yet")

        self.connection.execute(self.table.insert(), sqlData)

        return t.cast(AddDataResult, {"count": len(sqlData)})
