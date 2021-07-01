"""Get model data from s3 and return to client"""

import json
import boto3


s3 = boto3.resource('s3')


def lambda_handler(event, context):
	# get query string params
	params = event['queryStringParameters'] if type(event['queryStringParameters']) is dict else {}  # query string params
	bucket = params['bucket'] if 'bucket' in params else 'sfo-dev-virtualqueue'  # s3 bucket name
	model = params['model'] if 'model' in params else 'decomp'
	print('params:', {'bucket': bucket, 'model': model})  # log params

	# get model info from s3
	key = 'models/%s.json' % model
	print('key:', key)  # log key
	obj = s3.Object(bucket, key)
	body = json.loads(obj.get()['Body'].read().decode('utf-8'))
	return {
		'statusCode': 200,
		'body': json.dumps(body)
	}
