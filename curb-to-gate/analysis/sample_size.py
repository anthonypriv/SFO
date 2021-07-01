# sample size analysis

from postgres import query_postgres


def print_term_trips(print_trips):
	terms = ['ITA', 'ITG', 'T1', 'T2', 'T3']
	terminals = {term: sum([trip['terminal'] == term for client, trip in print_trips.items()]) for term in terms}
	for key, value in terminals.items():
		print('   ', key, value)


# query data from postgres
data = query_postgres('dev', 'client_counts')

# restructure data
trips = {}
for row in data:
	if row['client_id'] not in trips:
		trips[row['client_id']] = {'data': [row]}
	else:
		trips[row['client_id']]['data'].append(row)

# trip data
for client, trip in trips.items():
	# terminal
	terminal_vals = list(set([d['terminal'] for d in trip['data'] if d['terminal'] is not None])) 
	if len(terminal_vals) > 0:
		if terminal_vals[0] in ['T1', 'T2', 'T3', 'ITA', 'ITG']:  # just terminal
			trip['terminal'] = terminal_vals[0]
		elif ('ITM' in terminal_vals) and ('ITA' in terminal_vals):  # international A
			trip['terminal'] = 'ITA'
		elif ('ITM' in terminal_vals) and ('ITA' in terminal_vals):  # international A
			trip['terminal'] = 'ITG'
		else:
			trip['terminal'] = None
	else:
		trip['terminal'] = None

	# door
	doors = [d['door'] for d in trip['data'] if d['door'] is not None]
	trip['door'] = doors[-1] if len(doors) > 0 else None
	trip['door_time'] = [d['event_timestamp'] for d in trip['data'] if d['door'] == trip['door']][0] if trip['door'] is not None else None

	# gate
	gates = [d['gate'] for d in trip['data'] if d['gate'] is not None]
	trip['gate'] = gates[-1] if len(gates) > 0 else None
	trip['gate_time'] = [d['event_timestamp'] for d in trip['data'] if d['gate'] == trip['gate']][0] if trip['gate'] is not None else None

	trip['delta'] = trip['gate_time'] - trip['door_time'] if (trip['door_time'] is not None) and (trip['gate_time'] is not None) else None



# count of total trips
print('total trips:', len(trips))

# trips per terminal
term_trips = {client: trip for client, trip in trips.items() if trip['terminal'] is not None}
print('trips per terminal:', len(term_trips))
print_term_trips(term_trips)

# trips with door (per terminal)
door_trips = {client: trip for client, trip in term_trips.items() if trip['door'] is not None}
print('trips with door:', len(door_trips))
print_term_trips(door_trips)

# trips with gate
gate_trips = {client: trip for client, trip in term_trips.items() if trip['gate'] is not None}
print('trips with gate:', len(gate_trips))
print_term_trips(gate_trips)

# trips with door and gate
door_gate_trips = {client: trip for client, trip in term_trips.items() if (trip['door'] is not None) and (trip['gate'] is not None)}
print('trips with door and gate:', len(door_gate_trips))
print_term_trips(door_gate_trips)

# c2g time filter
c2g_trips = {client: trip for client, trip in door_gate_trips.items() if 60 < trip['delta'].seconds < 14400}
print('trips with valid c2g time:', len(c2g_trips))
print_term_trips(c2g_trips)

# employee filter
