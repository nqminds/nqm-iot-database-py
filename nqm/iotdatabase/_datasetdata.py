"""Stores data about a dataset"""
import typing
import collections

class DatasetMetaData(collections.MutableMapping):
    """Stores the dataset metada"""
    metaData: typing.Mapping[typing.Text, typing.Any] = {}

    def __init__(self, *args, **kwargs):
        self.metaData = {}
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
    count: typing.Iterable[typing.Mapping[typing.Text, typing.Any]] = ()

    def __init__(self, count, *args, **kwargs):
        self.count = count
        super().__init__(*args, **kwargs)
