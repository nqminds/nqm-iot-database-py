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
pipenv run mypy -m nqm.iotdatabase._sqliteschemaconverter && echo -e "\e[1;32mPass! \e[0m"
```
