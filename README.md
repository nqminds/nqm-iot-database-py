# nqm-iot-database-utils-python

Python port of
[`nqminds/nqm-iot-database-utils`][1]

[1]: https://github.com/nqminds/nqm-iot-database-utils

## Installing

Use the below to install dependencies

```bash
pipenv install
```

And use the following to install development dependencies for testing
and building documentation:

```bash
pipenv install --dev
```

## Documentation

We use Sphinx, Autodoc, Napoleon, and
[`sphinx_autodoc_typehints`](https://github.com/agronholm/sphinx-autodoc-typehints)
to make our documentation.

The below creates html.

```bash
pipenv run make html
```

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

### Doctests

```bash
pipenv run make doctest
```

## Changes to make in SQLAlchemy

- Add sorting on Primary Keys (SQLite feature)
- allow using SQLite URI connections
