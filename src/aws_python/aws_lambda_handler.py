"""AWS Lambda handler for the AWS Python example."""

from mangum import Mangum

from aws_python.main import create_app

APP = create_app()

handler = Mangum(APP)
