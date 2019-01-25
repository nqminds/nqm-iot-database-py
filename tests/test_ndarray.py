import pytest
import nqm.iotdatabase.ndarray as _ndarray
import numpy as np
import os

types = ["int8", "int64", "uint32", "float", "double"]
@pytest.fixture(params=types)
def dtype(request):
    return request.param

shapes = [(2, 3, 4), (5), (1, 1, 1)]
@pytest.fixture(params=shapes)
def shape(request):
    return request.param

@pytest.fixture(params=(True, False))
def c_order(request):
    return request.param

@pytest.fixture(params=("f", "B", "G"))
def fileformat(request):
    return request.param

@pytest.fixture(scope="module") # run once per module
def datadir(tmpdir_factory):
    datadir = tmpdir_factory.mktemp("test_ndarray_data")
    os.makedirs(datadir, exist_ok=True)
    return datadir

@pytest.fixture
def arr(dtype, shape, c_order):
    a = np.random.random_sample(shape)
    if c_order: a = np.ascontiguousarray(a, np.dtype(dtype))
    else: a = np.asfortranarray(a, np.dtype(dtype))

    return a

def test_saving_loading(arr, fileformat, datadir):
    a = arr

    metadata1 = _ndarray.saveNDArray(arr, datadir, storage_method=fileformat)
    metadata2 = _ndarray.saveNDArray(arr+2, datadir, storage_method=fileformat)

    assert np.array_equal(arr, _ndarray.getNDArray(metadata1, datadir))
    arr2 = _ndarray.getNDArray(metadata2, datadir)
    assert not np.array_equal(arr, arr2)
    assert np.array_equal(arr+2, arr2)

def test_saving_as_pure_json(arr):
    json = _ndarray.saveToPureJSON(arr)
    assert np.array_equal(_ndarray.loadFromPureJSON(json), arr)
