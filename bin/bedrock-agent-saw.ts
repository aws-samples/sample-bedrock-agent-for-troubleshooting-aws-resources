#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { BedrockAgentSawStack } from '../lib/bedrock-agent-saw-stack';

const app = new cdk.App();
new BedrockAgentSawStack(app, 'BedrockAgentSawStack', {});