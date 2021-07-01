# lambda function

from get_secret import get_secret
from postgres import query_postgres, batch_insert
from curb_to_gate import get_environ, post_gate, gather_results, bootstrap_results, generate_rows


interval = '-30 day'  # study period
col_name_map = {  # map local columns with postgres schema
	'door': 'door_id',
	'dow': 'day_of_week',
	'hour': 'hour_of_day',
	'gate': 'gate_id',
	'travel': 'travel_time',
	'sample': 'dwell_sample_size',
	'batch': 'batch_timestamp'
}


def lambda_handler(event, context):
	# get environments to query from, insert to
	query_env, insert_env = get_environ(context)
	print('environments:', query_env, insert_env)

	# get db credentials
	query_secret = get_secret(query_env)  # query db credentials
	insert_secret = get_secret(insert_env)  # insert db credentials

	# get security wait (d2p) times
	d2p_query = open('d2p_query.sql').read().replace('INTERVAL', interval)
	trips = query_postgres(query_secret, d2p_query)  # [{trip_id, door, dow, hour, delta, terminal}]
	print('trips:', len(trips))

	# gate walk times
	gate_query = open('gate_query.sql').read()
	gates = query_postgres(query_secret, gate_query)  # [{gate_id, ba, lat, lon}]
	walk_time = post_gate(gates)  # {terminal: {gate_id: walk_time}}

	# gather d2p times
	times = gather_results(trips)  # {terminal: {dow-hour-door: [deltas]}}

	# bootstrap d2p times
	times = bootstrap_results(times)  # {terminal: {dow-hour-door: {travel, sample}}}

	# combine d2p and walk times
	curb2gate = generate_rows(times, walk_time)  # [{door, dow, hour, gate, travel, sample, batch}]

	# insert results to postgres
	batch_insert(insert_secret, curb2gate, 'curb_to_gate_matrix', col_name_map)
