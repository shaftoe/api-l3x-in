# WARNING: The folder structure of Lambda layers base folder is important

Refer to [the docs](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html#configuration-layers-path) for details.

For Python every module needs to be under a root `python` folder. Example with the Python _Pillow_ package:

    pillow.zip
    │ python/PIL
    └ python/Pillow-5.3.0.dist-info

So in our case it means something like:

    layers
    ├── bs4
    │   └── python
    │       └── bs4
    │           ├── __init__.py
    │           └── *.py
    └── requests_oauthlib
        └── python
            └── requests_oauthlib
                ├── __init__.py
                └── *.py

## Be sure the module can be properly imported locally before deployment

E.g. check that:

    cd layers/bs4/python/ && python -c 'import bs4'

returns exit code 0

## Install

- bs4
  - https://www.crummy.com/software/BeautifulSoup/bs4/download/
  - pip install -t . soupsieve
  - 2to3 -w bs4
- requests_oauth
  - pip install -t . requests_oauth

and remember to cleanup useless files like `pyc`, tests, etc
