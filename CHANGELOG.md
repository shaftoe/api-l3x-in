# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0](https://github.com/shaftoe/api-l3x-in/compare/0.2.0...0.3.0) - 2020-02-15

### Added

* rename `src` to `lib` to adhere to common CDK examples

### Bug Fixes

* **api:** ignore environment when setting LOG_LEVEL

## [0.2.0] - 2020-02-15

### Added

* add some logging and linting to `src/cdk.py`
* add URL validation to utils.helpers
* better __version__ handling in utils
* improve `utils/cdk.py` environment handling
* modify stack folder structure to avoid unneeded deploys
* remove `requests` dependency from utils.helpers
* set version to 0.2.0

### Fixes and cleanups

* add lambda layers code (`bs4` and `requests_oauth`)
* Add `setup.py` metadata
* better handle GitHub apis in utils.helpers
* cleanup publish-to-social response message
* fix folder structure in README
* improve `bin/cleanup_cache.py`
* Improve Makefile `clean` target
* move bin/ folder to root
* pass properly formatted data input to dev.to APIs
* remove redundant utils.Response.put_text
* remove useless redirection in Makefile clean target
* Reorder `.gitignore`

## [0.1.0] - 2020-02-11

### Added

* This [CHANGELOG](CHANGELOG.md)
* Apache v2.0 [license](LICENSE)
* [Makefile](Makefile) with commands to ease interaction
* the [README](README.md)
* the source of truth for [VERSION](VERSION) of this software
* `cdk.*`: metadata needed by CDK that should not change
* An [example template](config.example.mk) for creating needed `config.mk` with sensitive data (i.e. not tracked by Git)
* [`setup.py`](setup.py) (used by Pip, should not change)
* all the [CDK and applications source code](src/)
* [test](test/) folder for unit tests
