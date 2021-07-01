""" Take data from request body and send to data folder in s3 bucket """

import json
import boto3
import datetime as dt


s3 = boto3.resource('s3')  # s3 resource


def fill_data(data, interval):
	"""Fill in missing data"""
	first_date = dt.datetime.strptime(data[0]['time'], '%Y-%m-%d %H:%M:%S')
	last_date = dt.datetime.strptime(data[-1]['time'], '%Y-%m-%d %H:%M:%S')
	ndates = int((last_date - first_date).total_seconds() / interval) + 1  # number of dates that there should be
	new_dates = [first_date + dt.timedelta(seconds=interval*i) for i in range(ndates)]  # fill in dates
	new_data = {str(new_date): {'exits': .01} for new_date in new_dates}  # init dataset
	for d in data:  # fill in known data
		new_data[d['time']]['exits'] = d['exits']
	return new_data


def lambda_handler(event, context):
	# get query string params
	params = event['queryStringParameters'] if type(event['queryStringParameters']) is dict else {}  # query string params
	bucket = params['bucket'] if 'bucket' in params else 'sfo-dev-virtualqueue'  # s3 bucket name
	interval = params['interval'] if 'interval' in params else 300  # time interval between datapoints (in seconds)
	now = str(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))  # current timestamp (string)
	print('params:', {'bucket': bucket, 'interval': interval, 'now': now})  # log params

	data = json.loads(event['body'])  # raw data
	new_data = fill_data(data, interval) if len(data) > 1 else data  # fill in missing data

	key = 'data/%s.json' % now  # destination file key
	print('key:', key)
	obj = s3.Object(bucket, key)  # create s3 object
	obj.put(Body=json.dumps(new_data))  # put data in object body
	return {
		'statusCode': 200,
		'body': json.dumps('Wrote file %s to bucket %s' % (key, bucket))
	}
