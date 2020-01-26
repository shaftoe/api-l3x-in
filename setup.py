import setuptools


VERSION = None

with open("VERSION") as f:
    VERSION = f.read().rstrip()


setuptools.setup(
    name="api-l3x-in",
    version=VERSION,

    description="api.l3x.in source code",

    author="Alexander Fortin",

    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),

    install_requires=[
        "aws-cdk.core",
        "aws-cdk.aws-apigateway",
        "aws-cdk.aws-certificatemanager",
        "aws-cdk.aws-lambda",
        "aws-cdk.aws-logs",
        "aws-cdk.aws-sns",
        "aws-cdk.aws-sns-subscriptions",
    ],

    python_requires=">=3.8",

)
