"""
"""
import typing as t

import pathlib
import os
import sqlalchemy
import sqlalchemy.engine
import sqlalchemy.dialects.postgresql

import shortuuid

import nqm.iotdatabase._sqliteconstants as _sqliteconstants
import nqm.iotdatabase._sqliteutils as _sqliteutils
import nqm.iotdatabase._sqliteinfotable as _sqliteinfotable
import nqm.iotdatabase._sqliteschemaconverter as schemaconverter
import nqm.iotdatabase._sqlitealchemyconverter as alchemyconverter

DbTypeEnum = _sqliteutils.DbTypeEnum
AddDataResult = t.NewType("AddDataResult", dict)


class Database(object):
    general_schema: schemaconverter.GeneralSchema
    sqlEngine: sqlalchemy.engine.Engine
    table: sqlalchemy.Table = None

    def __init__(self,
        path: t.Union[t.Text, os.PathLike],
        type: t.Union[t.Text, DbTypeEnum],
        mode: t.Union[t.Text, _sqliteutils.DbModeEnum]
    ):
        self.openDatabase(path, type, mode)

    @property
    def tdx_schema(self) -> schemaconverter.TDXSchema:
        tdx_schema: schemaconverter.TDXSchema = dict()
        if _sqliteinfotable.checkInfoTable(self.sqlEngine):
            info_keys = _sqliteinfotable.getInfoKeys(
                self.sqlEngine, ["schema"])
            if info_keys: # lists are False is empty
                info_keys.setdefault("schema", dict())
                # dataset schema definition
                tdx_schema = info_keys["schema"]
                # dataset data schema
                tdx_schema.setdefault("dataSchema", dict())
        return tdx_schema

    def createDatabase(self,
        id: t.Text = shortuuid.uuid(),
        schema: schemaconverter.TDXSchema = {},
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
        db = self.sqlEngine

        tdxSchema = dict(schema.items())

        if not schema["dataSchema"] and schema["uniqueIndex"]:
            raise ValueError(("schema.dataSchema was empty, but"
                    " schema.uniqueIndex has a non.empty value of {}"
                ).format(schema.uniqueIndex))

        # convert the TDX schema to an SQLite schema and save it
        self.general_schema = schemaconverter.convertSchema(
            schema["dataSchema"])

        if _sqliteinfotable.checkInfoTable(db):
            # check if old id exists
            infovals = _sqliteinfotable.getInfoKeys(db, ["id"])
            # use the original id if we can find it
            id = infovals.get("id", id)

            # will raise an error if the schemas aren't compatible
            self.compatibleSchema(schema, raise_error=True)
        else:
            # create infotable
            _sqliteinfotable.createInfoTable(db)
            info = kargs
            info["schema"] = schema
            info["id"] = id
            
            _sqliteinfotable.setInfoKeys(db, info)

        sqlite_schema = schemaconverter.mapSchema(self.general_schema)

        if not sqlite_schema:
            # TODO Maybe add error (none now matches nqm-iot-database-utils)
            return id

        self.table = alchemyconverter.makeDataTable(
            db, sqlite_schema, schema)
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
        typeEnum = DbTypeEnum(type)
        if typeEnum == DbTypeEnum.file:
            try:
                # makes the directory the sqlite db is in
                os.makedirs(os.path.dirname(path))
            except FileExistsError:
                pass

        uri = _sqliteutils.sqlAlchemyURL(pathlib.Path(path), typeEnum, mode)
        # creates the sqlite3 connection
        self.sqlEngine = sqlalchemy.create_engine(uri)
        
        self.general_schema = dict()
        tdx_schema = self.tdx_schema
        if tdx_schema:
            self.general_schema = schemaconverter.convertSchema(tdx_schema)
        
        self.connection = self.sqlEngine.connect().execution_options(
            autocommit=True)
        return self

    # copy docstring
    __init__.__doc__ = openDatabase.__doc__

    def compatibleSchema(self,
        schema: schemaconverter.TDXSchema,
        raise_error: bool = True
    ) -> bool:
        """Checks whether the given schema is a subset of the db schema
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
        # self.* lookup is slow so do it once only
        general_schema = self.general_schema
        
        # convert all the data to SQLite types
        convertRow = schemaconverter.convertRowToSqlite
        sqlData = [convertRow(general_schema, row) for row in data]

        if self.table is None:
            raise ValueError("self.table has not been initialized yet")

        self.connection.execute(self.table.insert(), sqlData)

        return t.cast(AddDataResult, {"count": len(sqlData)})
