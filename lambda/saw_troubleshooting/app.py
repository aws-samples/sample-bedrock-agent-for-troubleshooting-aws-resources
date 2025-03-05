"""
Amazon Bedrock Agent for AWS Support Automation Workflow (SAW) - Action Group Lambda Function

This module defines the API endpoints for the Bedrock Agent action group that
executes AWS Support Automation Workflow (SAW) documents. SAW documents are curated AWS Systems Manager
self-service automation runbooks created by AWS Support Engineering to troubleshoot common AWS issues.
"""

from typing import Any, Dict

import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import BedrockAgentResolver
from aws_lambda_powertools.event_handler.openapi.params import Body
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError
from typing_extensions import Annotated

from utils import execute_automation

tracer = Tracer()
logger = Logger()
app = BedrockAgentResolver(enable_validation=True)

ssm = boto3.client('ssm')


@app.post("/troubleshoot-eks-worker-node", description="Troubleshoot EKS worker node failed to join the cluster")
@tracer.capture_method
def troubleshoot_eks_worker_node(
    cluster_name: str = Body(description="The name of the EKS cluster"),
    worker_id: str = Body(description="The ID of the worker node")
) -> Annotated[dict, Body(description="The output of the Automation execution")]:
    """
    Troubleshoot an EKS worker node that failed to join the cluster using the
    AWSSupport-TroubleshootEKSWorkerNode SAW document created by AWS Support
    Engineering.

    Args:
        cluster_name: The name of the EKS cluster
        worker_id: The ID of the worker node

    Returns:
        The output of the Automation execution
    """
    logger.info(f"Troubleshooting EKS worker node {worker_id} in cluster {cluster_name}")
    return execute_automation(
        'AWSSupport-TroubleshootEKSWorkerNode',
        {'ClusterName': [cluster_name], 'WorkerID': [worker_id]},
        'TroubleshootWorkerNode'
    )


@app.post("/troubleshoot-ecs-container-instance", description="Troubleshoot ECS container instance failed to register with the cluster")
@tracer.capture_method
def troubleshoot_ecs_container_instance(
    cluster_name: str = Body(description="The name of the ECS cluster"),
    container_instance_id: str = Body(description="The ID of the container instance")
) -> Annotated[dict, Body(description="The output of the Automation execution")]:
    """
    Troubleshoot an ECS container instance that failed to register with the cluster
    using the AWSSupport-TroubleshootECSContainerInstance SAW document created by
    AWS Support Engineering.

    Args:
        cluster_name: The name of the ECS cluster
        container_instance_id: The ID of the container instance

    Returns:
        The output of the Automation execution
    """
    logger.info(f"Troubleshooting ECS container instance {container_instance_id} in cluster {cluster_name}")
    return execute_automation(
        'AWSSupport-TroubleshootECSContainerInstance',
        {'ClusterName': [cluster_name], 'InstanceId': [container_instance_id]},
        'executeChecker'
    )
    

@app.post("/troubleshoot-s3-lambda", description="Troubleshoot why an Amazon S3 event notification failed to trigger the specified AWS Lambda function.")
@tracer.capture_method
def troubleshoot_s3_lambda(
    s3_bucket_name: str = Body(description="The name of the S3 bucket"),
    lambda_function_arn: str = Body(description="The ARN of the Lambda function")
) -> Annotated[dict, Body(description="The output of the Automation execution")]:
    """
    Troubleshoot why an Amazon S3 event notification failed to trigger a Lambda function
    using the AWSSupport-TroubleshootLambdaS3Event SAW document created by AWS Support
    Engineering.

    Args:
        s3_bucket_name: The name of the S3 bucket
        lambda_function_arn: The ARN of the Lambda function

    Returns:
        The output of the Automation execution
    """
    logger.info(f"Troubleshooting S3 event notification from bucket {s3_bucket_name} to Lambda function {lambda_function_arn}")
    return execute_automation(
        'AWSSupport-TroubleshootLambdaS3Event',
        {'S3BucketName': [s3_bucket_name], 'LambdaFunctionArn': [lambda_function_arn]},
        'GenerateReport'
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """
    Lambda handler function that processes incoming events from Bedrock Agent and
    executes the appropriate AWS Support Automation Workflow document.

    Args:
        event: The event dict from Bedrock Agent
        context: The Lambda context object

    Returns:
        The response to be sent back to Bedrock Agent
    """
    logger.info(f"Received event: {event}")
    return app.resolve(event, context)


if __name__ == "__main__":
    print(app.get_openapi_json_schema())
