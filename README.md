# nqm-iot-database-utils-python

Python port of
[`nqminds/nqm-iot-database-utils`][1]

[1]: https://github.com/nqminds/nqm-iot-database-utils

## Tests

### Unittests

```bash
pipenv run python -m pytest
```

### Unittests Coverage

```bash
pipenv run coverage run --source=nqm -m pytest && pipenv run coverage report
```

### Typetests

```bash
pipenv run mypy -m nqm.iotdatabase._sqliteschemaconverter && echo -e "\e[1;32mPass! \e[0m"
```

## Changes to make in SQLAlchemy

- Add sorting on Primary Keys (SQLite feature)
- allow using SQLite URI connections
