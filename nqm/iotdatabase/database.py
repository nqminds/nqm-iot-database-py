"""Module for controlling an NQM InterliNQ Database in Python

See the class `Database` for more info.
"""
import typing as t

import pathlib
import os
import tempfile # used for in-memory dbs
import collections
import collections.abc
import warnings
import json

import sqlalchemy
import sqlalchemy.engine
import sqlalchemy.dialects.postgresql
import mongosql

import shortuuid

from . import _sqliteconstants
from . import _sqliteutils
from . import _sqliteinfotable
from . import _sqliteschemaconverter as schemaconverter
from . import _sqlitealchemyconverter as alchemyconverter
from ._datasetdata import DatasetData, DatasetCount, MetaData

TDX_TYPE = _sqliteconstants.TDX_TYPE
SQLITE_GENERAL_TYPE = _sqliteconstants.SQLITE_GENERAL_TYPE
SCHEMA_KEY = str(_sqliteconstants.SCHEMA_KEY)

DbTypeEnum = _sqliteutils.DbTypeEnum
TDXSchema = schemaconverter.TDXSchema
AddDataResult = t.NewType("AddDataResult", dict)
TDXData = t.Iterable[t.Mapping[t.Text, t.Any]]

T = t.TypeVar("T") # generic type
def first(iterable: t.Iterable[T]) -> T:
    """Returns the first value of an iterable"""
    return next(iter(iterable))

def check_tdx_schema_valid(tdx_schema: t.Any) -> TDXSchema:
    try:
        assert isinstance(tdx_schema, collections.abc.MutableMapping)
        for key in tdx_schema:
            assert isinstance(key, str) or isinstance(key, bytes)
    except AssertionError as e:
        raise AssertionError(
            f"Expected tdx schema {tdx_schema} to be a "
            "MutableMapping with text keys"
        ) from e
    try:
        json.dumps(tdx_schema)
    except (TypeError, OverflowError) as e:
        raise AssertionError(
            f"Expected tdx schema {tdx_schema} to be JSONable") from e
    return t.cast(TDXSchema, tdx_schema)

class Database(object):
    """An instance of an NQM InterliNQ Database.

    Uses SQLite as a backend, but allows for TDX-style commands.

    Attributes:
        general_schema: The SQLite General Schema.
        sqlEngine: The `sqlalchemy` engine used for this connection.
        table: The `sqlalchemy` data table.
        table_model: The SQLAlchemy ORM (model) of the `sqlalchemy` data table.
        tdx_schema: The `TDXSchema` used by this dataset.
        tdx_data_schema: The `tdx_data_schema` for the data.
        data_dir:
            The location of the data directory (for saving ndarrays to file)
        path_to_db: The location of the underlying SQLite file.
        session_maker:
            Used to create an :class:`sqlalchemy.orm.session.Session` for
            querying data.
    """
    general_schema: schemaconverter.GeneralSchema
    sqlEngine: sqlalchemy.engine.Engine
    table: sqlalchemy.Table = None
    table_model = None
    tdx_schema: schemaconverter.TDXSchema = TDXSchema(dict())
    tdx_data_schema: schemaconverter.TDXDataSchema = dict()
    data_dir: t.Union[t.Text, os.PathLike] = ""
    path_to_db: os.PathLike
    session_maker: sqlalchemy.orm.scoped_session
    _mongosql_config: dict

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
                self.sqlEngine, [SCHEMA_KEY], self.session_maker)
            if info_keys: # lists are False is empty
                info_keys.setdefault(SCHEMA_KEY, dict())
                # dataset schema definition
                tdx_schema = info_keys[SCHEMA_KEY]
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
        db_engine = self.sqlEngine

        copiedTDXSchema = dict(schema.items())

        copiedTDXSchema.setdefault("dataSchema", {})
        copiedTDXSchema.setdefault("uniqueIndex", {})

        tdx_schema = TDXSchema(copiedTDXSchema)

        if not tdx_schema["dataSchema"] and tdx_schema["uniqueIndex"]:
            raise ValueError(("schema.dataSchema was empty, but"
                    " schema.uniqueIndex has a non.empty value of {}"
                ).format(tdx_schema["uniqueIndex"]))

        # convert the TDX schema to an SQLite schema and save it
        self.general_schema = schemaconverter.convertSchema(
            t.cast(schemaconverter.TDXDataSchema, tdx_schema["dataSchema"]))

        if _sqliteinfotable.checkInfoTable(db_engine):
            # check if old id exists
            self.session_maker
            infovals = _sqliteinfotable.getInfoKeys(
                db_engine, ["id"], self.session_maker)
            # use the original id if we can find it
            id = str(infovals.get("id", id))

            # will raise an error if the schemas aren't compatible
            self.compatibleSchema(TDXSchema(tdx_schema), raise_error=True)
        else:
            # create infotable
            _sqliteinfotable.createInfoTable(db_engine)
            info = kargs
            info[SCHEMA_KEY] = tdx_schema
            info["id"] = id

            _sqliteinfotable.setInfoKeys(db_engine, info)

        self._load_tdx_schema()

        sqlite_schema = schemaconverter.mapSchema(self.general_schema)

        if not sqlite_schema:
            # TODO Maybe add error (none now matches nqm-iot-database-utils)
            return id

        self._mongosql_config = dict(
            default_projection=None,
            default_exclude=[],
            default_exclude_properties=False,
            # allow aggregation on all columns
            aggregate_columns=sqlite_schema.keys(),
        )

        self.table_model = alchemyconverter.makeDataModel(
            db_engine, sqlite_schema, tdx_schema)

        def get_table():
            #pylint: disable=local-disable, no-member
            return self.table_model.__table__

        self.table = get_table()
        self.table.create(self.sqlEngine,  checkfirst=True) # create unless already exists

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
        self.path_to_db = pathlib.Path(path)

        type_enum = DbTypeEnum(type)
        if type_enum is DbTypeEnum.file:
            # makes the directory the sqlite db is in
            os.makedirs(os.path.dirname(path), exist_ok=True)
            self.data_dir = self.path_to_db.with_suffix(
                str(_sqliteconstants.DATABASE.DATA_FOLDER_SUFFIX))
        else: # in-memory db
            # autodeleted when self is deleted
            self.__tmpdir = tempfile.TemporaryDirectory()
            self.data_dir = self.__tmpdir.name

        os.makedirs(self.data_dir, exist_ok=True) # makes the data folder

        creator = _sqliteutils.sqlAlchemyEngineCreator(
            self.path_to_db, type_enum, mode)
        # creates the sqlite3 connection
        # see https://github.com/pudo/dataset/issues/136 for why we do this
        self.sqlEngine = sqlalchemy.create_engine(
            "sqlite:///", creator=creator)

        session_factory = sqlalchemy.orm.sessionmaker(bind=self.sqlEngine)
        # TODO: Replace session_maker with @contextlib.contextmanager format
        self.session_maker = sqlalchemy.orm.scoped_session(session_factory)

        # check to see if this is an already created database
        if _sqliteinfotable.checkInfoTable(self.sqlEngine):
            # check if old id exists
            infovals = _sqliteinfotable.getInfoKeys(
                self.sqlEngine, ["id", SCHEMA_KEY], self.session_maker)
            # use the original id if we can find it
            id = str(infovals.get("id"))
            loaded_tdx_schema = infovals.get(SCHEMA_KEY, None)
            tdx_schema = check_tdx_schema_valid(loaded_tdx_schema)
            self.createDatabase(id=id, schema=tdx_schema)

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

    def _convertDataToSQLite(self, data: TDXData
    ) -> t.Sequence[t.Mapping[t.Text, schemaconverter.SQLVal]]:
        """Converts the given TDX Data to SQLite Data.

        TDX Data is a list of dicts of Python objects.
        SQLite Data is a list of dicts of JSON-strings.

        Args:
            data: The list of TDX Data Rows.
        Returns:
            A list of SQL data rows.
        """
        # self.* lookup is slow so do it once only
        general_schema = self.general_schema

        # convert all the data to SQLite types
        convert_row = schemaconverter.convertRowToSqlite
        sql_data = [
            convert_row(general_schema, r, data_dir=self.data_dir)
            for r in data]
        return sql_data

    def _convertFilterToSQLite(self, mongofilter: t.Mapping[t.Text, t.Any]
    ) -> t.Mapping[t.Text, t.Any]:
        """Converts the given Mongo Query to a MongoSQLite Query

        Args:
            mongofilter: A Mongo Style Query
        Returns:
            The converted query that can be given to MongoSQL
        Raises:
            TypeError
                If you use mongo query ops (ie '$lt') on an invalid TDX_TYPE
                or if you query on an invalid type (ndarray).
        """
        if any(field[0] == "$" for field in mongofilter):
            invalid_fields = [f for f in mongofilter if f[0] == "$"]
            warnings.warn(RuntimeWarning(
                f"You have a top level mongo query operator {invalid_fields} "
                "in your filter. This should work, as long as you don't try "
                "querying any non-sqlite primitive types, ie array/object."))
            return mongofilter

        if not any(op[0] == "$" for val in mongofilter.values()
            if isinstance(val, dict) # val might be just a str
            for op in val
        ):
            # check if any column filters have a mongodb query operator
            # ie $eq, $lte, etc.
            # if they don't, we can easily convert the given row to sql
            sql_filter, = self._convertDataToSQLite((mongofilter, ))
            return sql_filter

        sql_filter = dict()
        prim_types = {
            TDX_TYPE.BOOLEAN, TDX_TYPE.DATE, TDX_TYPE.STRING, TDX_TYPE.NUMBER}
        banned_types = {TDX_TYPE.NDARRAY}

        # convert ugly TDX Data Schema to Map of Column to Type.
        # might need to be changed in the future for new TDX dataschema schema
        dataschema: t.Dict[t.Text, TDX_TYPE] = {}
        for column, column_type in self.tdx_data_schema.items():
            if isinstance(column_type, collections.abc.Mapping):
                dataschema[column] = TDX_TYPE(
                    column_type.get("__tdxType", [TDX_TYPE.OBJECT])[0])
            elif isinstance(column_type, collections.abc.Sequence):
                dataschema[column] =  TDX_TYPE.ARRAY

        for field, val in mongofilter.items():
            tdx_type = dataschema[field]
            if tdx_type in prim_types: # no need for conversion
                sql_filter[field] = val
                continue

            if tdx_type in banned_types: # cannot query
                raise TypeError(
                    f"All queries are banned on tdx_type {tdx_type}. "
                    "Given item was {field}.")

            if not isinstance(val, dict) or all(op[0] != "$" for op in val):
                # val is array/or dict with NO mongo query ops
                # can convert normally
                con_row, = self._convertDataToSQLite([{field: val}])
                sql_filter[field] = con_row[field]
                continue

            raise TypeError(
                "MongoDB Style Queries are only supported on items "
                f"with TDX Type values of {prim_types}. Given "
                "item was {field} with type {tdx_type}. "
                f"Mongo Op given was {next(op for op in val if op[0] == '$')}")
        return sql_filter

    def addData(self,
        data: TDXData
    ) -> AddDataResult:
        """Add data to a database resource.

        Example:
            >>> from nqm.iotdatabase.database import Database
            >>> db = Database("", "memory", "w+")
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
        sqlData = self._convertDataToSQLite(data)

        if self.table is None:
            raise ValueError("self.table has not been initialized yet")

        connection = self.sqlEngine.connect().execution_options(
            autocommit=True)
        connection.execute(self.table.insert(), sqlData)

        return t.cast(AddDataResult, {"count": len(sqlData)})

    def _mongo_query(self, session) -> mongosql.MongoQuery:
        return mongosql.MongoQuery(
            self.table_model, self._mongosql_config,
        ).from_query(
            session.query(self.table_model)
        )

    def getData(self,
        filter: t.Mapping[t.Text, t.Any] = {},
        projection: t.Mapping[t.Text, int] = {},
        options: t.Mapping[t.Text, t.Any] = {}
    ) -> DatasetData:
        """Gets all data from the given dataset that matches the filter.

        Args:
            filter:
                A mongodb filter object. If omitted, all data will be retrieved.
            projection:
                A mongodb projection object.
                Should be used to restrict the payload to the minimum
                properties needed if a lot of data is being retrieved.
            options:
                A mongodb options object. Can be used to limit, skip, sort etc.

        Returns:
            An object containing the data retrieved in the data field.

        Raises:
            ValueError: If an invalid option is given.
            TypeError: If the sort option is a dict, not an OrderedDict.

        Example:
            >>> from nqm.iotdatabase.database import Database
            >>> db = Database("", "memory", "w+")
            >>> id = db.createDatabase(schema={"dataSchema": {"a": []}})
            >>> db.addData([{"a": 1}, {"a": 2}]) == {"count": 2}
            True
            >>> datasetData = db.getData(filter={"a": 2})
            >>> datasetData.data == [{"a": 2}]
            True
        """
        if options.get("nqmMeta", False):
            raise NotImplementedError(
                "Setting options.nqmMeta to True is not implemented yet.")

        valid_query_opt = {"limit", "skip", "sort"} # opts to pass to mongosql
        query_opts = {k: options[k] for k in options if k in valid_query_opt}
        # raise Error if invalid options are given
        if any(key not in valid_query_opt for key in options):
            raise ValueError("Invalid option in options param. "
                f"'{next(k for k in options if k not in valid_query_opt)}' "
                f"is not a valid option. Valid options are {valid_query_opt}."
            )
        sort = query_opts.get("sort", {})
        if (sort and isinstance(sort, dict)
            and not isinstance(sort, collections.OrderedDict)
        ):
            if len(sort) == 1:
                # mongosql only accepts OrderedDict for sort
                # since dict is orderless
                query_opts["sort"] = collections.OrderedDict(sort)
            elif len(sort) > 1:
                raise TypeError("Received Sort Option of type dict with len "
                    f"{len(sort)}. Python dicts do not have order, therefore "
                    "please give either a list or OrderedDict as a sort "
                    "option.")

        # convert dict/array types to JSON
        mongosql_filter = self._convertFilterToSQLite(filter)

        session = self.session_maker()

        # in mongosql, an empty projection means don't return anything
        mongosql_projection = projection if projection else None

        mongoquery = self._mongo_query(session).query(
            filter=mongosql_filter, project=mongosql_projection, **query_opts,
        ).end()

        schema = self.general_schema

        data_dir = self.data_dir

        # TODO: MongoSQL's projection operator doesn't work correctly.
        # we should fix it instead of using this hack
        noproject = set(x for x, v in projection.items() if v == 0)
        projected_data = [
            {x: a for x, a in row.__dict__.items() if x not in noproject}
            for row in mongoquery.all()
        ]
        # close the ORM session when done
        session.close()

        data = [schemaconverter.convertRowToTdx(
            schema, row, data_dir) for row in projected_data]

        return DatasetData(data=data)

    def getAggregateData(self, pipeline: t.Mapping[t.Text, t.Any],
        filter: t.Mapping[t.Text, t.Any] = {},
    ) -> DatasetData:
        """Performs an aggregate query on the given dataset resource.

        Please note that as MongoSQL is used, some queries may not work.

        Args:
            pipeline: The aggregate pipeline, as defined in
                [the mongodb docs](https://docs.mongodb.com/manual/core/aggregation-pipeline/).
                Can be given as a JSON object or as a stringified JSON object.
            filter: A mongodb filter object.
                If omitted, all data will have the aggregation run on them.

        Returns:
            The data made from the aggregrate query.
            This will have only one row of data, and will be in SQL types.

        Example:
            >>> from nqm.iotdatabase.database import Database
            >>> db = Database("", "memory", "w+")
            >>> id = db.createDatabase(schema={"dataSchema": {"a": []}})
            >>> db.addData({"a": x} for x in range(3)) == {"count": 3}
            True
            >>> datasetData = db.getAggregateData(
            ...     pipeline={"answer": {"$sum": "a"}},
            ...     filter={"a": {"$lte": 2}})
            >>> datasetData.data == [
            ...     {"answer": sum(a for a in range(3) if a <= 2)}] # 1 + 2
            True
        """
        session = self.session_maker()

        mongoquery = self._mongo_query(session).query(
            filter=filter,
            aggregate=pipeline,
        ).end()

        schema = self.general_schema
        data_dir = self.data_dir

        #TODO: Make sure this is tested (above vars are unused, why?)

        data = [row._asdict() for row in mongoquery.all()]

        # close the ORM session when done
        session.close()

        return DatasetData(data=data)

    def getDataCount(self, filter: t.Mapping[t.Text, t.Any] = {}
    ) -> DatasetCount:
        """Gets a count of the data that matches the filter.

        Essentially just wraps
        :func:`~nqm.iotdatabase.database.Database.getAggregateData` with args
        ``pipeline={"count": {"$sum": 1}}``.

        Args:
            filter:
                An optional mongodb filter to apply before counting the data.

        Returns:
            The metadata and count in the count field.

        Example:
            >>> from nqm.iotdatabase.database import Database
            >>> db = Database("", "memory", "w+")
            >>> id = db.createDatabase(schema={"dataSchema": {"a": []}})
            >>> db.addData({"a": x} for x in range(3)) == {"count": 3}
            True
            >>> datasetCount = db.getDataCount({"a": {"$lte": 2}})
            >>> datasetCount.count == sum(1 for a in range(3) if a <= 2)
            True
        """
        aggregate_data = self.getAggregateData(
            pipeline={"count": {"$sum": 1}},
            filter=filter,
        )
        count = first(aggregate_data.data)["count"]
        return DatasetCount(count=count)

    def getResource(self) -> MetaData:
        """Gets the details/metadata for this dataset

        Returns:
            The metadata of this dataset.

        Example
            >>> from nqm.iotdatabase.database import Database
            >>> db = Database("", "memory", "w+")
            >>> metadata = {
            ...     "schema": {"dataSchema": {"a": []}}, "name": "Hi World"}
            >>> id = db.createDatabase(**metadata)
            >>> loaded_md = db.getResource()
            >>> # loaded_md's schemaDefintion creates an empty uniqueIndex
            >>> "uniqueIndex" in loaded_md["schemaDefinition"]
            True
            >>> loaded_md["schemaDefinition"]["dataSchema"] == {"a": []}
            True
            >>> # can use both md["x"] format or JavaScript like md.x format
            >>> print(loaded_md.name)
            Hi World
        """
        return MetaData(_sqliteinfotable.getInfoKeys(
            self.sqlEngine, [], self.session_maker))
