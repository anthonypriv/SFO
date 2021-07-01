# client trips

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from postgres import query_postgres


data = query_postgres('dev', 'client_trips')

# group by client id
trip_data = {}
for row in data:
	if row['client_id'] not in trip_data:
		trip_data[row['client_id']] = [row]
	else:
		trip_data[row['client_id']].append(row)
print('trip data', len(trip_data))

# get trip attributes
p1 = 0
p2 = 0
p3 = 0
trips = {}
for client, tdata in trip_data.items():
	doors = [d['door'] for d in tdata if d['door'] is not None]
	gates = [d['gate'] for d in tdata if d['gate'] is not None]
	if (len(doors) > 0) and (len(gates) > 0):
		p1 += 1
		door = doors[0]
		door_terminal = [d['door_terminal'] for d in tdata if d['door'] == door][0]
		door_time = [d['event_timestamp'] for d in tdata if d['door'] == door][0]
		gate = gates[-1]
		gate_time = [d['event_timestamp'] for d in tdata if d['gate'] == gate][0]
		delta = (gate_time - door_time).seconds
		gate_terminal = [d['gate_terminal'] for d in tdata if d['gate'] == gate][0]
		if (gate_terminal in ['T2', 'T3']) and (door_terminal == gate_terminal):
			p2 += 1
			if delta > 60:
				p3 += 1
				trips[client] = {
					'door': door,
					'gate': gate,
					'terminal': gate_terminal,
					'delta': delta,
					'rows': [{
						'client_id': client,
						'time': d['event_timestamp'],
						'lat': d['latitude'],
						'lon': d['longitude'],
						'terminal': gate_terminal,
						'door': door,
						'gate': gate,
						'ap_id': d['ap_id'],
						'client_mac': d['client_mac'],
						'c2g': delta,
						'ap_mac': d['nyansa_mac']}
						for d in tdata if door_time <= d['event_timestamp'] <= gate_time]
				}
print('passed', p1, p2, p3)

# terminal-gate trips
trip_sort = {'T2': {}, 'T3': {}}
for client, trip in trips.items():
	if trip['gate'] not in trip_sort[trip['terminal']]:
		trip_sort[trip['terminal']][trip['gate']] = [trip]
	else:
		trip_sort[trip['terminal']][trip['gate']].append(trip)

# get samples
samples = {'T2': [], 'T3': []}
for terminal, term_values in trip_sort.items():
	for gate, values in term_values.items():
		perc = np.percentile([trip['delta'] for trip in values], 10)
		samples[terminal].extend([trip for trip in values if trip['delta'] <= perc])
print('t2 samples', len(samples['T2']))
print('t3 samples', len(samples['T3']))

# n trips for each terminal
n = 10
t2_trips = np.random.choice(samples['T2'], n, replace=False)
t3_trips = np.random.choice(samples['T3'], n, replace=False)
all_trips = list(t2_trips) + list(t3_trips)

# compile rows
rows = []
for trip in all_trips:
	rows.extend(trip['rows'])

# write to csv
df = pd.DataFrame(rows)
df.to_csv('data/client_trips.csv', index=False)

# test plot
plt.figure(figsize=(8,7))
plt.title('Curb to Gate Trips', fontsize=16)
for trip in all_trips:
	plt.plot([t['lon'] for t in trip['rows']], [t['lat'] for t in trip['rows']], label=trip['gate'])
plt.legend()
plt.tight_layout()
plt.savefig('figures/c2g_trips.png')
