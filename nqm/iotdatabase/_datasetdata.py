"""Stores data about a dataset"""
import typing
import collections

class DatasetData(collections.MutableMapping):
    """Stores the dataset metadata and data.
    """
    metaData: typing.Mapping[typing.Text, typing.Any] = {}
    data: typing.Iterable[typing.Mapping[typing.Text, typing.Any]] = ()

    def __init__(self, *args, **kwargs):
        self.metaData = {}
        self.data = () # tuple is faster to create than a list
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
