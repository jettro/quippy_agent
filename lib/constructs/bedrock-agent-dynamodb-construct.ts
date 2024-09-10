import {Construct} from "constructs";
import * as cdk from "aws-cdk-lib";
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

export interface BedrockAgentDynamodbConstructProps extends cdk.StackProps{

}

export class BedrockAgentDynamodbConstruct extends Construct {
    public readonly knowledgeItemsTable: dynamodb.Table;

    constructor(scope: Construct, id: string, props: BedrockAgentDynamodbConstructProps) {
        super(scope, id);

        // Define the DynamoDB table
        this.knowledgeItemsTable = new dynamodb.Table(this, 'KnowledgeItemsTable', {
            partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
            sortKey: { name: 'create_date', type: dynamodb.AttributeType.STRING },
            billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
            removalPolicy: cdk.RemovalPolicy.DESTROY, // NOT recommended for production code
        });

    }
}