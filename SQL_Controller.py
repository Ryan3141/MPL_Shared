from .Install_If_Necessary import Ask_For_Install

try:
	import mysql.connector
except:
	Ask_For_Install( "mysql-connector-python" )
	import mysql.connector

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

def Connect_To_SQL( configuration_file_path ):
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
			sql_conn.ping( True ) # Maintain connection to avoid timing out
		return db_type, sql_conn

	except sqlite3.Error as e:
		should_open_file = Ask_Yes_Or_No_Popup( "SQL Connection Error, Open config.ini?", "There was an issue connecting the SQL server described in the config.ini file" )
		if should_open_file:
			os.startfile( os.path.abspath(configuration_file_path ) )
		return None, None
	except mysql.connector.Error as e:
		should_open_file = Ask_Yes_Or_No_Popup( "SQL Connection Error, Open config.ini?", "There was an issue connecting the SQL server described in the config.ini file" )
		if should_open_file:
			os.startfile( os.path.abspath(configuration_file_path ) )
		return None, None
	except Exception as e:
		should_open_file = Ask_Yes_Or_No_Popup( "Error In config.ini File, Open It?", "Error finding: " + str(e) )
		if should_open_file:
			os.startfile( os.path.abspath(configuration_file_path ) )


def Commit_To_SQL( sql_type, sql_conn, sql_table, **commit_things ):
	sql_insert_string = '''INSERT INTO {}({}) VALUES({})'''.format( sql_table, ','.join( commit_things.keys() ), ','.join( ['%s'] * len(commit_things.keys()) ) )
	if sql_type == 'QSQLITE':
		sql_insert_string.replace( '%s', '?' )

	cur = sql_conn.cursor()
	cur.execute( sql_insert_string, list(commit_things.values()) )
	sql_conn.commit()

def Commit_XY_Data_To_SQL( sql_type, sql_conn, xy_data_sql_table, xy_sql_labels, x_data, y_data, metadata_sql_table, **commit_things ):
	get_measurement_id_string = '''SELECT MAX(measurement_id) FROM {}'''.format( metadata_sql_table )
	meta_data_sql_string = '''INSERT INTO {}(measurement_id,{}) VALUES({})'''.format( metadata_sql_table, ','.join( commit_things.keys() ), ','.join( ['%s'] * (1 + len(commit_things.keys())) ) )
	data_sql_string = '''INSERT INTO {}(measurement_id,{}) VALUES(%s,%s,%s)'''.format( xy_data_sql_table, ','.join( xy_sql_labels ) )
	if sql_type == 'QSQLITE':
		sql_insert_string.replace( '%s', '?' )

	cur = sql_conn.cursor()
	cur.execute( get_measurement_id_string )
	measurement_id = int( cur.fetchone()[0] ) + 1
	cur.execute( meta_data_sql_string, [measurement_id] + list(commit_things.values()) )
	data_as_tuple = tuple(zip([measurement_id] * len(x_data),(float(x) for x in x_data),(float(y) for y in y_data))) # mysql.connector requires a tuple or list (not generator) and native float type as input
	cur.executemany( data_sql_string, data_as_tuple )
	sql_conn.commit()

