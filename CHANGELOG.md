# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Fixed OSError not being created properly when too many files were opened.
- Fixed package not working in Python 3.7 due to
  [#27](https://github.com/nqminds/nqm-iot-database-py/issues/27)

### Misc

- Changed package dependecy manager from `pipenv` to `poetry`
- Specify `mongosql` version as v1.5.5
- Update dependecies
- Cleaned up tests