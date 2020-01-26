from typing import Union

from . import (
    HandledError,
    Log,
    Response,
)
from .helpers import (
    import_non_stdlib_module,
    send_http_request,
)


oauthlib          = import_non_stdlib_module("oauthlib.oauth2")
requests_oauthlib = import_non_stdlib_module("requests_oauthlib")


def post_request_to_v1_endpoint(url: str, client_key: str, client_secret: str,
        resource_owner_key: str, resource_owner_secret:str, post_data: Union[None, dict]=None) -> Response:
    """Implements https://requests-oauthlib.readthedocs.io/en/latest/oauth1_workflow.html"""

    response = Response()

    oauth = requests_oauthlib.OAuth1Session(
        client_key=client_key,
        client_secret=client_secret,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret)

    Log.info("Posting status to Oauth1 endpoint {}".format(url))
    resp = oauth.post(url, data=post_data)

    msg = "status_code: {}\ncontent: {}\nheaders: {}".format(resp.status_code,
                                                             resp.json(),
                                                             resp.headers)

    Log.debug("Received response from {}:\n{}".format(url, msg))

    if resp.status_code == 200:
        Log.info("POST request to {} successful".format(url))

        response.put_text(resp.text)
        return response

    else:
        raise HandledError(
            message="Failed POST to {}:\n{}".format(url, msg),
            status_code=resp.status_code)


def get_v2_access_token(token_url: str, client_id: str, client_secret: str, scope: Union[list, None]=None) -> str:
    Log.debug("Fetching Oauth2 access token")

    Log.debug("Input: token_url={} client_id={} client_secret{} scope={}".format(
        token_url, client_id, client_secret, scope))

    client = oauthlib.BackendApplicationClient(client_id=client_id)
    oauth = requests_oauthlib.OAuth2Session(client=client)

    Log.debug("Sending POST request to {}".format(token_url))
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


def post_request_to_v2_endpoint(token_url: str, publish_url: str, client_id: str, client_secret: str, data: dict, auth_token: Union[str, None]=None, scope: Union[list, None]=None) -> Response:
    if not (token_url or auth_token):
        raise ValueError("You must provide at least token_url or auth_token. Aborting")

    Log.debug("Preparing to send POST request to Oauth2 enabled API")
    Log.debug("Request input: token_url={} publish_url={} client_id={} client_secret{} scope={} data={}".format(
        token_url, publish_url, client_id, client_secret, scope, data))

    Log.debug("Initializing authentication flow")

    if auth_token:
        Log.debug("Skipping get_v2_access_token call, using provided auth_token: {}".format(auth_token))
        token = auth_token

    else:
        token = get_v2_access_token(token_url, client_id, client_secret, scope)

    return send_http_request(url=publish_url,
                             data=data,
                             headers={"Authorization": "Bearer {}".format(token)})
