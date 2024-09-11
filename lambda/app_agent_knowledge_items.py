import logging
import boto3
import json
import os
import uuid
import requests
from bs4 import BeautifulSoup


from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Set the log level to INFO

# Initialize the DynamoDB resource
dynamodb = boto3.resource('dynamodb')
# Extract the table name from the ARN
table_arn = os.getenv('TABLE_ARN')
table_name = table_arn.split('/')[1]
table = dynamodb.Table(table_name)


def handler(event, context):
    agent = event['agent']
    action_group = event['actionGroup']
    api_path = event['apiPath']
    logger.info(f"Calling function with API path: {api_path}")

    parameters = event.get('requestBody', {}).get('content', {}).get('application/json', {}).get('properties', [])
    if not parameters:
        logger.warning("No parameters found in the event")
    else:
        logger.info(f"Calling with parameters: {parameters}")


    # Execute your business logic here. For more information, refer to: https://docs.aws.amazon.com/bedrock/latest/userguide/agents-lambda.html
    if api_path == '/find-url':
        # One parameter with the name url of type string
        url_to_find = next((param['value'] for param in parameters if param['name'] == 'url'), None)
        function_response = json.dumps(find_url_details(url_to_find))
    elif api_path == '/store-knowledge':
        logger.info("About to store the knowledge")

        # Extract the relevant parameters using next() or handle if not found.
        knowledge_value = next((param['value'] for param in parameters if param['name'] == 'knowledge'), None)
        title = next((param['value'] for param in parameters if param['name'] == 'title'), None)
        source = next((param['value'] for param in parameters if param['name'] == 'source'), None)

        # create knowledge
        function_response = json.dumps(store_knowledge(title=title, knowledge=knowledge_value, source=source))
    elif api_path == '/list-knowledge':
        logger.info("About to list the knowledge")
        num_items = next((param['value'] for param in parameters if param['name'] == 'num_items'), 10)
        continuation_token = next((param['value'] for param in parameters if param['name'] == 'continuation_token'), None)
        function_response = json.dumps(list_knowledge(num_items, continuation_token))
    else:
        function_response = f"API Path is unknown {api_path}"

    response_body = {
        "application/json": {
            "body": function_response
        }
    }

    action_response = {
        'actionGroup': action_group,
        'apiPath': api_path,
        'httpMethod': 'POST',
        'httpStatusCode': 200,
        'responseBody': response_body
    }

    method_response = {'response': action_response, 'messageVersion': event['messageVersion']}
    logger.info("Response: {}".format(method_response))

    return method_response


def find_url_details(url: str):
    logger.info(f"url received: {url}")

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        soup = BeautifulSoup(response.content, 'html.parser')

        title = soup.title.string if soup.title else 'No title found'
        description_tag = soup.find('meta', attrs={'name': 'description'})
        description = description_tag['content'] if description_tag else 'No description found'

        result = {
            "source": url,
            "title": title,
            "knowledge": description
        }
    except requests.RequestException as e:
        logger.error(f"Error fetching URL: {e}")
        result = {
            "source": url,
            "title": "Error",
            "knowledge": "Could not retrieve information"
        }

    return result

def store_knowledge(title: str, knowledge: str, source: str):
    logger.info(f"knowledge received {knowledge}")
    # Generate a unique ID using UUID
    unique_id = str(uuid.uuid4())
    # Generate current timestamp in ISO 8601 format
    create_date = datetime.utcnow().isoformat() + 'Z'  # Add 'Z' to indicate UTC

    response = table.put_item(Item={
        'id': unique_id,
        'title': title,
        'knowledge': knowledge,
        'source': source,
        'create_date': create_date
    })
    logger.info(f"Response from dynamo: {response}")
    return {
        "message": "The provided knowledge item is stored."
    }


def list_knowledge(num_items, continuation_token):
    scan_kwargs = {
        'Limit': num_items
    }
    if continuation_token:
        scan_kwargs['ExclusiveStartKey'] = json.loads(continuation_token)

    response = table.scan(**scan_kwargs)
    items = response.get('Items', [])
    next_token = response.get('LastEvaluatedKey', None)

    result = {
        'knowledgeItems': items
    }
    if next_token:
        result['continuationToken'] = json.dumps(next_token)
    return result
