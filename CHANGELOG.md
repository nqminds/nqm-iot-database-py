# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.5] - 2019-11-14

### Fixed

- Fixed minor typing issue in database.py

### Misc

- Changed poetry lockfile to use ~=0.12.17 instead of in beta ~=1.0.0
- Added Github actions to repo

## [1.1.4] - 2019-11-13

### Fixed

- Fixed OSError not being created properly when too many files were opened.
- Fixed package not working in Python 3.7 due to
  [#27](https://github.com/nqminds/nqm-iot-database-py/issues/27)
- Fixed incorrect mypy type fields

### Misc

- Changed package dependecy manager from `pipenv` to `poetry`
- Update `monogsql` version to v2
- Update dependecies
- Cleaned up tests
