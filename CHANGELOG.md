# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2020-02-15

### Added

* add some logging and linting to `src/cdk.py` ([2bbe683](https://github.com/shaftoe/api-l3x-in/commit/2bbe683))
* add URL validation to utils.helpers ([7384126](https://github.com/shaftoe/api-l3x-in/commit/7384126))
* better __version__ handling in utils ([356691a](https://github.com/shaftoe/api-l3x-in/commit/356691a))
* improve `utils/cdk.py` environment handling ([e3b8139](https://github.com/shaftoe/api-l3x-in/commit/e3b8139))
* modify stack folder structure to avoid unneeded deploys ([e0615b2](https://github.com/shaftoe/api-l3x-in/commit/e0615b2))
* remove `requests` dependency from utils.helpers ([23b84fd](https://github.com/shaftoe/api-l3x-in/commit/23b84fd))
* set version to 0.2.0 ([408418f](https://github.com/shaftoe/api-l3x-in/commit/408418f))

### Fixes and cleanups

* add lambda layers code (`bs4` and `requests_oauth`) ([c2636f0](https://github.com/shaftoe/api-l3x-in/commit/c2636f0))
* Add `setup.py` metadata ([c5c1b43](https://github.com/shaftoe/api-l3x-in/commit/c5c1b43))
* better handle GitHub apis in utils.helpers ([42e2fdb](https://github.com/shaftoe/api-l3x-in/commit/42e2fdb))
* cleanup publish-to-social response message ([3eda2db](https://github.com/shaftoe/api-l3x-in/commit/3eda2db))
* fix folder structure in README ([0e92601](https://github.com/shaftoe/api-l3x-in/commit/0e92601))
* improve `bin/cleanup_cache.py` ([e3d1252](https://github.com/shaftoe/api-l3x-in/commit/e3d1252))
* Improve Makefile `clean` target ([b95651c](https://github.com/shaftoe/api-l3x-in/commit/b95651c))
* move bin/ folder to root ([f87373a](https://github.com/shaftoe/api-l3x-in/commit/f87373a))
* pass properly formatted data input to dev.to APIs ([af9b465](https://github.com/shaftoe/api-l3x-in/commit/af9b465))
* remove redundant utils.Response.put_text ([bf18c57](https://github.com/shaftoe/api-l3x-in/commit/bf18c57))
* remove useless redirection in Makefile clean target ([7f068ae](https://github.com/shaftoe/api-l3x-in/commit/7f068ae))
* Reorder `.gitignore` ([8cbf231](https://github.com/shaftoe/api-l3x-in/commit/8cbf231))

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
