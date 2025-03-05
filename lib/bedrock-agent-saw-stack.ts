import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { bedrock } from '@cdklabs/generative-ai-cdk-constructs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { AgentActionGroup } from '@cdklabs/generative-ai-cdk-constructs/lib/cdk-lib/bedrock';
import * as path from 'path';
import { NagSuppressions } from 'cdk-nag';
import { AwsSolutionsChecks } from 'cdk-nag';

/**
 * Stack for deploying an Amazon Bedrock Agent that can troubleshoot AWS resources
 * using AWS Support Automation Workflow (SAW) documents. SAW documents are curated AWS Systems Manager
 * self-service automation runbooks created by AWS Support Engineering to troubleshoot common AWS issues.
 */
export class BedrockAgentSawStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Add CDK Nag for best practices validation
    cdk.Aspects.of(this).add(new AwsSolutionsChecks());

    const lambdaRole = this.createLambdaExecutionRole();
    const agent = this.createBedrockAgent();
    NagSuppressions.addResourceSuppressions(agent.role, [
      {
        id: 'AwsSolutions-IAM5',
        reason: 'Bedrock Agent requires these permissions to invoke models and interact with action group functions'
      }
    ], true);
    const actionGroupFunction = this.createActionGroupFunction(lambdaRole);
    this.createActionGroup(agent, actionGroupFunction);

    new bedrock.AgentAlias(this, 'SAWAlias', {
      aliasName: `SAW-agent-${Date.now()}`,
      agent: agent,
      description: 'Alias for AWS Support Automation Workflow troubleshooting agent'
    });

    new cdk.CfnOutput(this, 'AgentId', { value: agent.agentId, description: 'The ID of the Bedrock Agent' });
  }

  /**
   * Creates the IAM role for the Lambda function with necessary permissions
   * to execute AWS Support Automation Workflow documents and access AWS resources
   * for troubleshooting.
   */
  private createLambdaExecutionRole(): iam.Role {
    const lambdaRole = new iam.Role(this, 'TroubleshootAWSResourcesLambdaExecutionRole', {
      roleName: 'TroubleshootAWSResourcesLambdaExecutionRole',
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      inlinePolicies: {
        TroubleshootAWSResourcesLambdaExecutionPolicy: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'iam:PassRole',
                'ssm:StartAutomationExecution',
                'ssm:GetAutomationExecution',
              ],
              resources: ['*'],
            }),
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'logs:CreateLogGroup',
                'logs:CreateLogStream',
                'logs:PutLogEvents',
              ],
              resources: ['arn:aws:logs:*:*:*'],
            }),
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'ec2:Describe*',
                'eks:DescribeCluster',

                // IAM permissions
                'iam:GetInstanceProfile',
                'iam:GetRole',
                'iam:ListAttachedRolePolicies',

                // SSM permissions
                'ssm:DescribeInstanceInformation',
                'ssm:ListCommandInvocations',
                'ssm:ListCommands',
                'ssm:SendCommand',

                // S3 permissions
                's3:GetBucketNotification',
                's3:ListBucket',
                's3:GetBucketPolicy',
                's3:GetBucketLocation',

                // Lambda permissions
                'lambda:GetFunction',
                'lambda:GetPolicy',
                'lambda:ListEventSourceMappings',
                'lambda:GetEventSourceMapping',
                'lambda:ListFunctionEventInvokeConfigs'
              ],
              resources: ['*'],
            }),
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'ec2:DescribeIamInstanceProfileAssociations',
                'iam:SimulateCustomPolicy',
                'iam:SimulatePrincipalPolicy',
              ],
              resources: ['*'],
            }),
          ],
        }),
      },
    });

    NagSuppressions.addResourceSuppressions(lambdaRole, [
      { id: 'AwsSolutions-IAM5', reason: 'Lambda role requires these permissions to execute AWS Support Automation Workflow documents' },
    ], true);

    return lambdaRole;
  }

  /**
   * Creates the Bedrock Agent with appropriate configuration
   */
  private createBedrockAgent(): bedrock.Agent {
    return new bedrock.Agent(this, 'Agent', {
      foundationModel: bedrock.BedrockFoundationModel.ANTHROPIC_CLAUDE_3_5_SONNET_V2_0,
      instruction: `You are an AWS Support Engineer specializing in troubleshooting AWS resources using AWS Support Automation Workflow (SAW) documents. SAW documents are curated AWS Systems Manager self-service automation runbooks created by AWS Support Engineering with best practices learned from solving customer issues.

When helping users:
1. Ask clarifying questions to understand their specific issue with AWS resources
2. Explain which AWS Support Automation Workflow document you'll use to troubleshoot their problem
3. Request the necessary parameters required for the troubleshooting process
4. Run the appropriate troubleshooting function
5. Analyze the results and provide a clear explanation of the findings
6. Suggest specific remediation steps based on the identified issues

Always provide context about what the troubleshooting process will check and how it can help resolve their issue.`,
      shouldPrepareAgent: true,
    });
  }

  /**
   * Creates the Lambda function that will handle the action group requests and execute SAW documents
   */
  private createActionGroupFunction(role: iam.Role): lambda.Function {
    return new lambda.Function(this, 'ActionGroupFunction', {
      runtime: lambda.Runtime.PYTHON_3_13,
      handler: 'app.lambda_handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/saw_troubleshooting')),
      layers: [
        lambda.LayerVersion.fromLayerVersionArn(
          this,
          'PowerToolsLayer',
          `arn:aws:lambda:${this.region}:017000801446:layer:AWSLambdaPowertoolsPythonV2:71`
        )
      ],
      timeout: cdk.Duration.minutes(3),
      role: role,
    });
  }
  

  /**
   * Creates the action group for AWS Support Automation Workflow and adds it to the agent
   */
  private createActionGroup(agent: bedrock.Agent, actionGroupFunction: lambda.Function): void {
    const actionGroup = new AgentActionGroup({
      name: 'SAW-troubleshooting-action-group',
      description: 'Use this function to troubleshoot AWS resources using AWS Support Automation Workflow (SAW) documents',
      executor: bedrock.ActionGroupExecutor.fromlambdaFunction(actionGroupFunction),
      enabled: true,
      apiSchema: bedrock.ApiSchema.fromLocalAsset(path.join(__dirname, '../bedrock_agent_schemas/schema.json')),
    });

    agent.addActionGroup(actionGroup);
  }

}
