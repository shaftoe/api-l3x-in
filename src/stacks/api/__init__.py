from os import environ as env
from typing import Iterable

from aws_cdk import (
    assets,
    aws_apigateway,
    aws_certificatemanager,
    aws_lambda,
    aws_logs,
    core,
)

from utils.cdk import get_lambda


class ApiStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, lambda_layers: Iterable[aws_lambda.ILayerVersion], **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        my_lambda = get_lambda(
            self,
            id,
            code='src/stacks/{}'.format(id),
            handler='api.handler',
            environment={
                'CORS_ALLOW_ORIGIN': env['CORS_ALLOW_ORIGIN'],
                'PUSHOVER_TOKEN': env['PUSHOVER_TOKEN'],
                'PUSHOVER_USERKEY': env['PUSHOVER_USERKEY'],
                'LAMBDA_FUNCTIONS_LOG_LEVEL': env.get('LAMBDA_FUNCTIONS_LOG_LEVEL', 'INFO'),
            },
            layers=[
                lambda_layers['requests_oauthlib'],
            ],
        )

        cert = aws_certificatemanager.Certificate(
            self,
            '{}-certificate'.format(id),
            domain_name=env['API_DOMAIN'],
        )

        domain = aws_apigateway.DomainNameOptions(
            certificate=cert,
            domain_name=env['API_DOMAIN'],
        )

        cors = aws_apigateway.CorsOptions(
            allow_methods=['POST'],
            allow_origins=[env['CORS_ALLOW_ORIGIN']]
                            if env.get('CORS_ALLOW_ORIGIN')
                            else aws_apigateway.Cors.ALL_ORIGINS,
        )

        aws_apigateway.LambdaRestApi(
            self,
            '{}-gateway'.format(id),
            handler=my_lambda,
            domain_name=domain,
            default_cors_preflight_options=cors,
        )
