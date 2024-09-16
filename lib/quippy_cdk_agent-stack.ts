import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import {Construct} from 'constructs';
import {bedrock} from '@cdklabs/generative-ai-cdk-constructs';
import {BedrockAgentLambdaConstruct} from "./constructs/bedrock-agent-lambda-construct";
import {BedrockAgentDynamodbConstruct} from "./constructs/bedrock-agent-dynamodb-construct";
import {AgentActionGroup} from "@cdklabs/generative-ai-cdk-constructs/lib/cdk-lib/bedrock";
import * as path from "node:path";

export class QuippyCdkAgentStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props);

        const bedrockAgentTable = new BedrockAgentDynamodbConstruct(this, 'BedrockAgentDynamodbConstruct', {});

        // Create a Lambda Layer for dependencies
        const dependenciesLayer = new lambda.LayerVersion(this, 'DependenciesLayer', {
            code: lambda.Code.fromAsset('lambda/dependencies_layer'),
            compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
            description: 'A layer to include dependencies for the Lambda functions',
        });

        const bedrockAgentLambda = new BedrockAgentLambdaConstruct(this, 'BedrockAgentConstruct', {
            dependenciesLayer: dependenciesLayer,
            tableARN: bedrockAgentTable.knowledgeItemsTable.tableArn,
        });

        // Grant the Lambda function permissions to access the DynamoDB table
        bedrockAgentTable.knowledgeItemsTable.grantReadWriteData(bedrockAgentLambda.bedrockAgentLambda);

        const agent = new bedrock.Agent(this, 'Agent', {
            foundationModel: bedrock.BedrockFoundationModel.ANTHROPIC_CLAUDE_V2_1,
            instruction: 'You are a helpful and friendly agent that assists in storing knowledge items. ' +
                'There are two tools you can use. One uses a URL as input. That tool obtains more information ' +
                'about the URL like the title and the knowledge provided by the website from the URL. The ' +
                'other tool takes the title, source and knowledge to store it somewhere.',
            enableUserInput: true,
            shouldPrepareAgent: true
        });

        const actionGroup = new AgentActionGroup(this, 'KnowledgeItemActionGroup', {
            actionGroupName: 'store-knowledge-items-action-group',
            description: 'Use these functions to get more information about a url and to store knowledge items.',
            actionGroupExecutor: {
                lambda: bedrockAgentLambda.bedrockAgentLambda
            },
            actionGroupState: "ENABLED",
            apiSchema: bedrock.ApiSchema.fromAsset(path.join(__dirname, 'action-group.yaml')),
        });

        agent.addActionGroups([actionGroup]);

        const agentAlias = agent.addAlias({
            aliasName: 'knowledge-item-agent-alias',
            description: 'alias for my agent handling knowledge items',
        })

        new cdk.CfnOutput(this, 'AgentId', {value: agent.agentId});
        new cdk.CfnOutput(this, 'AgentAliasId', {value: agentAlias.aliasId});
    }
}
