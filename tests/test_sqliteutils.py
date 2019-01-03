import pytest
import nqm.iotdatabase._sqliteutils as sqliteutils

@pytest.mark.parametrize(
    #Runs test_sqliteURI once for each of argvalues
    argnames="path,type,mode,uri",
    argvalues=[
        ("/tmp/test.sqlite3", "memory", "r",
            "file:///tmp/test.sqlite3?mode=memory")
        # only one test case since this func is currenty unused
    ]
)
def test_sqliteURI(path, type, mode, uri):
    sqliteURI = sqliteutils.sqliteURI
    assert sqliteURI(path=path, type=type, mode=mode) == uri
