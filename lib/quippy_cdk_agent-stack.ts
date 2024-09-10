import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import {Construct} from 'constructs';
import {BedrockAgentLambdaConstruct} from "./constructs/bedrock-agent-lambda-construct";
import {BedrockAgentDynamodbConstruct} from "./constructs/bedrock-agent-dynamodb-construct";

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

    }
}
