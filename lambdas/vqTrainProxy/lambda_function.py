"""Proxy lambda for hand-off between api request and model training"""

import json
import boto3


def lambda_handler(event, context):
	"""Pass api request on to training lambda, invoke asynchronously"""
	# get query string params
	params = event['queryStringParameters'] if type(event['queryStringParameters']) is dict else {}  # query string params
	model = params['model'] if 'model' in params else 'decomp'  # model to train
	print('params:', {'model': model})  # log params

	lam = boto3.client('lambda', region_name='us-west-2')  # lambda client
	lam.invoke(FunctionName='vqTrain', InvocationType='Event', Payload=json.dumps(event))  # invoke asynch
	return {
		'statusCode': 200,
		'body': json.dumps('Training of model: %s in progress' % model)
	}
