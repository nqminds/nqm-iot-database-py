# nqm-iot-database-utils-python

Python port of
[`nqminds/nqm-iot-database-utils`][1]

[1]: https://github.com/nqminds/nqm-iot-database-utils

## Tests

### Unittests

```bash
pipenv run python -m pytest
```

### Typetests

```bash
pipenv run mypy --namespace-packages --warn-redundant-casts --warn-unused-ignores --warn-return-any -m nqm.iotdatabase._sqliteschemaconverter
```
