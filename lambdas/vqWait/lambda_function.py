import json
from botocore.vendored import requests
import datetime as dt


def get_prediction(endpoint, api_key, params):
	"""Get prediction from /demand/predict endpoint
	params = query string parameters
	"""
	r = requests.get(endpoint, params=params, headers={'x-api-key': api_key})
	prediction = json.loads(r.text) if r.status_code == 200 else {}
	return prediction


def wait_time(prediction, qlen):
	"""Get wait time for all positions in queue"""
	preds = 0  # cumulative preds
	w = 0  # cumulative wait
	waits = {}
	for interval in prediction['intervals']:
		start_time = dt.datetime.strptime(interval['start_time'], '%Y-%m-%d %H:%M:%S')
		end_time = dt.datetime.strptime(interval['end_time'], '%Y-%m-%d %H:%M:%S')
		int_time = (end_time - start_time).seconds  # interval length
		for p in range(int(preds), min([int(preds+interval['prediction']), qlen])):
			waits[str(p)] = int_time * (p+1 - preds) / (interval['prediction']) + w
		preds += interval['prediction']
		w += int_time
	for p in range(int(preds), qlen):  # remaining positions
		waits[str(p)] = w
	return waits


def lambda_handler(event, context):
	# get query string params
	params = event['queryStringParameters'] if type(event['queryStringParameters']) is dict else {}  # query string params
	queue = params['queue']  # required: vq, vk, vp, pq
	pqlen = int(params['pqlen']) if 'pqlen' in params else 0
	vplen = int(params['vplen']) if 'vplen' in params else 0
	vklen = int(params['vklen']) if 'vklen' in params else 0
	pkratio = float(params['pkratio']) if 'pkratio' in params else 4/5
	endpoint = params['endpoint'] if 'endpoint' in params else 'https://woykgpo9zk.execute-api.us-west-2.amazonaws.com/dev/demand/predict'  # prediction endpoint
	api_key = params['apikey'] if 'apikey' in params else 'Yb2NjaFqIw303Ab2XlNfi9oqM2SE9ICA6JtYMjd4'
	print('params:', {'queue': queue, 'pqlen': pqlen, 'vplen': vplen, 'vklen': vklen, 'pkratio': pkratio, 'endpoint': endpoint})  # log params

	# get prediction
	params['window'] = 4*60  # 4 hour prediction window
	prediction = get_prediction(endpoint, api_key, params)  # get prediction

	# assemble queue info
	qlen = pqlen if queue == 'pq' else vplen + vklen

	# get wait times for all positions in queue
	waits = wait_time(prediction, qlen)  # {pos: wait}

	# assembe output
	if queue == 'pq':
		output = waits
	else:
		vp_waits = {}
		vk_waits = {}
		p = 0  # vp index
		k = 0  # vk index
		i = 0  # p/k counter -- add to vk when i >= 1, increment by pkratio
		for key, value in waits.items():
			i = 0 if k > vklen else 1 if p > vplen else i + 1 - pkratio
			if i >= 1:
				vk_waits[str(k)] = value  # add to vk queue
				k += 1  # increment vk index
				i = 0  # reset i
			else:
				vp_waits[str(p)] = value  # add to vp queue
				p += 1  # indrement vp index
		output = {'vp': vp_waits, 'vk': vk_waits}
		if queue == 'vp':
			output = output['vp']
		elif queue == 'vk':
			output = output['vk']

	return {
		'statusCode': 200,
		'body': json.dumps(output)
	}
