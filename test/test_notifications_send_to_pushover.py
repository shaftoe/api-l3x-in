from os import environ as env
from unittest.mock import patch
import pytest

from stacks.notifications.lambdas import send_to_pushover
from utils import Response, HandledError


@patch("utils.helpers.send_http_request")
def test_send(mock):
    mock.return_value = Response()
    mock.return_value.put({
        "status": 1,
        "request": "XXX-SOME-UNIQUE-ID-XXX",
    })

    send_to_pushover.send({"title": "fake title", "payload": "some message here"})

    assert mock.called
    assert mock.call_args.kwargs == {
        "url": send_to_pushover.PUSHOVER_API_ENDPOINT,
        "data": {
            "token": env["PUSHOVER_TOKEN"],
            "user": env["PUSHOVER_USERKEY"],
            "message": "some message here",
            "title": "fake title",
        },
    }


@patch("utils.helpers.send_http_request")
def test_send_throws(mock):
    with pytest.raises(KeyError):
        send_to_pushover.send({"payload": "missing title in event"})

    with pytest.raises(KeyError):
        send_to_pushover.send({"title": "missing payload in event"})

    with pytest.raises(HandledError) as error:
        mock.return_value = Response()
        mock.return_value.put({
            "status": 0, # wrong `status` value, expected 1
            "request": "XXX-SOME-UNIQUE-ID-XXX",
        })
        send_to_pushover.send({"title": "fake title", "payload": "some message here"})
        assert error.status_code == 500

    with pytest.raises(HandledError) as error:
        mock.return_value = Response()
        mock.return_value.put({
            "status": 1, # missing `request` key
        })
        send_to_pushover.send({"title": "fake title", "payload": "some message here"})
        assert error.status_code == 500
