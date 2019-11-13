"""Stores data about a dataset"""
import typing
import collections.abc

# ignore too-many-ancestors. We inherit from MutableMapping, which has tons.
# ignore invalid-name. We are copying the name from the JavaScript API.
#pylint: disable=locally-disabled, too-many-ancestors, invalid-name

class Object(collections.abc.MutableMapping):
    """An ``dict`` that can be used like a JavaScript object with dot notation

    Example:
        >>> obj = Object()
        >>> obj["example"] = "hello world"
        >>> obj.example
        "hello world"
        >>> obj.example = "hello users"
        >>> obj["example"]
        "hello users"
    """
    def __init__(self, *args, **kwargs):
        self.update(dict(*args, **kwargs))

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __delitem__(self, key):
        del self.__dict__[key]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        cls = self.__class__
        return f"{cls.__module__}.{cls.__name__}({str(self)})"

class MetaData(Object):
    """Stores the dataset metadata"""
    description: typing.Text = ""
    id: typing.Text = ""
    name: typing.Text = ""
    parents: typing.Iterable[typing.Text] = []
    schemaDefinition: typing.Mapping[typing.Text, typing.Any] = {}
    tags: typing.Iterable[typing.Text] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "schema" in self.__dict__:
            # delete schema value and replace it with schemaDefinition
            self.schemaDefinition = self.__dict__.pop("schema")

class DatasetMetaData(Object):
    """Base class for various results.

    Attributes:
        metaData: The dataset metadata.
    """
    metaData: MetaData

    def __init__(self, *args, **kwargs):
        self.metaData = MetaData()
        super().__init__(*args, **kwargs)

class DatasetData(DatasetMetaData):
    """Stores the dataset metadata and data.
    """
    data: typing.Iterable[typing.Mapping[typing.Text, typing.Any]] = ()

    def __init__(self, *args, **kwargs):
        self.data = tuple()
        super().__init__(*args, **kwargs)

class DatasetCount(DatasetMetaData):
    """Stores the dataset metadata and data count.
    """
    count: int = -1

    def __init__(self, count, *args, **kwargs):
        self.count = count
        super().__init__(*args, **kwargs)
