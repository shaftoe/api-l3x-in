# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

# [0.7.0](https://github.com/shaftoe/api-l3x-in/compare/0.6.0...0.7.0) (2020-03-29)

### Added

* add `pocket-to-kindle` stack

# [0.6.0](https://github.com/shaftoe/api-l3x-in/compare/0.5.0...0.6.0) (2020-03-22)

### Added

* remove lambda_layers stack and bundle layers directly in stacks

### Fixes

* **Makefile:** add cdk_version task
* **Makefile:** add show-loggroups target
* **notifications:** add support for S3 attachments
* **publish-to-social:** fix infinite retention for reports log group
* **publish-to-social:** fix wrong log retention for report loggroup
* **utils:** add support for multiple event types to invoke_lambda, improve trigger_ecs_fargate_task
* **utils:** better handle 3rd-party modules versions
* **Makefile:** add `make upgrade-cdk`
* **utils:** add debug info to aws.read_log_stream
* **utils:** remove unused PYTHON_3_7 compatible runtime
* **utils:** remove useless list

## [0.5.0](https://github.com/shaftoe/api-l3x-in/compare/0.4.0...0.5.0) - 2020-03-08

### Added

* **api:** expose publish-to-social report content via `GET /social_report`
* **cdk:** add `get_layer` to `utils.cdk`
* **notifications:** add `Mailjet` lambda
* **publish-to-social:** add `populate_logstreams.py` utility script
* **publish-to-social:** add tags to published messages
* **utils:** add `S3EventHandler`
* **utils:** improve `utils.aws` and `utils.cdk` libraries

### Fixes

* **devto:** inject original blog reference to markdown content
* **utils:** add missing UTF-8 decoding to `get_file_from_github`
* **utils:** update GitHub blog folder structure

## [0.4.0](https://github.com/shaftoe/api-l3x-in/compare/0.3.0...0.4.0) - 2020-02-22

### Added

* **publish-to-social:** add send_report lambda destination
* **utils:** improve Response data handling
* **notifications:** add notifications stack
* add linter (`Pylint`) to Makefile targets
* make `Pylint` happier (some docstrings still missing)

### Fixes

* improve README
* remove bogus brackets from messages
* **publish-to-social:** remove unused message event argument

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
