# nqm-iot-database-utils-python

Python port of
[`nqminds/nqm-iot-database-utils`][1]

[1]: https://github.com/nqminds/nqm-iot-database-utils

## Installing

Use the below to install as a library using `pip`:

```bash
# pypi version is only for Python 2
pip3 install git+https://github.com/dignio/py-mongosql#egg=mongosql
# for SSH:
# pip3 install git+ssh://git@github.com/nqminds/nqm-iot-database-py.git#egg=nqm.iotdatabase
pip3 install git+https://github.com/nqminds/nqm-iot-database-py.git#egg=nqm.iotdatabase
```

You can replace `pip3` with `pipenv` if you prefer.

To download the library, install dependencies for running tests, and build
documentation, do:

```bash
git clone https://github.com/nqminds/nqm-iot-database-py.git
cd nqm-iot-database-py/
pipenv --python 3 install --dev
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
pipenv run mypy -m nqm.iotdatabase && echo -e "\e[1;32mPass! \e[0m"
```

### Doctests

```bash
pipenv run make doctest
```

### Linting

```bash
pipenv run pylint nqm
```

## Possible upgrades to make in SQLAlchemy

- Add sorting on Primary Keys (SQLite feature)
- allow using SQLite URI connections (for read-only)
