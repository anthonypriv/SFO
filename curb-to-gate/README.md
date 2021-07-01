# curb-to-gate

Curb to gate travel time for UC-04.

	.
	|-- analysis                                 # analysis of results
	|	|-- results_validation.py                # generate c2g time figures for latest data
	|-- lambdas                                  # lambda function(s)
	|	|-- curbToGate                           # calculates curb to gate times


## Data Service Scope

- read data from pwifi database
- transform/process to curb-->gate times
- handoff result to postgres table
- API's/web services can deal with the rest


## Requirements

- travel time for door-gate pair on day of week, hour of day for last 30 days (estimation) - last **d** days
- exclude non-passengers
- journey must start at door, end at gate
- estimated travel time is median
- calculated every **n** hours
- store output in postgres table
- calendar day should be 3am - 3am to include late flights


## Query

convert to local timestamp
```sql
select client_id, ap_id, event_timestamp at time zone 'utc' at time zone 'america/los_angeles' as et_local
from client_association
where event_timestamp > current_timestamp + interval '-30 days'
and ap_id != -1
```

redefine calendar day as 3am-3am to keep late night sessions intact
```sql
select client_id, ap_id, et_local, case when date_part('hour', et_local) <= 2 then et_local::date - interval '1 day' else et_local::date end as date
from local_timestamp
```

for each day, for each client, for each ap visited, get first and last timestamp associated with ap and assign id to each trip
```sql
select client_id, ap_id, min(et_local), max(et_local), dense_rank() over (order by client_id, date) as trip_id
from calendar_day
group by client_id, ap_id, date
```

join doors and gates to trips
```sql
select C.trip_id, C.client_id, C.min, C.max, doors.door_number as door, gates.gate_display_name as gate, gates.terminal
from C
left join vw_ap_doors as doors on doors.ap_id = C.ap_id
left join vw_ap_gates as gates on gates.ap_id = C.ap_id
```

get the first time at the first door for each trip
```sql
select first_door.trip_id, first_door.door_time, trips.client_id, trips.door
from (  -- first door time for each trip
	select trip_id, min(min) as door_time
	from trips
	where door is not null
	group by trip_id
) as first_door
inner join trips on trips.trip_id = first_door.trip_id and trips.min = first_door.door_time
```

get the first time at the last gate for each trip
```sql
select last_gate.trip_id, trips.min as gate_time, trips.client_id, trips.gate, trips.terminal
from (  -- last gate tiem for each trip
	select trip_id, max(max) as max_gate_time
	from trips
	where gate is not null
	group by trip_id
) as last_gate
inner join trips on trips.trip_id = last_gate.trip_id and trips.max = last_gate.max_gate_time
```

combine door and gate times to get result: one row per trip-door-gate combination
```sql
select
	doors.trip_id,
	doors.client_id,
	gates.terminal as terminal,
	doors.door,
	gates.gate,
	extract(epoch from gates.gate_time - doors.door_time) as delta,
	extract(dow from doors.door_time) as dow,
	extract(hour from doors.door_time) as hour
from doors
left join gates on gates.trip_id = doors.trip_id
where doors.door is not null  -- trip must have door
and gates.gate is not null  -- trip must have gate
and extract(epoch from gates.gate_time - doors.door_time) between 60 and 14400;  -- curb to gate between 1 min and 4 hours
```

query output:

	trip_id            int        id for trip
	client_id          int        id for client
	terminal           str        terminal code
	door               int        door number
	gate               str        gate display name
	delta              int        curb to gate time (seconds)
	dow                int        day of week (0 = Sunday)
	hour               int        hour of day (0-23)


## curbToGate lambda

query database (takes around 5 min for full 30 days of data)
```python
def get_trips(environ, query_name):
	# get data from postgres
	data, col_names = query_postgres(environ, query_name)
	print('col names:', col_names)

	# transform to list of dicts
	trips = [{col: val for col, val in zip(col_names, r)} for r in data]

	# get client ids
	clients = list(set([r['client_id'] for r in trips]))
	return clients, trips
```

filter out suspected employee trips (client with > 4 trips)
```python
def filter_trips(clients, trips, f=4):
	# filter out employee trips

	# get trips for each client
	client_trips = {client: [] for client in clients}
	for trip in trips:
		client_trips[trip['client_id']].append(trip)

	# filter client trips to filt trips
	filt_trips = []
	for client, ctrips in client_trips.items():
		trip_ids = set([trip['trip_id'] for trip in ctrips])  # number of trips (not number of rows)
		if len(trip_ids) <= f:  # employee filter
			filt_trips.extend(ctrips)
	return filt_trips
```

aggregate curb to gate times
curb to gate time is **median** of all curb to gate times in a terminal-gate-door-dow-hour category
additional metrics are found: sample size, standard deviation, 1st quartile, 3rd quartile
```python
def curb_to_gate(trips):
	# gather results
	curb2gate = {}  # {terminal-door-gate-dow-hour: [times]}
	for trip in trips:
		key = '%s %s %s %s %s' % (trip['terminal'], trip['door'], trip['gate'], trip['dow'], trip['hour'])
		if key in curb2gate:
			curb2gate[key].append(trip['delta'])
		else:
			curb2gate[key] = [trip['delta']]

	# aggregate curb2gate times
	curb2gate_rows = [key.split() + [quartile(values,.5)/60, len(values), std(values)/60, quartile(values,.25)/60, quartile(values,.75)/60] for key, values in curb2gate.items()]
	return curb2gate_rows
```

batch insert records to postgres
```python
def batch_insert(environ, records, table_name, col_names):
	# batch insert records to table
	# records is list of dicts
	conn = connect(environ)
	cursor = conn.cursor()
	f = StringIO()  # bytestring to insert
	for record in records:
		vals = []
		for value, typ in zip(record, col_names.values()):  # fix data type
			if typ == 'int':
				vals.append(str(int(float(value))))
			else:
				vals.append(str(value))
		line = ','.join(vals) + '\n'
		f.write(line)
	f.seek(0)  # ?
	cols = list(col_names.keys())  # column names
	cursor.copy_from(f, table_name, sep=',', columns=col_names)
	f.close()
	conn.commit()  # commit changes to database
	conn.close()
	print('inserted %s rows to %s' % (len(records), table_name))
```

*Note:* Library for interacting with postgres, **psycopg2** must be downloaded from https://github.com/jkehler/awslambda-psycopg2 to be compatable with lambda.


## Output

	curb_to_gate_matrix table:
	curb_to_gate_matrix_id        int          primary key (sequence)
	terminal_code                 str          terminal
	door_number                   int          door
	gate_display_name             str          gate
	day_of_week                   int          day of week
	hour_of_day                   int          hour of day
	travel_time                   float        fast curb to gate time (10th percentile)
	dwell_time                    float        mean curb to gate time (dwell time)
	confidence_interval           float        dwell time confidence interval  -- remove
	dwell_sample_size             int          sample size
	travel_sample_size            int          number of samples that fall under 10th percentile  -- remove
	batch_timestamp               datetime     time of record generation
	inserted_at                   datetime     time of insert
