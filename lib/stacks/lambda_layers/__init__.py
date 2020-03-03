from os import environ as env
from aws_cdk import (
    aws_lambda,
    core,
)


from utils.cdk import (
    get_layer,
    DEFAULT_RUNTIME,
)


class LambdaLayersStack(core.Stack):

    # pylint: disable=redefined-builtin
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        """
        Provide `layers` attribute as shareble mapping of available Lambda Layers.

        e.g.
        self.layers = {
            "requests": requests_layer,
            "bs4:, bs4_layer,
            ...
        }

        XXX: maybe replace `requests` layer with AWS officially supported one:
        https://aws.amazon.com/blogs/compute/upcoming-changes-to-the-python-sdk-in-aws-lambda/
        """

        super().__init__(scope, id, **kwargs)

        self.layers = {layer.lower(): get_layer(self,
                                                f"lambda-layer-python3-{layer}",
                                                code_path=f"lib/stacks/{id}/layers/{layer}",
                                                description=f"Adds {layer} dependecy",
                                                compatible_runtimes=[
                                                    aws_lambda.Runtime.PYTHON_3_7,
                                                    DEFAULT_RUNTIME,
                                                ])
                       for layer in env.get("LAMBDA_LAYERS", "")
                       .replace(" ", "")
                       .split(",")
                       if layer}
