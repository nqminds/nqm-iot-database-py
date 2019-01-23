import pytest
import nqm.iotdatabase._ndarray as _ndarray
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

def test_saving_loading(dtype, shape, c_order, fileformat, datadir):
    a = np.random.random_sample(shape)
    if c_order: a = np.ascontiguousarray(a, np.dtype(dtype))
    else: a = np.asfortranarray(a, np.dtype(dtype))

    metadata1 = _ndarray.saveNDArray(a, datadir, storage_method=fileformat)
    metadata2 = _ndarray.saveNDArray(a+2, datadir, storage_method=fileformat)

    assert np.array_equal(a, _ndarray.getNDArray(metadata1, datadir))
    a2 = _ndarray.getNDArray(metadata2, datadir)
    assert not np.array_equal(a, a2)
    assert np.array_equal(a+2, a2)
