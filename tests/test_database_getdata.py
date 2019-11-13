import pathlib
import json
import itertools

import pytest
from nqm.iotdatabase.database import Database

def limit(iterable, limit_val):
    return itertools.islice(iterable, None, limit_val)

def skip(iterable, skip_val):
    return itertools.islice(iterable, skip_val, None)

DEFAULT_LIMIT = 3
"""
We limit queries by default,
as the OS can only open so many np arrays at once before throwing an OSError
"""

def json_dbinfo(jsonfilepath="tdx-schemas.json"):
    with pathlib.Path(__file__).with_name(jsonfilepath).open() as jsonfile:
        return json.load(jsonfile)

@pytest.fixture(scope="module")
def dataDb(make_data):
    for s in json_dbinfo():
        if s.get("name", None) == "NDArray Conversion Test":
            schema = s["schema"]
    db =  Database("", "memory", "w+")
    db.createDatabase(schema=schema)
    number = 100
    data = make_data(schema, number=number)
    db.addData(data)
    key = list(schema["uniqueIndex"][0].values())[0]
    return db, data, key

def test_getsingledata(dataDb, row_equal):
    db, data, key = dataDb
    for row in data:
        data = db.getData({key: row[key]}).data
        assert len(data) == 1
        row_equal(row, data[0])

def test_getalldata(dataDb, row_equal):
    db, data, key = dataDb
    # change data to a dict, where uniqueIndex is the key
    dataByKey = {row[key]: row for row in data}
    savedData = db.getData().data
    for savedrow in savedData:
        row_equal(dataByKey[savedrow[key]], savedrow)

def test_getlimitdata(dataDb):
    db, data, key = dataDb
    for limit in range(1, 10):
        loadedData = db.getData(options={"limit": limit}).data
        assert len(loadedData) == limit
    for limit in -1, 0:
        # no limit if limit is -1 or 0
        loadedData = db.getData(options={"limit": limit}).data
        assert len(loadedData) == len(data)

def test_getsorteddata(dataDb, data_equal):
    db, data, key = dataDb
    for sort in +1, -1:
        sortedData = sorted(data,
            key=lambda row: row[key],
            reverse=sort == -1)
        sortedSavedData = db.getData(options={"sort": {key: sort}}).data
        data_equal(sortedSavedData, sortedData)

def test_invalidoption(dataDb):
    db, data, key = dataDb
    with pytest.raises(ValueError, match=r"Invalid option in options param.*"):
        db.getData(options={"hello_world": 1}).data

a = 89; b = 12; c = [a, b, 50]
@pytest.fixture(params=(
        (lambda x: x == a, {"$eq": a}),
        (lambda x: x > a, {"$gt": a}),
        (lambda x: x >= a, {"$gte": a}),
        (lambda x: x <= b, {"$lte": b}),
        (lambda x: x < b, {"$lt": b}),
        (lambda x: x in c, {"$in": c}),
        (lambda x: x not in c, {"$nin": c}),
        # implicit and in mongo query
        (lambda x: a > x and x > b, {"$lt": a, "$gt": b})
    ))
def filterfunc_mongofilter(request):
    return request.param

@pytest.mark.dependency()
def test_getqueryopts(dataDb, data_equal, filterfunc_mongofilter):
    db, data, key = dataDb

    limit_val = DEFAULT_LIMIT
    sortedData = sorted(data, key=lambda row: row[key])

    filterfunc, mongofilter = filterfunc_mongofilter

    savedData = db.getData(
        filter={key: mongofilter},
        options={"sort": {key: 1}, "limit": limit_val}).data
    filteredData = filter(lambda x: filterfunc(x[key]), sortedData)
    expectedData = limit(filteredData, limit_val)
    data_equal(savedData, expectedData)

@pytest.mark.dependency(depends=["test_getqueryopts"])
def test_getqueryopts_skip(dataDb, data_equal, filterfunc_mongofilter):
    db, data, key = dataDb

    limit_val = DEFAULT_LIMIT
    sortedData = sorted(data, key=lambda row: row[key])

    filterfunc, mongofilter = filterfunc_mongofilter

    for skip_val in (0, 2, 4):
        savedData = db.getData(
            filter={key: mongofilter},
            options={
                "sort": {key: 1}, "skip": skip_val, "limit": limit_val
            }).data
        filteredData = limit(skip(
            filter(lambda x: filterfunc(x[key]), sortedData),
            skip_val,
        ), limit_val)

        data_equal(savedData, filteredData)

@pytest.mark.dependency(depends=["test_getqueryopts"])
def test_getlogicalquery(dataDb, row_equal):
    db, data, key = dataDb
    sortedData = sorted(data, key=lambda row: row[key])

    filterfunc_mongofilters = (
        (lambda x: x[key] > 12 and x[key] <= 26,
            {"$and": [{key: {"$gt": 12}}, {key: {"$lte": 26}}]}),
        (lambda x: x[key] < 12 or x[key] > 95,
            {"$or": [{key: {"$lt": 12}}, {key: {"$gt": 95}}]}),
        (lambda x: x[key] < 12 and not x[key] < 6,
            {"$and": [{key: {"$lt": 12}}, {key: {"$gt": 95}}]}),
    )

    for filterfunc, mongofilter in filterfunc_mongofilters:
        # expect warning since logical operators might do weird stuff
        with pytest.warns(RuntimeWarning):
            savedData = db.getData(
                filter=mongofilter,
                options={"sort": {key: 1}}).data
        for row, getDataRow in zip(
            savedData, filter(filterfunc, sortedData)
        ):
            row_equal(row, getDataRow)

def projections(fields, project={}):
    for projectVal in 0, 1:
        project[fields[0]] = projectVal
        if len(fields) > 1:
            yield from projections(fields[1:], project)
        else:
            yield project

def test_getdata_projection(dataDb):
    db, data, key = dataDb
    sortedData = sorted(data, key=lambda row: row[key])

    for projection in projections(tuple(data[0].keys())):
        print(projection)
        projectedData = db.getData(
            projection=projection,
            options={"limit": 1}).data

        assert len(projectedData) == 1

        projectedSet = set(x for x,v in projection.items() if v == 1)
        assert projectedSet == set(projectedData[0].keys())

@pytest.fixture(params=(
    (max, lambda x: {"$max": x}),
    (min, lambda x: {"$min": x}),
    (lambda x: sum(x)/len(x), lambda x: {"$avg": x}),
    (sum, lambda x: {"$sum": x}),
    (len, lambda x: {"$sum": 1}),
))
def aggfunc_mongopipe(request):
    return request.param

@pytest.mark.dependency(depends=["test_getqueryopts"])
def test_getaggregatedata(dataDb, filterfunc_mongofilter, aggfunc_mongopipe):
    db, data, key = dataDb
    filterfunc, mongofilter = filterfunc_mongofilter
    aggfunc, mongopipe = aggfunc_mongopipe

    result_key = "result"
    pipeline = {result_key: mongopipe(key)}

    aggregateResult = db.getAggregateData(
        filter={key: mongofilter},
        pipeline=pipeline)

    actualAgg = aggregateResult.data[0]
    print(data[0])
    filteredData = [r[key] for r in data if filterfunc(r[key])]
    expectedAgg = {result_key: aggfunc(filteredData)}

    assert expectedAgg == actualAgg

@pytest.mark.dependency(depends=["test_getqueryopts"])
def test_getdatacount(dataDb, filterfunc_mongofilter):
    db, data, key = dataDb
    filterfunc, mongofilter = filterfunc_mongofilter

    aggregateResult = db.getDataCount(
        filter={key: mongofilter}
    )

    count = aggregateResult.count

    expectedCount = sum(1 for r in data if filterfunc(r[key]))

    assert count == expectedCount
