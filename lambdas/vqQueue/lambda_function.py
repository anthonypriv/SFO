import json
from botocore.vendored import requests


def get_prediction(endpoint, api_key, params):
	"""Get prediction from /demand/predict endpoint
	params = query string parameters
	"""
	r = requests.get(endpoint, params=params, headers={'x-api-key': api_key})
	prediction = json.loads(r.text) if r.status_code == 200 else {}
	return prediction


def lambda_handler(event, context):
	# get query string params
	params = event['queryStringParameters'] if type(event['queryStringParameters']) is dict else {}  # query string params
	pqtarget = int(params['pqtarget']) if 'pqtarget' in params else 200  # target pq length (capacity)
	pqlen = int(params['pqlen']) if 'pqlen' in params else 0  # taxis in holding lot
	vplen = int(params['vplen']) if 'vplen' in params else 0  # vp queue length
	vklen = int(params['vklen']) if 'vklen' in params else 0  # vk queue length
	pkratio = float(params['pkratio']) if 'pkratio' in params else 4/5  # p/k call ratio
	complete = float(params['complete']) if 'complete' in params else .95  # fraction of called taxis that complete SLA
	shorts = int(params['shorts']) if 'shorts' in params else 0  # number of active short trips
	pending = int(params['pending']) if 'pending' in params else 0  # number of pending entries
	sla = int(params['sla']) if 'sla' in params else 50  # max time from call to garage arrival (accept + arrive time) (minutes)
	callmax = int(params['callmax']) if 'callmax' in params else 50  # throttle on number of calls - depends on frequency -- recommended max for 5 min interval is 50, but this will probably run more frequently (once/min?)
	pqmin = int(params['pqmin']) if 'pqmin' in params else 20  # min pq length
	under = float(params['under']) if 'under' in params else -2  # std allowance for dipping below min queue length (-2 = 2% chance)
	over = float(params['over']) if 'over' in params else 1  # std allowance for overflowing lot (1 = 16% chance)
	endpoint = params['endpoint'] if 'endpoint' in params else 'https://woykgpo9zk.execute-api.us-west-2.amazonaws.com/dev/demand/predict'  # prediction endpoint
	api_key = params['apikey'] if 'apikey' in params else 'Yb2NjaFqIw303Ab2XlNfi9oqM2SE9ICA6JtYMjd4'
	print('params:', {'pqlen': pqlen, 'pqtarget': pqtarget, 'vplen': vplen, 'vklen': vklen, 'pkratio': pkratio,
	'complete': complete, 'shorts': shorts, 'pending': pending, 'sla': sla, 'callmax': callmax, 'endpoint': endpoint})  # log params

	# get prediction
	params['window'] = sla  # prediction window
	prediction = get_prediction(endpoint, api_key, params)  # get prediction
	demand, std = (prediction['total_prediction'], prediction['total_std'])
	print('demand:', int(demand), 'std:', int(std))

	# expected pqlen
	expected = pqlen + pending + shorts - demand  # how many taxis will be in PQ
	print('expected: %s = %s + %s + %s - %s' % (int(expected), pqlen, pending, shorts, int(demand)))

	# get number to call
	ncall_over = (pqtarget - expected) - over*std  # number to call to avoid over-supply
	ncall_under = (pqmin - expected) - under*std  # number to call to avoid under-supply
	ncall = max((ncall_over, ncall_under)) / complete  # number to call	
	ncall = 0 if ncall < 0 else callmax if ncall > callmax else int(ncall)  # can't be negative
	print('ncall:', ncall)
	nvk = int(-(-ncall * (1-pkratio) // 1)) if ncall > 1 else 0  # number to call off VK queue
	nvp = ncall - nvk  # number to call off VP queue

	# adjust calls (if too few P or K cabs)
	if vplen < nvp:  # too few P's
		print('vplen < nvp')
		nvp = vplen
		nvk = ncall - vplen
	if vklen < nvk:  # too few K's
		print('vklen < nvk')
		nvk = vklen
		nvp = ncall - vklen
	if vplen + vklen < ncall:  # too few in both queues, call all
		print('vplen + vklen < ncall')
		nvp = vplen
		nvk = vklen
	output = {'vp': nvp, 'vk': nvk}
	print('output:', output)
	return {
		'statusCode': 200,
		'body': json.dumps(output)
	}
