"""Train model using training data"""

import json
import boto3
import random
import decomp  # decomp model


s3 = boto3.resource('s3')


def get_data(bucket, prefix='data/', suffix='.json'):
	"""Get and assemble training data from s3"""
	bucket_resource = s3.Bucket(bucket)  # bucket resource
	keys = [obj.key for obj in bucket_resource.objects.filter(Prefix=prefix) if obj.key.endswith(suffix)]  # data keys
	data = {}  # combined dataset
	for key in keys:
		obj = s3.Object(bucket, key)  # get data object
		body = json.loads(obj.get()['Body'].read().decode('utf-8'))  # dict - {time: {exits}}
		data.update(body)  # update dataset
	return data


def train_test_data(data, t=.1):
	"""Separate data into training and test data
	t = fraction of data that becomes test data
	"""
	keys = list(data.keys())
	random.shuffle(keys)  # randomly shuffle keys
	idx = int(len(data)*t)  # cutoff between train and test sets
	test_data = {key: data[key] for key in keys[:idx]}
	train_data = {key: data[key] for key in keys[idx:]}
	return train_data, test_data


def lambda_handler(event, context):
	# get query string params
	params = event['queryStringParameters'] if type(event['queryStringParameters']) is dict else {}  # query string params
	bucket = params['bucket'] if 'bucket' in params else 'sfo-dev-virtualqueue'  # s3 bucket name
	model = params['model'] if 'model' in params else 'decomp'  # model to train
	print('params:', {'bucket': bucket, 'model': model})  # log params

	base_data = get_data(bucket)  # get taxi dataset
	train_data, test_data = train_test_data(base_data)  # divide base_data into train and test sets
	print('train: %s, test: %s' % (len(train_data), len(test_data)))  # log amount of training, test data

	# get model training function
	if model == 'decomp':
		trainer = decomp.decomposition
		validator = decomp.validate_decomp
	else:
		trainer, validator = (None, None)

	model_info = trainer(train_data)  # train
	validator(model_info, test_data)  # test (adds rmse metric to model)
	print('model_info:', list(model_info.keys()))  # log model info

	# write to s3
	key = 'models/%s.json' % model
	obj = s3.Object(bucket, key)  # create s3 object
	obj.put(Body=json.dumps(model_info))  # put data in object body
	print('wrote file %s to bucket %s' % (key, bucket))
