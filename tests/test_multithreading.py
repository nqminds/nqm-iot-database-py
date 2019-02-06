import pathlib
import json

import pytest
from nqm.iotdatabase.database import Database

import threading

def json_dbinfo(jsonfilepath="tdx-schemas.json"):
    with pathlib.Path(__file__).with_name(jsonfilepath).open() as jsonfile:
        return json.load(jsonfile)

def ndarray_schema():
    for s in json_dbinfo():
        if s.get("name", None) == "NDArray Conversion Test":
            schema = s["schema"]
            return schema

def make_ndarray_db(filepath, save_list=None, save_arg=None):
    schema = ndarray_schema()
    db =  Database(filepath, "file", "w+")
    db.createDatabase(schema=schema)
    key = list(schema["uniqueIndex"][0].values())[0]
    if save_list:
        save_list[save_arg] = db, key
    return db, key

def add_data_to_db(data, db_path):
    db, key = make_ndarray_db(db_path)
    db.addData(data)

import time

no_threads = 2
def test_make_multithreaded_db(make_data, tmp_path, row_equal):
    number = 100
    schema = ndarray_schema()
    data = make_data(schema, number)
    output = [None,] * no_threads
    step = len(data)/no_threads
    path = tmp_path / "multithreading_test.sqlite"

    # check if all data added succesfully
    db, key = make_ndarray_db(path)

    thread_data = [data[int(x*step): int((x+1) * step)] for x in range(no_threads)]

    threads = [threading.Thread(target=add_data_to_db, args=(data, path))
        for data in thread_data ]
    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    loaded_data = db.getData(options={"sort": {key: 1}}).data

    data = sorted(data, key=lambda x: x[key])

    assert len(data) == len(loaded_data)
    for datum, loaded_datum in zip(data, loaded_data):
        row_equal(datum, loaded_datum)
