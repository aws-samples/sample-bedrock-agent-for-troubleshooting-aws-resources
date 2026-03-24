"""
Amazon Bedrock Agent for AWS Support Automation Workflow (SAW) - Action Group Lambda Function

This module defines the API endpoints for the Bedrock Agent action group that
executes AWS Support Automation Workflow (SAW) documents. SAW documents are curated AWS Systems Manager
self-service automation runbooks created by AWS Support Engineering to troubleshoot common AWS issues.
"""

from typing import Any, Dict

import boto3
# import pprint
# import json
import logging

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import BedrockAgentResolver
from aws_lambda_powertools.event_handler.openapi.params import Body
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError
from typing_extensions import Annotated

from utils import execute_automation

tracer = Tracer()
logger = Logger()
app = BedrockAgentResolver(debug = True, enable_validation=True)

ssm = boto3.client('ssm')

myLogger = logging.getLogger()
myLogger.setLevel(logging.INFO)

# @app.post("/setup-ip-monitor-vpc", description="creates an Amazon EC2 instance in the specified subnet and monitors selected target IPs (IPv4 or IPv6) by continuously running ping, MTR, traceroute and tracetcp tests.")
# @tracer.capture_method
# def setup_ip_monitor_vpc(
#     subnet_id: str = Body(description="The subnet ID for the monitor instance. Be aware that if you specify a private subnet, then you must make sure there is Internet access to allow the monitor instance to setup the test (meaning, install the CloudWatch Logs agent, interact with Systems Manager and CloudWatch)."),
#     target_ips: list = Body(description="Comma separated list of IPv4s and/or IPv6s to monitor. No spaces allowed. Maximum size is 255 characters. Be aware that if you provide an invalid IP, then the automation will fail and rollback the test setup.")
# ) -> Annotated[dict, Body(description="The output of the Automation execution")]:
#     """
#     This runbook creates an Amazon Elastic Compute Cloud (Amazon EC2) instance in the specified subnet
#     and monitors selected target IPs (IPv4 or IPv6) by continuously running ping, MTR, traceroute and tracetcp tests.
#     The results are stored in Amazon CloudWatch Logs logs, and metric filters are applied
#     to quickly visualize latency and packet loss statistics in a CloudWatch dashboard. 

#     Args:
#         subnet_id: The subnet ID for the monitor instance.
#         target_ips: Comma separated list of IPv4s and/or IPv6s to monitor. No spaces allowed.
    
#     Returns: 
#         The output of the Automation execution
#     """
#     logger.info(f"setup ip monitorong from subnet {subnet_id} (target ips list: {target_ips}) ")
#     return execute_automation(
#         'AWSSupport-SetupIPMonitoringFromVPC',
#         {'SubnetId': [subnet_id], 'TargetIPs': [target_ips]},
#         'configureCloudWatchLogsForTestResults'
#     )

@app.post("/ts-connectivity", description="diagnoses connectivity issues between resources.")
@tracer.capture_method
def Connectivity(
    source_ip: str = Body(default="False", description="The private IPv4 address of the AWS resource in your Amazon VPC you want to test connectivity from"),
    destination_ip: str = Body(description="The IPv4 address of the resource you want to connect to."),
    destination_port: str = Body(desription="The port number you want to connect to on the destination resource.")
) -> Annotated[dict, Body(description="The output of the Automation execution")]:
    """"
    The AWSSupport-ConnectivityTroubleshooter runbook diagnoses connectivity issues between the following:
    - AWS resources within an Amazon Virtual Private Cloud (Amazon VPC)
    - AWS resources in different Amazon VPCs within the same AWS Region that are connected using VPC peering
    - AWS resources in an Amazon VPC and an internet resource using an internet gateway
    - AWS resources in an Amazon VPC and an internet resource using a network address translation (NAT) gateway
    """
    logger.info(f"Connectivity {source_ip} and DestinationIP{destination_ip} with DestinationPort{destination_port}")
    return execute_automation(
        'AWSSupport-ConnectivityTroubleshooter',
        {'SourceIP': [source_ip], 'DestinationIP': [destination_ip], 'DestinationPort':[destination_port]},
        'generateReport'
    )
    
@app.post("/enable-vpc-flow-logs", description="creates Amazon Virtual Private Cloud (Amazon VPC) Flow Logs for subnets, network interfaces, and VPCs in your AWS account")
@tracer.capture_method
def enable_vpc_flow_logs(
    log_destination_type: str = Body(default="cloud-watch-logs", description="Determines where flow log data is published. (cloud-watch-logs | s3)"),
    resource_ids: list = Body(description="A comma-separated list of the IDs for the subnets, elastic network interfaces, or VPC for which you want to create a flow log."),
    traffic_type: str = Body(default="ALL", description="The type of traffic to log. You can log traffic that the resource accepts or rejects, or all traffic. (ACCEPT | REJECT | ALL)")
) -> Annotated[dict, Body(description="The output of the Automation execution")]:
    """
    This runbook creates Amazon Virtual Private Cloud (Amazon VPC) Flow Logs 
    for subnets, network interfaces, and VPCs in your AWS account. 

    Args:
        log_destination_type: where flow log data is published
        resource_ids: A comma-separated list of the IDs for the subnets, elastic network interfaces, or VPC
        traffic_type: type of traffic to log
    
    Returns: 
        The output of the Automation execution
    """
    logger.info(f"enable vpc flow logs for {resource_ids}")
    return execute_automation(
        'AWSSupport-EnableVPCFlowLogs',
        {'LogDestinationType': [log_destination_type], 'ResourceIds': resource_ids, 'TrafficType': [traffic_type]},
        'CreateFlowLogs'
    )

@app.post("/check-and-mount-efs", description="verifies the prerequisites to mount EFS file system and mounts the file system on the EC2 instance")
@tracer.capture_method
def check_and_mount_efs(
    action: str = Body(description="whether the runbook verifies prerequisites, or verifies prerequisites and mounts the file system. (Check | CheckAndMount)"),
    efs_id: str = Body(description="The ID of the file system you want to mount."),
    instance_id: str = Body(description="The ID of the Amazon EC2 instance on which you want to mount the file system."),
    region: str = Body(description="The AWS Region where the Amazon EC2 instance and file system are located.")
) -> Annotated[dict, Body(description="The output of the Automation execution")]:
    """
    This runbook verifies the prerequisites to mount your Amazon Elastic File System (Amazon EFS) file system 
    and mounts the file system on the Amazon Elastic Compute Cloud (Amazon EC2) instance you specify. 
    This runbook supports mounting your Amazon EFS file system with the DNS name, or using the mount target’s IP address. 

    Args:
        action: Check | CheckAndMount
        efs_id: ID of the file system you want to mount
        instance_id: ID of the Amazon EC2 instance on which you want to mount the file system
        region: AWS Region where the Amazon EC2 instance and file system are located
    
    Returns: 
        The output of the Automation execution
    """
    logger.info(f"check efs {efs_id}")
    return execute_automation(
        'AWSSupport-CheckAndMountEFS',
        {'Action': [action], 'EfsId': [efs_id], 'InstanceId': [instance_id], 'Region': [region]},
        'FinalOutput'
    )

@app.post("/troubleshoot-cw-agent", description="Troubleshoot Amazon CloudWatch Agent on your Amazon EC2 instance.")
@tracer.capture_method
def troubleshoot_cw_agent(
    instance_id: str = Body(description="The ID of the Amazon EC2 instance you want to troubleshoot the Amazon CloudWatch Agent on."),
    s3_upload_bucket: str = Body(description="The name of an Amazon S3 bucket to upload the collected Amazon CloudWatch Agent logs.")
) -> Annotated[dict, Body(description="The output of the Automation execution")]:
    """
    The AWSSupport-TroubleshootCloudWatchAgent runbook automates troubleshooting the Amazon CloudWatch Agent on your Amazon Elastic Compute Cloud (Amazon EC2) instances.
    The runbook performs this troubleshooting through a series of basic, and (optional) extended checks.
    The basic checks include the following:

    1. Check for an AWS Identity and Access Management (IAM) instance profile
    2. Verify if the necessary Amazon CloudWatch Agent AWS Identity and Access Management (IAM) permissions are attached to the Amazon EC2 instance

    The extended checks are only performed if the Amazon EC2 instance ID provided is an AWS Systems Manager managed instance. These extended checks include the following:

    1. Check the status of the Amazon CloudWatch Agent on the instance
    2. Analyze the logs of the Amazon CloudWatch Agent for common issues and relevant troubleshooting steps
    3. Zip the relevant logs and configuration files on the Amazon EC2 instance and optionally upload them to an Amazon Simple Storage Service (Amazon S3) bucket of your choosing
    4. Perform a connectivity check between the instance and the required endpoints

    Args:
        instance_id: The ID of the Amazon EC2 instance you want to troubleshoot the Amazon CloudWatch Agent on.
        s3_upload_bucket: The name of an Amazon S3 bucket to upload the collected Amazon CloudWatch Agent logs.    
        logger.info(f"Troubleshoot Amazon CloudWatch Agent on an EC2 instance {instance_id}")
    """
    logger.info(f"Troubleshooting the Amazon CloudWatch Agent in EC2 instance {instance_id}.")

    return execute_automation(
        'AWSSupport-TroubleshootCloudWatchAgent',
        {'InstanceId': [instance_id], 'S3UploadBucket': [s3_upload_bucket]},
        'outputFindings'
    )

@app.post("/activate-windows", description="Activate an Amazon EC2 instance for Windows Server with a license provided by Amazon.")
@tracer.capture_method
def activate_windows(
    force_activation: str = Body(default="False", description="Set it to true if you want to proceed even if Windows is already activated. (defatult: false)"),
    instance_id: str = Body(description="ID of your managed EC2 instance for Windows Server")
) -> Annotated[dict, Body(description="The output of the Automation execution")]:
    """
    The AWSSupport-ActivateWindowsWithAmazonLicense runbook activates an Amazon Elastic Compute Cloud (Amazon EC2) instance for Windows Server with a license provided by Amazon.
    The automation verifies and configures required key management service operating system settings and attempts activation.
    This includes operating system routes to Amazon's key management servers and key management service operating system settings.
    Setting the AllowOffline parameter to true allows the automation to successfully target instances that are not managed by AWS Systems Manager, but requires a stop and start of the instance.

    Args:
        force_activation: Set it to true if you want to proceed even if Windows is already activated.
        instance_id: ID of your managed EC2 instance for Windows Server

    Returns:
        The output of the Automation execution
    """
    logger.info(f"Activate windows license for an instance {instance_id}")
    return execute_automation(
        'AWSSupport-ActivateWindowsWithAmazonLicense',
        {'ForceActivation': [force_activation], 'InstanceId': [instance_id]},
        'GetActivateWindowsOfflineResult'
    )

@app.post("/troubleshoot-eb", description="Troubleshoot the potential reasons why your AWS Elastic Beanstalk environment is in a Degraded or Severe state")
@tracer.capture_method
def troubleshoot_eb(
    application_name: str = Body(description="The name of your Elastic Beanstalk application"),
    environment_name: str = Body(description="The name of your Elastic Beanstalk environment")
) -> Annotated[dict, Body(description="The output of the Automation execution")]:
    """
    The AWSSupport-TroubleshootElasticBeanstalk runbook helps you troubleshoot the potential reasons why your AWS Elastic Beanstalk environment is in a Degraded or Severe state. This automation checks the following AWS resources associated with your Elastic Beanstalk environment:
     - Configuration details for a load balancer, AWS CloudFormation stack, Amazon EC2 Auto Scaling group, Amazon Elastic Compute Cloud (Amazon EC2) instances, and virtual private cloud (VPC).
     - Network configuration issues with the associated security group rules, route tables, and network access control lists (ACLs) associated with your subnets.
     - Verifies connectivity to the Elastic Beanstalk endpoints and public internet access.
     - Verifies the status of the load balancer.
     - Verifies the status of the Amazon EC2 instances.
     - Retrieves a log bundle from your Elastic Beanstalk environment, and optionally uploads the files to Support.


    Args:
        application_name: The name of your Elastic Beanstalk application
        environment_name: The name of your Elastic Beanstalk environment

    Returns:
        The output of the Automation execution
    """
    logger.info(f"troubleshoot eb environment {environment_name}")
    return execute_automation(
        'AWSSupport-TroubleshootElasticBeanstalk',
        {'ApplicationName': [application_name], 'EnvironmentName': [environment_name]},
        'GenerateReport'
    )

@app.post("/troubleshoot-ssh", description="installs the Amazon EC2Rescue tool for Linux, and then uses the EC2Rescue tool to check or attempt to fix common issues that prevent a remote connection to the Linux machine via SSH")
@tracer.capture_method
def troubleshoot_ssh(
    action: str = Body(description="Specify whether to check for issues without fixing them or to check and automatically fix any discovered issues. (CheckAll | FixAll)"),
    instance_id: str = Body(description="ID of your EC2 instance for Linux")
) -> Annotated[dict, Body(description="The output of the Automation execution")]:
    """
    This runbook installs the Amazon EC2Rescue tool for Linux, 
    and then uses the EC2Rescue tool to check or attempt to fix common issues that prevent a remote connection to the Linux machine via SSH. 
    Optionally, changes can be applied offline by stopping and starting the instance, 
    if the user explicitly allows for offline remediation. 
    By default, the runbook operates in read-only mode.

    Args:
        action: CheckAll | FixAll
        instance_id: ID of your EC2 instance for Linux
    
    Returns: 
        The output of the Automation execution
    """
    logger.info(f"troubleshoot ssh for {instance_id}")
    return execute_automation(
        'AWSSupport-TroubleshootSSH',
        {'Action': [action], 'InstanceId': [instance_id]},
        'troubleshootSSH'
    )

@app.post("/manage-rdp-settings", description="allows the user to manage common Remote Desktop Protocol (RDP) settings, such as the RDP port and Network Layer Authentication (NLA)")
@tracer.capture_method
def manage_rdp_settings(
    instance_id: str = Body(description="ID of the managed instance to manage the RDP settings of"),
    nla_setting_action: str = Body(description="action to perform on the NLA setting: Check, Enable, Disable"),
    rdp_port_action: str = Body(description="action to apply to the RDP port (Check | Modify)"),
    remote_connections: str = Body(description="action to perform on the fDenyTSConnections setting (Check | Enable | Disable)")
) -> Annotated[dict, Body(description="The output of the Automation execution")]:
    """
    This runbook allows the user to manage common Remote Desktop Protocol (RDP) settings, 
    such as the RDP port and Network Layer Authentication (NLA). 
    By default, the runbook reads and outputs the values of the settings.

    Args:
        instance_id: ID of the managed instance to manage the RDP settings of
        nla_setting_action: action to perform on the NLA setting: Check, Enable, Disable
        rdp_port_action: action to apply to the RDP port (Check | Modify)
        remote_connections: action to perform on the fDenyTSConnections setting (Check | Enable | Disable)
    
    Returns: 
        The output of the Automation execution
    """
    logger.info(f"manage rdp settings for {instance_id}")
    return execute_automation(
        'AWSSupport-ManageRDPSettings',
        {'InstanceId': [instance_id], 'NLASettingAction': [nla_setting_action], 'RDPPortAction': [rdp_port_action], 'RemoteConnections': [remote_connections]},
        'manageRDPSettings'
    )

@app.post("/configure-ec2-metadata", description="Configure instance metadata service (IMDS) options for Amazon Elastic Compute Cloud (Amazon EC2) instances.")
@tracer.capture_method
def troubleshoot_rdp(
    instance_id: str = Body(description="The ID of the Amazon EC2 Instance you want to configure metadata options"),
    enforce_IMDSv2: str = Body(default="optional", description="Enforce IMDSv2. If you choose required, the Amazon EC2 instance will only use IMDSv2. If you choose optional, you can choose between IMDSv1 and IMDSv2 for metadata access. Default: optional")
) -> Annotated[dict, Body(description="The output of the Automation execution")]:
    """
    AWSSupport-ConfigureEC2Metadata runbook helps users configure instance metadata service (IMDS) options for Amazon Elastic Compute Cloud (Amazon EC2) instances. Using this runbook, users can configure the following:

    Enforce the use of IMDSv2 for instance metadata.
    Configure the HttpPutResponseHopLimit value.
    Allow or deny instance metadata access.

    Args:
        instance_id: The ID of the Amazon EC2 instance whose metadata settings you want to configure
        enforce_IMDSv2: Enforce IMDSv2. If you choose required, the Amazon EC2 instance will only use IMDSv2. If you choose optional, you can choose between IMDSv1 and IMDSv2 for metadata access. Default: optional

    Returns:
        The output of the Automation execution
    """
    logger.info(f"configure metadata for {instance_id}")
    return execute_automation(
        'AWSSupport-ConfigureEC2Metadata',
        {'InstanceId': [instance_id], 'EnforceIMDSv2': [enforce_IMDSv2]},
        'describeMetadataOptions'
    )

@app.post("/troubleshoot-rdp", description="check or modify common settings on the target instance which may impact Remote Desktop Protocol (RDP) connections")
@tracer.capture_method
def troubleshoot_rdp(
    instance_id: str = Body(description="The ID of the instance to troubleshoot the RDP settings of"),
    rdp_port_action: str = Body(default="Check", description="Check the current port used for RDP connections, or modify the RDP port back to 3389 and restart the service. Default: Check")
) -> Annotated[dict, Body(description="The output of the Automation execution")]:
    """
    The AWSSupport-TroubleshootRDP runbook allows the user to check or modify common settings on the target instance which
    may impact Remote Desktop Protocol (RDP) connections, such as the RDP port, Network Layer Authentication (NLA) and Windows Firewall profiles.
    Optionally, changes can be applied offline by stopping and starting the instance, if the user explicitly allows for offline remediation.
    By default, the runbook reads and outputs the values of the settings.

    Args:
        instance_id: The ID of the instance to troubleshoot the RDP settings of
        rdp_port_action: Check the current port used for RDP connections, or modify the RDP port back to 3389 and restart the service. Default: Check

    Returns:
        The output of the Automation execution
    """
    logger.info(f"reset access for {instance_id}")
    return execute_automation(
        'AWSSupport-TroubleshootRDP',
        {'InstanceId': [instance_id], 'RDPPortAction': [rdp_port_action]},
        'describeSourceInstance'
    )

@app.post("/reset-ec2-access", description="use the EC2Rescue tool on the specified EC2 instance to re-enable password decryption using the EC2 Console (Windows) or to generate and add a new SSH key pair (Linux).")
@tracer.capture_method
def reset_ec2_access(
    instance_id: str = Body(description="ID of the EC2 instance you want to reset access for"),
    ec2_rescue_instance_type: str = Body(default="t2.small", description="EC2 instance type for the EC2Rescue instance. Default: t2.small")
) -> Annotated[dict, Body(description="The output of the Automation execution")]:
    """
    This runbook will use the EC2Rescue tool on the specified EC2 instance 
    to re-enable password decryption using the EC2 Console (Windows) or to generate and add a new SSH key pair (Linux). 
    If you lost your key pair, this automation will create a password-enabled AMI 
    that you can use to launch a new EC2 instance with a key pair you own (Windows).

    Args:
        instance_id: ID of the EC2 instance you want to reset access for
        ec2_rescue_instance_type: EC2 instance type for the EC2Rescue instance
    
    Returns: 
        The output of the Automation execution
    """
    logger.info(f"reset access for {instance_id}")
    return execute_automation(
        'AWSSupport-ResetAccess',
        {'InstanceId': [instance_id], 'EC2RescueInstanceType': [ec2_rescue_instance_type]},
        'getEC2RescueForLinuxResult'
    )
    
@app.post("/collect-eks-node-logs", description="Collect EKS worker node logs")
@tracer.capture_method
def collect_eks_node_logs(
    log_destination: str = Body(description="The S3 bucket in your account to upload the archived logs to"),
    instance_id: str = Body(description="The ID of the ec2 worker node")
) -> Annotated[dict, Body(description="The output of the Automation execution")]:
    """
    Collect logs from an EKS worker node using the
    AWSSupport-CollectEKSInstanceLogs SAW document created by AWS Support
    Engineering.

    Args:
        instance_id: The ID of the worker node
        log_destination: The S3 bucket in your account to upload the archived logs to

    Returns:
        The output of the Automation execution
    """

    logger.info(f"Collecting logs from an EKS worker node {instance_id}")
    return execute_automation(
        'AWSSupport-CollectEKSInstanceLogs',
        {'LogDestination': [log_destination], 'EKSInstanceId': [instance_id]},
        'runUploadScript'
    )

@app.post("/troubleshoot-ecs-task", description="Troubleshoot an ECS Task that failed to start")
@tracer.capture_method
def troubleshoot_ecs_task(
    cluster_name: str = Body(description="The name of the ECS cluster"),
    task_id: str = Body(description="The ID of the failed task")
) -> Annotated[dict, Body(description="The output of the Automation execution")]:
    """
    Troubleshoot an ECS Task that failed to start using the
    AWSSupport-TroubleshootECSTaskFailedToStart SAW document created by AWS Support
    Engineering.

    Args:
        cluster_name: The name of the Amazon ECS cluster where the task failed to start.
        task_id: The ID of the failed task. Use the most recently failed task.

    Returns:
        The output of the Automation execution
    """
    logger.info(f"Troubleshooting an ECS task {task_id} in cluster {cluster_name}")
    return execute_automation(
        'AWSSupport-TroubleshootECSTaskFailedToStart',
        {'ClusterName': [cluster_name], 'TaskId': [task_id]},
        'ExecutionResults'
    )

@app.post("/diagnose-disk-usage", description="Diagnose disk usage of EC2 instance if disk issues can be mitigated by expanding the volume")
@tracer.capture_method
def diag_disk_usage_win(
    instance_id: str = Body(description="The ID of your Amazon EC2 instance."),
    volume_expansion_enabled: str = Body(default="true", description="Flag to control whether the document will extend the affected volumes and partitions. Set it to `false` if you do not want to make changes to the Amazon EBS volumes, their partitions, and filesystems."),
    volume_expansion_usage_trigger: str = Body(default="85", description="Minimum usage of partition space required to trigger extension (in percentage). By default 85%"),
    volume_expansion_cap_size: str = Body(default="2048", description="Maximum size that the EBS Volume will be increased to (in GiB). By default 2048 GiB."),
    volume_expansion_gib_increase: str = Body(default="20", description="Increase in GiB of the volume. The biggest net increase between `VolumeExpansionGibIncrease` and `VolumeExpansionPercentageIncrease` will be used. By default 20 GiB."),
    volume_expansion_percentage_increase: str = Body(default="20", description="Increase in percentage of the volume. The biggest net increase between `VolumeExpansionGibIncrease` and `VolumeExpansionPercentageIncrease` will be used. By default 20%."),
) -> Annotated[dict, Body(description="The output of the Automation execution")]:
    """
    The AWSPremiumSupport-TroubleshootEC2DiskUsage runbook helps you investigate
    and potentially remediate issues with Amazon Elastic Compute Cloud (Amazon EC2) instance root and non-root disk usage.
    If possible, the runbook attempts to remediate issues by extending the volume and its file system.
    To perform these tasks, this runbook orchestrates the execution of several runbooks based on the operating system of the affected instance.

    Args:
        instance_id: The ID of your Amazon EC2 instance.
        volume_expansion_enabled: Flag to control whether the document will extend the affected volumes and partitions. Set it to `false` if you do not want to make changes to the Amazon EBS volumes, their partitions, and filesystems.
        volume_expansion_usage_trigger: Minimum usage of partition space required to trigger extension (in percentage). By default `85%`.
        volume_expansion_cap_size: Maximum size that the EBS Volume will be increased to (in GiB). By default `2048` GiB.
        volume_expansion_gib_increase: Increase in GiB of the volume. The biggest net increase between `VolumeExpansionGibIncrease` and `VolumeExpansionPercentageIncrease` will be used. By default `20` GiB.
        volume_expansion_percentage_increase: Increase in percentage of the volume. The biggest net increase between `VolumeExpansionGibIncrease` and `VolumeExpansionPercentageIncrease` will be used. By default `20%`.

    Returns:
        The output of the Automation execution
    """
    logger.info(f"Starting diag_disk_usage_win()...")    
    logger.info(f"Diagnosing an EC2 Windows instance {instance_id}, while the trigger disk usage is set to {volume_expansion_usage_trigger}.")
    return execute_automation(
        'AWSPremiumSupport-TroubleshootEC2DiskUsage',
        {'InstanceId': [instance_id], 'VolumeExpansionEnabled': [volume_expansion_enabled], 'VolumeExpansionUsageTrigger': [volume_expansion_usage_trigger], 'VolumeExpansionCapSize': [volume_expansion_cap_size], 'VolumeExpansionGibIncrease': [volume_expansion_gib_increase], 'VolumeExpansionPercentageIncrease': [volume_expansion_percentage_increase]},
        'BranchOnDiagnosticResult'
    )

@app.post("/diagnose-disk-usage-win", description="Diagnose disk usage of Windows instance if disk issues can be mitigated by expanding the volume")
@tracer.capture_method
def diag_disk_usage_win(
    instance_id: str = Body(description="The ID of your Amazon EC2 instance."),
    volume_expansion_usage_trigger: str = Body(default="85", description="Minimum usage of partition space required to trigger extension (in percentage)."),
    volume_expansion_cap_size: str = Body(default="2048", description="Maximum size that the Amazon EBS Volume will be increased to (in GiB)."),
    volume_expansion_gib_increase: str = Body(default="20", description="Increase in GiB of the volume. The biggest net increase between VolumeExpansionGibIncrease and VolumeExpansionPercentageIncrease will be used."),
    volume_expansion_percentage_increase: str = Body(default="20", description="Increase in percentage of the volume. The biggest net increase between VolumeExpansionGibIncrease and VolumeExpansionPercentageIncrease will be used."),
) -> Annotated[dict, Body(description="The output of the Automation execution")]:
    """
    The AWSPremiumSupport-DiagnoseDiskUsageOnWindows runbook determines if disk issues can be mitigated by expanding the volume.

    Args:
        instance_id: The ID of your Amazon EC2 instance.
        volume_expansion_usage_trigger: Minimum usage of partition space required to trigger extension (in percentage).
        volume_expansion_cap_size: Maximum size that the Amazon EBS Volume will be increased to (in GiB).
        volume_expansion_gib_increase: Increase in GiB of the volume. The biggest net increase between VolumeExpansionGibIncrease and VolumeExpansionPercentageIncrease will be used.
        volume_expansion_percentage_increase: Increase in percentage of the volume. The biggest net increase between VolumeExpansionGibIncrease and VolumeExpansionPercentageIncrease will be used.

    Returns:
        The output of the Automation execution
    """
    logger.info(f"Starting diag_disk_usage_win()...")    
    logger.info(f"Diagnosing an EC2 Windows instance {instance_id}, while the trigger disk usage is set to {volume_expansion_usage_trigger}.")
    return execute_automation(
        'AWSPremiumSupport-DiagnoseDiskUsageOnWindows',
        {'InstanceId': [instance_id], 'VolumeExpansionUsageTrigger': [volume_expansion_usage_trigger], 'VolumeExpansionCapSize': [volume_expansion_cap_size], 'VolumeExpansionGibIncrease': [volume_expansion_gib_increase], 'VolumeExpansionPercentageIncrease': [volume_expansion_percentage_increase]},
        'RunPreChecksOnWindows'
    )
    
@app.post("/troubleshoot-eks-cluster", description="Troubleshoot an EKS cluster")
@tracer.capture_method
def troubleshoot_eks_cluster(
    cluster_name: str = Body(description="The name of the Amazon EKS cluster that you want to troubleshoot."),
    s3_bucket_name: str = Body(description="The name of the private Amazon S3 bucket where the report generated by the runbook should be uploaded.")
) -> Annotated[dict, Body(description="The output of the Automation execution")]:
    """
    Diagnose common issues with an Amazon Elastic Kubernetes Service (Amazon EKS) cluster,
    underlying infrastructure, and provides recommended remediation steps.

    Args:
        cluster_name: The name of the Amazon EKS cluster that you want to troubleshoot.
        s3_bucket_name: The name of the private Amazon S3 bucket where the report generated by the runbook should be uploaded.

    Returns:
        The output of the Automation execution
    """
    
    logger.info(f"Troubleshooting an EKS cluster {cluster_name}, report will be saved in a S3 {s3_bucket_name}")
    return execute_automation(
        'AWSPremiumSupport-TroubleshootEKSCluster',
        {'ClusterName': [cluster_name], 'S3BucketName': [s3_bucket_name]},
        'GenerateReport'
    )

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

@app.post("/troubleshoot-ecs-instance", description="Troubleshoot ECS container instance failed to register with the cluster")
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
