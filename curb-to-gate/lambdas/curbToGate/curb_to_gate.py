# curb to gate functions

import datetime
from c2g_math import mean, median, bootstrap, haversine
import json


ba_term_map = {  # map boarding areas to terminals
	'A': 'ITA',
	'B': 'T1',
	'C': 'T1',
	'D': 'T2',
	'E': 'T3',
	'F': 'T3',
	'G': 'ITG'
}


def get_environ(context):
	# get environment name from context object (from alias name)
	# return query environment, insert environment
	arn = context.invoked_function_arn.split(':')
	if arn[-1] in ['dev', 'tqa', 'stg']:  # dev, tqa, stg
		return 'dev', arn[-1]
	elif arn[-1] == 'prd':  # prod
		return 'prd', 'prd'
	else:
		return 'dev', 'dev'  # other ($LATEST)


def post_gate(gate_info, walk=1.3, m=1.15):
	# get security to gate walking times
	# gate_info = [{gate_id, ba (boarding area), lat, lon}]
	# walk = average walking speed (m/s)
	# m = multiplier to walk times
	# return {terminal: {gate: walk_time}}
	checkpoints = json.loads(open('security.json').read())  # location of security checkpoints for each boarding area
	output = {}
	for gate in gate_info:
		ba = gate['ba']
		if ba in checkpoints:
			term = ba_term_map[ba]  # terminal
			if term not in output:
				output[term] = {}
			gate_loc = (gate['lat'], gate['lon'])  # gate lat, lon
			checkpoint_loc = (checkpoints[ba]['lat'], checkpoints[ba]['lon'])  # checkpoing lat, lon
			dist = haversine(gate_loc, checkpoint_loc)  # haversine distance between gate, checkpoint (straight line)
			output[term][gate['gate_id']] = dist / walk * m
	return  output


def gather_results(trips):
	# group trips by bin
	# return {terminal: {door-dow-hour: [deltas]}}
	output = {}
	for trip in trips:
		term = trip['terminal']
		if term not in output:
			output[term] = {}
		key = '%s %s %s' % (trip['door'], trip['dow'], trip['hour'])
		if key not in output[term]:
			output[term][key] = []
		output[term][key].append(trip['delta'])
	return output


def bootstrap_results(times):
	# get bootstrapped median, sample size from each bin
	# return {terminal: {door-dow-hour: {travel, sample}}}
	for term, values in times.items():
		for key, deltas in values.items():
			times[term][key] = {'travel': bootstrap(deltas), 'sample': len(deltas)}
	return times


def generate_rows(d2p, p2g):
	# generate rows based on bootstrapped data
	# return [{door, dow, hour, travel, sample, batch}]
	now = str(datetime.datetime.utcnow())  # batch timestamp
	output = []
	for term, data in d2p.items():  # door to post
		for key, value in data.items():
			k = key.split()
			for gate, walk in p2g[term].items():  # gate walk data
				output.append({
					'door': int(float(k[0])),
					'dow': int(float(k[1])),
					'hour': int(float(k[2])),
					'gate': gate,
					'travel': (value['travel'] + walk) / 60,  # travel time
					'sample': value['sample'],
					'batch': now
				})
	return output
