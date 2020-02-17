import utils
import utils.handlers


def handler(event, context) -> utils.Response:
    """lambda entry point"""
    return utils.handlers.EventHandler(
        name="medium",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=lambda x: NotImplementedError(
            "Requires approval from Medium.com: "
            "https://github.com/Medium/medium-api-docs#22-self-issued-access-tokens")
    ).response
