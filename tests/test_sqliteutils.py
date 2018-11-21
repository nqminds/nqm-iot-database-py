import pytest
import nqm.iotdatabase._sqliteutils as sqliteutils

@pytest.mark.parametrize(
    argnames="path,type,mode,uri",
    argvalues=[
        ("/tmp/test.sqlite3", "memory", "r",
            "file:///tmp/test.sqlite3?mode=memory")
    ]
)
def test_sqliteURI(path, type, mode, uri):
    sqliteURI = sqliteutils.sqliteURI
    assert sqliteURI(path=path, type=type, mode=mode) == uri
