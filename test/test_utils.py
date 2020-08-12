from os import environ
import json
import re

from utils import (LOG_LEVEL, Response, HandledError)

def test_default_loglevel():
    assert LOG_LEVEL == 'INFO'

def test_response_is_serializable():
    response = json.dumps(Response())
    assert isinstance(response, str)

def test_response_default_cors_content():
    cors = environ.get("CORS_ALLOW_ORIGIN", "*")
    response = json.dumps(Response())
    assert response == '{"isBase64Encoded": false, ' \
        '"headers": {"Access-Control-Allow-Origin": "' + cors + '"}, "body": "{}"}'

def test_response_custom_cors_content():
    global environ # pylint: disable=global-statement, invalid-name
    temp = environ.copy()
    cors = "https://bogus"
    environ["CORS_ALLOW_ORIGIN"] = cors
    response = json.dumps(Response())
    assert response == '{"isBase64Encoded": false, ' \
        '"headers": {"Access-Control-Allow-Origin": "' + cors + '"}, "body": "{}"}'
    environ = temp

def test_response_body():
    response = Response(name="TestResponse")
    assert response.body == '{"name": "TestResponse"}'

    response.put("Some Message")
    assert re.search('"http_code": 200', response.body)
    assert re.search('"message": "Some Message"', response.body)
    assert re.search(r'"timestamp": "[0-9|\-|\.|:|T|Z]+"', response.body)

    response.put(Exception("Some error"))
    assert re.search('"message": "Some error"', response.body)
    assert re.search('"http_code": 500', response.body)

    response.put(HandledError("Some other error", status_code=400))
    assert re.search('"message": "Some other error"', response.body)
    assert re.search('"http_code": 400', response.body)

    response.put(NotImplementedError("Something else"))
    assert re.search('"message": "Something else"', response.body)
    assert re.search('"http_code": 501', response.body)

def test_exception_parent_class():
    error = HandledError("bogus")
    assert isinstance(error, Exception)

def test_default_exception_code():
    error = HandledError("bogus")
    assert error.status_code == 400
