# pylint: disable=protected-access
import pytest
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
