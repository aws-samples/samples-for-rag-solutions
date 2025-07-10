#!/usr/bin/env python3
"""
CDK App for RFI Solution
"""
import aws_cdk as cdk
from rfi_stack import RFIStack

app = cdk.App()

# Get environment configuration
env = cdk.Environment(
    account=app.node.try_get_context("account"),
    region=app.node.try_get_context("region") or "us-west-2"
)

RFIStack(app, "RFIStack", env=env)

app.synth()