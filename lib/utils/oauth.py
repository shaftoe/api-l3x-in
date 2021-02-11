from typing import (
    Iterable,
    Mapping,
    Optional,
)

from . import (
    HandledError,
    Log,
    Response,
)
from .helpers import (
    import_non_stdlib_module,
    send_http_request,
)


oauthlib = import_non_stdlib_module("oauthlib.oauth2")  # pylint: disable=invalid-name
requests_oauthlib = import_non_stdlib_module("requests_oauthlib")  # pylint: disable=invalid-name

# pylint: disable=unsubscriptable-object
def post_request_to_v1_endpoint(
        url: str, client_key: str, client_secret: str,
        resource_owner_key: str, resource_owner_secret: str,
        post_data: Optional[Mapping] = None) -> Response:

    """Implements https://requests-oauthlib.readthedocs.io/en/latest/oauth1_workflow.html"""

    response = Response()

    oauth = requests_oauthlib.OAuth1Session(
        client_key=client_key,
        client_secret=client_secret,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret)

    Log.info("Posting status to Oauth1 endpoint %s", url)
    resp = oauth.post(url, data=post_data)

    msg = "status_code: %s\ncontent: %s\nheaders: %s" % (resp.status_code,
                                                         resp.json(),
                                                         resp.headers)

    Log.debug("Received response from %s:\n%s", url, msg)

    if resp.status_code == 200:
        Log.info("POST request to %s successful", url)

        response.put(resp.text)
        return response

    else:
        raise HandledError(
            message="Failed POST to %s:\n%s" % (url, msg),
            status_code=resp.status_code)


def get_v2_access_token(token_url: str, client_id: str,
                        client_secret: str,
                        scope: Optional[Iterable] = None) -> str:

    Log.debug("Fetching Oauthx2 access token")

    Log.debug("Input: token_url=%s client_id=%s client_secret=%s scope=%s",
              token_url, client_id, client_secret, scope)

    client = oauthlib.BackendApplicationClient(client_id=client_id)
    oauth = requests_oauthlib.OAuth2Session(client=client)

    Log.debug("Sending POST request to %s", token_url)
    token = oauth.fetch_token(token_url=token_url,
                              client_id=client_id,
                              client_secret=client_secret,
                              include_client_id=True,
                              scope=scope)

    try:
        return token["access_token"]

    except KeyError:
        raise HandledError(message="Missing access_token in response",
                           status_code=404)


def post_request_to_v2_endpoint(
        token_url: str, publish_url: str, client_id: str,
        client_secret: str, data: Mapping, auth_token: str = None,
        scope: Optional[Iterable] = None) -> Response:

    if not (token_url or auth_token):
        raise ValueError("You must provide at least token_url or auth_token. Aborting")

    Log.debug("Preparing to send POST request to Oauth2 enabled API")
    Log.debug("Request input: token_url=%s publish_url=%s client_id=%s "
              "client_secret=%s scope=%s data=%s",
              token_url, publish_url, client_id, client_secret, scope, data)

    Log.debug("Initializing authentication flow")

    if auth_token:
        Log.debug("Skipping get_v2_access_token call, "
                  "using provided auth_token: %s", auth_token)
        token = auth_token

    else:
        token = get_v2_access_token(token_url, client_id, client_secret, scope)

    return send_http_request(url=publish_url,
                             data=data,
                             headers={"Authorization": "Bearer {}".format(token)})
