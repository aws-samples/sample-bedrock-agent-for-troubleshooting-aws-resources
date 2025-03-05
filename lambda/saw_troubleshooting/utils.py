"""
Amazon Bedrock Agent for AWS Support Automation Workflow (SAW) - Utility Functions

This module provides utility functions for executing AWS Support Automation Workflow (SAW) documents
and waiting for their completion. SAW documents are curated AWS Systems Manager self-service
automation runbooks created by AWS Support Engineering to troubleshoot common AWS issues.
"""

from typing import Any, Dict, List, Optional
import json

import boto3
from aws_lambda_powertools.logging import Logger
from botocore.exceptions import ClientError, WaiterError
from botocore.waiter import WaiterModel, create_waiter_with_client

logger = Logger()

ssm = boto3.client('ssm')


def wait_for_automation_execution(execution_id: str, max_attempts: int = 30, delay: int = 10) -> Dict[str, Any]:
    """
    Wait for AWS Support Automation Workflow execution to complete.

    Args:
        execution_id: The ID of the automation execution
        max_attempts: Maximum number of attempts to check the status
        delay: Delay in seconds between attempts

    Returns:
        The automation execution result

    Raises:
        WaiterError: If the automation execution fails or times out
    """
    waiter_config = {
        "version": 2,
        "waiters": {
            "AutomationExecutionComplete": {
                "operation": "GetAutomationExecution",
                "delay": delay,
                "maxAttempts": max_attempts,
                "acceptors": [
                    {
                        "expected": "Success",
                        "matcher": "path",
                        "state": "success",
                        "argument": "AutomationExecution.AutomationExecutionStatus"
                    },
                    {
                        "expected": "Failed",
                        "matcher": "path",
                        "state": "failure",
                        "argument": "AutomationExecution.AutomationExecutionStatus"
                    }
                ]
            }
        }
    }

    waiter_model = WaiterModel(waiter_config)
    waiter = create_waiter_with_client('AutomationExecutionComplete', waiter_model, ssm)

    logger.info(f"Waiting for automation execution {execution_id} to complete...")
    waiter.wait(AutomationExecutionId=execution_id)

    result = ssm.get_automation_execution(AutomationExecutionId=execution_id)
    logger.info(f"Automation execution {execution_id} completed with status: {result['AutomationExecution']['AutomationExecutionStatus']}")

    return result


def get_available_steps(execution_result: Dict[str, Any]) -> List[str]:
    """
    Extract all available step names from an automation execution result.

    Args:
        execution_result: The automation execution result

    Returns:
        List of step names
    """
    if 'AutomationExecution' not in execution_result or 'StepExecutions' not in execution_result['AutomationExecution']:
        return []

    return [step['StepName'] for step in execution_result['AutomationExecution']['StepExecutions']]


def execute_automation(document_name: str, parameters: Dict[str, list], step_name: str) -> Dict[str, Any]:
    """
    Execute an AWS Support Automation Workflow document and return the output of a specific step.
    SAW documents are curated by AWS Support Engineering to troubleshoot common AWS issues.

    Args:
        document_name: The name of the SSM Automation document
        parameters: The parameters to pass to the document
        step_name: The name of the step to extract output from

    Returns:
        The output of the specified step

    Raises:
        ClientError: If there's an error executing the automation
        KeyError: If the step executions are not found in the result
        ValueError: If the specified step is not found and no fallback is available
    """
    try:
        response = ssm.start_automation_execution(
            DocumentName=document_name,
            Parameters=parameters
        )
        execution_id = response['AutomationExecutionId']
        logger.info(f"Started automation execution: {execution_id}")
        execution_result = wait_for_automation_execution(execution_id)
        # Check if the execution result contains step executions
        if 'AutomationExecution' not in execution_result or 'StepExecutions' not in execution_result['AutomationExecution']:
            raise KeyError("StepExecutions not found in automation execution result")

        # Log all available step names for debugging
        available_steps = get_available_steps(execution_result)
        logger.info(f"Available steps in automation execution: {available_steps}")

        output = None
        for step in execution_result['AutomationExecution']['StepExecutions']:
            if step['StepName'] == step_name:
                if 'Outputs' in step:
                    output = step['Outputs']
                else:
                    logger.warning(f"Step '{step_name}' found but has no outputs")
                    output = {"Message": ["Step executed but no outputs were found"]}
                break
        
        if output is None:
            if not execution_result['AutomationExecution']['StepExecutions']:
                raise ValueError("No steps found in automation execution result")

            last_step = execution_result['AutomationExecution']['StepExecutions'][-1]
            logger.warning(f"Step '{step_name}' not found. Using output from '{last_step['StepName']}' instead.")
            output = last_step.get('Outputs', {"Message": [f"Step '{step_name}' not found. Using output from '{last_step['StepName']}' instead."]})

        logger.info(f"Automation execution output: {json.dumps(output, default=str)}")
        return output

    except ClientError as e:
        logger.error(f"Error executing automation: {e}")
        raise
    except KeyError as e:
        logger.error(f"Key error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise
