from .Install_If_Necessary import Ask_For_Install

try:
	import base64
except ImportError:
	Ask_For_Install( "pybase64" )
	import base64

try:
	import mysql.connector
except ImportError:
	Ask_For_Install( "mysql-connector-python" )
	import mysql.connector

import numpy as np
import os
import sqlite3
import configparser
from tkinter import messagebox, Tk
def Ask_Yes_Or_No_Popup( title_of_window, message ):
	root = Tk()
	root.withdraw()
	root.lift()
	root.attributes("-topmost", True)
	answer_was_yes = messagebox.askyesno( title_of_window, message )

	return answer_was_yes

class NumpyMySQLConverter(mysql.connector.conversion.MySQLConverter):
    """ A mysql.connector Converter that handles Numpy types """

    def _float32_to_mysql(self, value):
        return float(value)

    def _float64_to_mysql(self, value):
        return float(value)

    def _int32_to_mysql(self, value):
        return int(value)

    def _int64_to_mysql(self, value):
        return int(value)

def Connect_To_SQL( configuration_file_path, config_error_popup=None ):
	if config_error_popup == None:
		config_error_popup = Ask_Yes_Or_No_Popup
	should_open_file = False
	try:
		configuration_file = configparser.ConfigParser()
		configuration_file.read( configuration_file_path )
		db_type = configuration_file['SQL_Server']['database_type']
		db_name = configuration_file['SQL_Server']['database_name']
		if db_type == "QSQLITE":
			sql_conn = sqlite3.connect( db_name )
		elif db_type == "QMYSQL":
			sql_conn = mysql.connector.connect( host=configuration_file['SQL_Server']['host_location'], database=db_name,
								user=configuration_file['SQL_Server']['username'], password=configuration_file['SQL_Server']['password'] )
			sql_conn.set_converter_class( NumpyMySQLConverter )
			sql_conn.ping( True ) # Maintain connection to avoid timing out
		return db_type, sql_conn

	except sqlite3.Error as e:
		should_open_file = config_error_popup( "SQL Connection Error", "There was an issue connecting the SQL server described in the config.ini file\nDo you want to open config.ini?" )
		if should_open_file:
			os.startfile( os.path.abspath(configuration_file_path ) )
		return None, None
	except mysql.connector.Error as e:
		should_open_file = config_error_popup( "SQL Connection Error", "There was an issue connecting the SQL server described in the config.ini file\nDo you want to open config.ini?" )
		if should_open_file:
			os.startfile( os.path.abspath(configuration_file_path ) )
		return None, None
	except Exception as e:
		should_open_file = config_error_popup( "Error In config.ini File", "Error finding: {}\nDo you want to open config.ini?".format( str(e) ) )
		if should_open_file:
			os.startfile( os.path.abspath(configuration_file_path ) )
		return None, None


def Commit_To_SQL( sql_type, sql_conn, sql_table, **commit_things ):
	sql_insert_string = '''INSERT INTO {}({}) VALUES({})'''.format( sql_table, ','.join( commit_things.keys() ), ','.join( ['%s'] * len(commit_things.keys()) ) )
	if sql_type == 'QSQLITE':
		sql_insert_string = sql_insert_string.replace( '''%s''', '?' )

	cur = sql_conn.cursor()
	cur.execute( sql_insert_string, list(commit_things.values()) )
	sql_conn.commit()

def Commit_XY_Data_To_SQL( sql_type, sql_conn, xy_data_sql_table, xy_sql_labels, x_data, y_data, metadata_sql_table, **commit_things ):
	get_measurement_id_string = '''SELECT MAX(measurement_id) FROM {}'''.format( metadata_sql_table )
	meta_data_sql_string = '''INSERT INTO {}(measurement_id,{}) VALUES({})'''.format( metadata_sql_table, ','.join( commit_things.keys() ), ','.join( ['%s'] * (1 + len(commit_things.keys())) ) )
	data_sql_string = '''INSERT INTO {}(measurement_id,{}) VALUES(%s,%s,%s)'''.format( xy_data_sql_table, ','.join( xy_sql_labels ) )
	if sql_type == 'QSQLITE':
		meta_data_sql_string = meta_data_sql_string.replace( '''%s''', '?' )
		data_sql_string = data_sql_string.replace( '''%s''', '?' )

	cur = sql_conn.cursor()
	cur.execute( get_measurement_id_string )
	try:
		measurement_id = int( cur.fetchone()[0] ) + 1
	except Exception:
		measurement_id = 0
	cur.execute( meta_data_sql_string, [measurement_id] + list(commit_things.values()) )
	data_as_tuple = tuple(zip([measurement_id] * len(x_data),(float(x) for x in x_data),(float(y) for y in y_data))) # mysql.connector requires a tuple or list (not generator) and native float type as input
	cur.executemany( data_sql_string, data_as_tuple )
	sql_conn.commit()

def Commit_XY_Blob_Data_To_SQL( sql_type, sql_conn, xy_data_sql_table, xy_sql_labels, x_data, y_data, metadata_sql_table, **commit_things ):
	get_measurement_id_string = '''SELECT MAX(measurement_id) FROM {}'''.format( metadata_sql_table )
	meta_data_sql_string = '''INSERT INTO {}(measurement_id,{}) VALUES({})'''.format( metadata_sql_table, ','.join( commit_things.keys() ), ','.join( ['%s'] * (1 + len(commit_things.keys())) ) )
	data_sql_string = '''INSERT INTO {}(measurement_id,{}) VALUES(%s,%s,%s)'''.format( xy_data_sql_table, ','.join( xy_sql_labels ) )
	if sql_type == 'QSQLITE':
		meta_data_sql_string = meta_data_sql_string.replace( '''%s''', '?' )
		data_sql_string = data_sql_string.replace( '''%s''', '?' )

	cur = sql_conn.cursor()
	cur.execute( get_measurement_id_string )
	try:
		measurement_id = int( cur.fetchone()[0] ) + 1
	except Exception:
		measurement_id = 0
	cur.execute( meta_data_sql_string, [measurement_id] + list(commit_things.values()) )
	x_data_binary = base64.b64encode( x_data.tobytes() )
	y_data_binary = base64.b64encode( y_data.tobytes() )
	cur.execute( data_sql_string, (measurement_id, x_data_binary, y_data_binary) )
	# data_as_tuple = tuple(zip([measurement_id] * len(x_data),(float(x) for x in x_data),(float(y) for y in y_data))) # mysql.connector requires a tuple or list (not generator) and native float type as input
	# cur.executemany( data_sql_string, data_as_tuple )
	sql_conn.commit()


def Read_XY_Blob_Data_From_SQL( sql_type, sql_conn, filter, xy_data_sql_table, xy_sql_labels, metadata_sql_table, metadata_requested=[] ):
	get_metadata_string = f'''SELECT {','.join( ["measurement_id"] + list(metadata_requested) )} FROM {metadata_sql_table} WHERE {filter}'''
	cursor = sql_conn.cursor()
	cursor.execute( get_metadata_string )
	metadata = [list(result) for result in cursor]
	measurement_ids = [str(x[0]) for x in metadata]
	if len(measurement_ids) != 0:
		data_sql_string = f'''SELECT {','.join( ["measurement_id"] + list(xy_sql_labels) )} FROM {xy_data_sql_table} WHERE measurement_id in ({','.join( measurement_ids )})'''
		cursor.execute( data_sql_string )
		deserialize = lambda x : np.frombuffer( base64.b64decode( x ), np.float64 )

		xy_metadata = [(measurement_id, deserialize(x), deserialize(y)) for (measurement_id, x, y) in cursor]
	else:
		xy_metadata = []
	cursor.close()

	return metadata, xy_metadata

#def Create_Table_If_Needed( sql_conn, sql_type ):
#	cur = sql_conn.cursor()
#	try:
#		if sql_type == "QSQLITE":
#			cur.execute("""CREATE TABLE `ftir_measurements` ( `sample_name`	TEXT NOT NULL, `time`	DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, `measurement_id`	TEXT NOT NULL, `temperature_in_k`	REAL, `bias_in_v`	REAL, `user`	TEXT, `detector`	TEXT, `beam_splitter`	TEXT, `start_wave_number`	REAL, `end_wave_number`	REAL, `number_of_scans`	INTEGER, `velocity`	REAL, `aperture`	REAL, `gain`	REAL );""")
#		else:
#			cur.execute("""CREATE TABLE `ftir_measurements` ( `sample_name`	TEXT NOT NULL, `time`	DATETIME NOT NULL, `measurement_id`	TEXT NOT NULL, `temperature_in_k`	REAL, `bias_in_v`	REAL, `user`	TEXT, `detector`	TEXT, `beam_splitter`	TEXT, `start_wave_number`	REAL, `end_wave_number`	REAL, `number_of_scans`	INTEGER, `velocity`	REAL, `aperture`	REAL, `gain`	REAL );""")
#	except (mysql.connector.Error, mysql.connector.Warning) as e:
#		pass
#		#print(e)
#	except:
#		pass # Will cause exception if they already exist, but that's fine since we are just trying to make sure they exist

#	try:
#		cur.execute("""CREATE TABLE `raw_ftir_data` ( `measurement_id` TEXT NOT NULL, `wavenumber` REAL NOT NULL, `intensity` REAL NOT NULL );""")
#	except:
#		pass # Will cause exception if they already exist, but that's fine since we are just trying to make sure they exist

#	cur.close()
#	return False