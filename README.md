# Source code for api.l3x.in

[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)][license] ![Python](https://img.shields.io/badge/python-v3.8-green) [![Serverless](https://img.shields.io/badge/serverless-app-yellow)][serverless] [![Lambda](https://img.shields.io/badge/aws-lambda-brightgreen)][lambda] [![SNS](https://img.shields.io/badge/aws-sns-brightgreen)][SNS] [![CDK](https://img.shields.io/badge/aws-cdk-brightgreen)][CDK]

Source code that powers REST APIs at <https://api.l3x.in/>

## Setup

```bash
make all
```

## Architecture

AWS CDK [man app](lib/cdk.py) and [stacks](lib/stacks) are responsible for deploying/destroying all the things, no interaction whatsoever needed via the web console.

Each applications live in a dedicated Python package under the [`lib/stacks`](lib/stacks) folder.

The _stack_ package includes the CDK code required for deployment (in `__init__.py`) and the `.py` Lambda files.

## Project code structure

```bash
.
│ # CLI utilities
├── bin/
│
├── lib/
│   │ # Main CDK application
│   ├── cdk.py
│   │
│   │ # CDK stacks
│   ├── stacks
│   │   │
│   │   ├── <stack_1>
│   │   │   ├── __init__.py  # CDK resources
│   │   │   └── ...          # all the rest, including Lambda code, Lambda Layers packages, etc.
│   │   │
│   │   └── <stack_2>
│   │       ├── __init__.py
│   │       └── ...
│   │
│   │ # Shared library
│   └── utils/
│
│ # To enable contrubutions and maintainability
├── CHANGELOG.md
├── LICENSE
├── README.md
│
├── Makefile  # Various commands, like `deploy`, `diff`, etc.
├── VERSION   # Source of truth for current VERSION of this software
│
│ # CDK metadata
├── cdk.context.json
├── cdk.json
│
│ # ENV variables template for `config.mk` file
├── config.config.mk
│
│ # Unit tests
└── test/
```

## Contributions / Contacts

[Pull requests][pull-requests] are welcome.

You can also send me a message from the blog [contact page][contact-page]... or a POST request to <https://api.l3x.in/contact> if you don't like browsers ;)

## Commit messages and CHANGELOG

Following [Conventional Commits][commits] specification to easily keep the [`CHANGELOG`](CHANGELOG.md) up to date

[CDK]:           <https://docs.aws.amazon.com/cdk/api/latest/python/>
[contact-page]:  <https://a.l3x.in/contact.html>
[lambda]:        <https://docs.aws.amazon.com/lambda/index.html>
[license]:       <https://opensource.org/licenses/Apache-2.0>
[pull-requests]: <https://github.com/shaftoe/api-l3x-in/pull/new/master>
[serverless]:    <https://serverless-stack.com/chapters/what-is-serverless.html>
[SNS]:           <https://docs.aws.amazon.com/sns/index.html>
[commits]:       <https://www.conventionalcommits.org/en/v1.0.0/>
