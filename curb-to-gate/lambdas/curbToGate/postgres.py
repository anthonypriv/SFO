# postgres functions

import psycopg2
import time
from io import StringIO


def connect(creds):
	# open database connection -- creds = db credentials (from secret)
	conn = psycopg2.connect('dbname=%s user=%s host=%s password=%s' % (creds['dbname'], creds['username'], creds['host'], creds['password']))
	print('connected to %s - %s' % (creds['dbname'], creds['username']))
	return conn


def query_postgres(creds, query):
	# execute query in postgres
	conn = connect(creds)
	cursor = conn.cursor()
	t = time.time()  # time query
	cursor.execute(query)  # execute query
	print('query time:', int(time.time() - t))
	rows = cursor.fetchall()  # query result
	col_names = [d[0] for d in cursor.description]  # column names
	conn.close()
	data = [{col: val for col, val in zip(col_names, r)} for r in rows]  # list of dicts
	return data


def batch_insert(creds, records, table_name, col_map):
	# batch insert records to table
	f = StringIO()
	for record in records:
		line = ','.join([str(record[key]) for key in col_map]) + '\n'  # get values in correct column order
		f.write(line)
	f.seek(0)  # not really sure what this does
	cols = [value for key, value in col_map.items()]  # postgres column names

	conn = connect(creds)
	cursor = conn.cursor()
	cursor.copy_from(f, table_name, sep=',', columns=cols)
	f.close()
	conn.commit()  # commit database changes
	conn.close()
	print('inserted %s rows to %s (%s)' % (len(records), table_name, creds['dbname']))
