import pytest

@pytest.fixture
def db():
    from nqm.iotdatabase._sqliteutils import sqliteURI
    import sqlalchemy
    pass
