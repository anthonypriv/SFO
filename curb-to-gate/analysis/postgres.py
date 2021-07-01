import psycopg2
from time import time
from io import StringIO
import postgres_config as config


def connect(environ):
	db = config.dev if environ == 'dev' else config.tqa if environ == 'tqa' else None  # choose environment
	conn = psycopg2.connect('dbname=%s user=%s host=%s password=%s' % (db['dbname'], db['user'], db['host'], db['password']))
	print('connected to', db['user'])
	return conn


def query_postgres(environ, query):
	"""Query postgres database """
	conn = connect(environ)  # connect to database
	cursor = conn.cursor()  # get cursor
	t = time()  # query start time
	cursor.execute(query)  # execute query
	print('query time:', int(time() - t))  # query run time
	rows = cursor.fetchall()  # fetch rows of data
	col_names = [desc[0] for desc in cursor.description]
	conn.close()  # close connection
	data = [{col: val for col, val in zip(col_names, r)} for r in rows]  # list of dicts
	return data


def batch_insert(environ, records, table_name, col_names):
	# batch insert records to table
	# records is list of lists
	conn = connect(environ)
	cursor = conn.cursor()
	f = StringIO()  # bytestring to insert
	for record in records:
		vals = []
		for value, typ in zip(record, col_names.values()):  # fix data type
			vals.append(str(int(float(value)))) if typ == 'int' else vals.append(str(value))  # int correction
		line = ','.join(vals) + '\n'
		f.write(line)
	f.seek(0)  # ?
	cols = list(col_names.keys())  # column names
	cursor.copy_from(f, table_name, sep=',', columns=col_names)
	f.close()
	conn.commit()  # commit changes to database
	conn.close()
	print('inserted %s rows to %s' % (len(records), table_name))
