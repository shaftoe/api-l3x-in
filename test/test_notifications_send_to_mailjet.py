# pylint: disable=protected-access
import json
import pytest
from io import BytesIO
from os import environ
from re import match
from unittest.mock import patch

from stacks.notifications.lambdas import send_to_mailjet
from utils import HandledError


def test_lambda_mailjet_message_from_event_defaults():
    result = send_to_mailjet._message_from_event(event={},
                                                 default_from="sender e@mail.com",
                                                 default_to="receiver e@mail.org")
    expected = {
        'From': {'Email': 'e@mail.com', 'Name': 'sender'},
        'TextPart': 'no content',
        'To': [{'Email': 'e@mail.org', 'Name': 'receiver'}],
        'Cc': [],
        'Bcc': [],
        'CustomID': 'api-l3x-in',
    }
    assert result == expected


@pytest.mark.parametrize(
    "event, expected_from",
    [
        ({"mail_from": "test@mail.com"}, {"Email": "test@mail.com"}),

        ({"mail_from": "With Name test.name@mail.com"},
         {"Email": "test.name@mail.com", "Name": "With Name"}),

        # Expect defaults when missing
        ({}, {"Email": "e@mail.com", "Name": "sender"}),
    ]
)
def test_lambda_mailjet_message_from_event_mailfrom(event, expected_from):
    result = send_to_mailjet._message_from_event(event, "sender e@mail.com", "receiver e@mail.org")
    assert result["From"] == expected_from


def test_lambda_mailjet_message_from_event_full():
    event = {
        "mail_from": "Misterious Sender email@co.m",
        "mail_to": "Anonynous Receiver e@ma.il",
        "mail_cc": ["email1@c.om", "No One no@one.there"],
        "mail_bcc": ["another@one.here", "With Long Name out@th.ere", "Third email@bl.ind"],
        "custom_id": "pytest",
        "subject": "pytest email",
        "text": "lorem ipsum blah blah blah",
        "attachments": [],
    }
    result = send_to_mailjet._message_from_event(event, "ignored e@mail.com", "<ignored> e@mail.org")

    assert result == {
        'From': {'Email': 'email@co.m', 'Name': 'Misterious Sender'},
        'TextPart': 'lorem ipsum blah blah blah',
        'To': [{'Email': 'e@ma.il', 'Name': 'Anonynous Receiver'}],
        'Cc': [
            {'Email': 'email1@c.om'},
            {'Email': 'no@one.there', 'Name': 'No One'},
        ],
        'Bcc': [
            {'Email': 'another@one.here'},
            {'Email': 'out@th.ere', 'Name': 'With Long Name'},
            {'Email': 'email@bl.ind', 'Name': 'Third'},
        ],
        'CustomID': 'pytest',
        'Subject': 'pytest email',
    }


@pytest.mark.parametrize(
    "event, error_message",
    [
        ({}, "Missing MAIL_FROM"),
        ({"mail_from": "not_an_email", "mail_to": "good@email.com"}, "Missing MAIL_FROM"),
        ({"mail_to": "test@mail.com"}, "Missing MAIL_FROM"),

        ({"mail_from": "test@mail.com"}, "Missing MAIL_TO"),
        ({"mail_to": "not_an_email", "mail_from": "good@email.com"}, "Missing MAIL_TO"),
    ]
)
def test_lambda_mailjet_message_from_event_throws(event, error_message):
    with pytest.raises(HandledError) as error:
        send_to_mailjet._message_from_event(event)

    assert error.match(error_message)
    assert error.value.status_code == 400


@patch("utils.aws.get_object_from_s3_bucket")
def test_add_content_to_attachment(mock):
    mock.return_value = BytesIO(bytes('🔥 FAKE utf-8 CONTENT ⚡️', encoding="utf-8"))

    attachment = {"Key": "fakeKey", "Bucket": "fakeBucket"}
    send_to_mailjet._add_content_to_attachment(attachment)

    assert mock.call_args.kwargs == {"key": "fakeKey", "bucket": "fakeBucket"}
    assert mock.return_value.closed
    assert "Base64Content" in attachment
    assert attachment["Base64Content"] == "8J+UpSBGQUtFIHV0Zi04IENPTlRFTlQg4pqh77iP"
    assert "Key" not in attachment
    assert "Bucket" not in attachment


@patch("utils.helpers.send_http_request")
def test_deliver_to_mailjet(mock):
    send_to_mailjet.deliver_to_mailjet({})

    assert mock.called

    assert "url" in mock.call_args.kwargs
    assert mock.call_args.kwargs["url"] == "https://api.mailjet.com/v3.1/send"

    assert "data" in mock.call_args.kwargs
    assert isinstance(mock.call_args.kwargs["data"], bytes)
    data = mock.call_args.kwargs["data"].decode(encoding="utf-8")
    data = json.loads(data)
    assert "Messages" in data
    assert len(data["Messages"]) == 1
    assert data["Messages"][0]["From"] == {"Email": "fake@from.address"}
    assert data["Messages"][0]["To"] == [{"Email": "fake@default.to.address"}]
    assert data["Messages"][0]["Cc"] == []
    assert data["Messages"][0]["Bcc"] == []
    assert data["Messages"][0]["CustomID"] == "api-l3x-in"
    assert data["Messages"][0]["TextPart"] == "no content"
    assert "Attachments" not in data["Messages"][0]
    assert "Subject" not in data["Messages"][0]

    assert "auth" in mock.call_args.kwargs
    for key in ("user", "pass"):
        val = mock.call_args.kwargs["auth"][key]
        assert isinstance(val, str)
        assert len(val) == 32
        assert match(r"[0-9a-f]+$", val)

    assert "headers" in mock.call_args.kwargs
    assert mock.call_args.kwargs["headers"]["Content-Type"] == "application/json"
