import logging
import boto3
import json
import os
import uuid

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
	function = event['function']
	parameters = event.get('parameters', [])

	logger.info(f"Calling function with name: {function}")
	logger.info(f"Calling with parameters: {parameters}")

	# Execute your business logic here. For more information, refer to: https://docs.aws.amazon.com/bedrock/latest/userguide/agents-lambda.html
	if function == 'find-url':
		# One parameter with the name url of type string
		url_to_find = parameters[0].get('value')
		function_response = find_url_details(url_to_find)
	elif function == 'store-knowledge':
		logger.info("About to store the knowledge")

		# Extract the relevant parameters using next() or handle if not found.
		knowledge_value = next((param['value'] for param in parameters if param['name'] == 'knowledge'), None)
		title = next((param['value'] for param in parameters if param['name'] == 'title'), None)
		source = next((param['value'] for param in parameters if param['name'] == 'source'), None)

		# create knowledge
		function_response = store_knowledge(title=title, knowledge=knowledge_value, source=source)
	else:
		function_response = f"function is unknown {function}"

	response_body = {
		"TEXT": {
			"body": function_response
		}
	}

	action_response = {
		'actionGroup': action_group,
		'function': function,
		'functionResponse': {
			'responseBody': response_body
		}

	}

	method_response = {'response': action_response, 'messageVersion': event['messageVersion']}
	logger.info("Response: {}".format(method_response))

	return method_response


def find_url_details(url: str):
	logger.info(f"url received: {url}")
	result = {
		"source": url,
		"title": "Dev website from jettro coenradie",
		"knowledge": "Jettro writes about LLMs, search and other Gen AI topics"
	}
	return f"The title is {result.get('title')}, the knowledge is {result.get('knowledge')} and the source is {url}"


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
	return f"The knowledge is stored: {json.dumps(response)}"
