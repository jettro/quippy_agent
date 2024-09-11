import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';

import {Construct} from "constructs";

export interface BedrockAgentLambdaConstructProps extends cdk.StackProps {
    dependenciesLayer: lambda.ILayerVersion;
    tableARN: string;
}

export class BedrockAgentLambdaConstruct extends Construct {
    public readonly bedrockAgentLambda: lambda.Function;

    constructor(scope: Construct, id: string, props: BedrockAgentLambdaConstructProps) {
        super(scope, id);

        this.bedrockAgentLambda = new lambda.Function(this, 'LambdaBedrockAgent', {
            runtime: lambda.Runtime.PYTHON_3_12,
            handler: 'app.handler',
            code: lambda.Code.fromAsset('lambda/app_agent_knowledge_items_package'),
            layers: [props.dependenciesLayer],
            environment: {
                'TABLE_ARN': props.tableARN,
            },
            timeout: cdk.Duration.seconds(60),
        });

        const principal = new iam.ServicePrincipal("bedrock.amazonaws.com");

        // Add permission for Bedrock to call the Lambda function
        this.bedrockAgentLambda.addPermission("agent-invoke-lambda", {
            principal: principal,
            action: "lambda:InvokeFunction",
        })
    }
}