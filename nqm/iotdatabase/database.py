"""
"""
import typing as t

import pathlib
import os
import sqlite3
import sqlalchemy
import sqlalchemy.engine
import sqlalchemy.dialects.postgresql

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

    @property
    def tdx_schema(self) -> schemaconverter.TDXSchema:
        tdx_schema: schemaconverter.TDXSchema = dict()
        if _sqliteinfotable.checkInfoTable(self.sqlEngine):
            info_keys = _sqliteinfotable.getInfoKeys(
                self.sqlEngine, ["schema"])
            if info_keys: # lists are False is empty
                tdx_schema = info_keys["schema"]
                # dataset schema definition
                tdx_schema.setdefault("schema", dict())
                # dataset data schema
                tdx_schema["schema"].setdefault("dataSchema", dict())
        return tdx_schema

    def createDatabase(self,
        basedOnSchema: t.Text = "dataset",
        derived: t.Mapping = None,
        description: t.Text = None,
        id: t.Text = None,
        name: t.Text = None,
        meta: t.Mapping = None,
        parentId: t.Text = None,
        provenance: t.Text = None,
        schema: schemaconverter.TDXSchema = None,
        shareMode: t.Text = None,
        tags: t.Iterable[t.Text] = None,
        **kargs
    ):
        """Creates a dataset in the SQLite Database

        Args:
            basedOnSchema:
                id of the schema on which this resource will be based.
        """

    def openDatabase(self,
        path: t.Union([t.Text, os.PathLike]),
        type: t.Union([t.Text, DbTypeEnum]),
        mode: t.Union([t.Text, _sqliteutils.DbModeEnum])
    ):
        """ Opens an SQLite database.

        Args:
            path: The path of the db.
            type: The type of the db: `"file"` or `"memory"`
            mode: The open mode of the db: `"w+"`, `"rw"`, or `"r"`
        """
        typeEnum = DbTypeEnum(type)
        if typeEnum == DbTypeEnum.file:
            # makes the directory the sqlite db is in
            os.makedirs(os.path.dirname(path))

        uri = _sqliteutils.sqlAlchemyURL(pathlib.Path(path), typeEnum, mode)
        # creates the sqlite3 connection
        self.sqlEngine = sqlalchemy.create_engine(uri)
        
        self.general_schema = dict()
        tdx_schema = self.tdx_schema
        if tdx_schema:
            self.general_schema = schemaconverter.convertSchema(tdx_schema)

        self.table = alchemyconverter.makeTable(
            self.sqlEngine, self.general_schema, tdx_schema)
        
        self.connection = self.sqlEngine.connect()
        return self

    def compatibleSchema(self, schema: schemaconverter.TDXSchema) -> bool:
        """Checks whether the given schema is a subset of the db schema
        """
        db_tdx_schema = self.tdx_schema
        # see https://stackoverflow.com/a/41579450/10149169
        is_subset = db_tdx_schema.items() <= schema.items()
        return is_subset

    def addData(self,
        data: t.Iterable[t.Mapping[t.Text, t.Any]]
    ) -> AddDataResult:
        # self.* lookup is slow so do it once only
        general_schema = self.general_schema
        
        # convert all the data to SQLite types
        convertRow = schemaconverter.convertRowToSqlite
        sqlData = [convertRow(general_schema, row) for row in data]

        uniqueIndex = self.tdx_schema.uniqueIndex

        self.connection.execute(
            sqlalchemy.dialects.postgresql.insert(self.table),
            sqlData)

        return t.cast(AddDataResult, {"count": len(sqlData)})
