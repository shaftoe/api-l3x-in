# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2020-02-11

### Added

- This [CHANGELOG](CHANGELOG.md)
- Apache v2.0 [license](LICENSE)
- [Makefile](Makefile) with commands to ease interaction
- the [README](README.md)
- the source of truth for [VERSION](VERSION) of this software
- `cdk.*`: metadata needed by CDK that should not change
- An [example template](config.example.mk) for creating needed `config.mk` with sensitive data (i.e. not tracked by Git)
- [`setup.py`](setup.py) (used by Pip, should not change)
- all the [CDK and applications source code](src/)
- [test](test/) folder for unit tests
