import json
from utils import (LOG_LEVEL, Response, HandledError)

def test_default_loglevel():
    assert LOG_LEVEL == 'INFO'

def test_response_is_serializable():
    response = json.dumps(Response())
    assert isinstance(response, str)

def test_exception_parent_class():
    error = HandledError("bogus")
    assert isinstance(error, Exception)

def test_default_exception_code():
    error = HandledError("bogus")
    assert error.status_code == 400
