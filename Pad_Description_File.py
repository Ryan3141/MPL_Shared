import csv
from collections import namedtuple

def Get_Device_Description_File( file_path ):
	config_info = {}
	csvfile = open( file_path )
	spamreader = csv.reader( csvfile, delimiter=',' )
	headers = next( spamreader )

	"sample_name", "user", "temperature_in_k", "device_side_length_in_um", "device_location", "measurement_setup"
	expected_headers = ["Negative Pad","Positive Pad","Device Side Length (um)","Device Location"]
	shortened_names  = ["neg_pad", "pos_pad", "side", "location"]
	Device_Info = namedtuple('Device_Info', shortened_names)
	# if not set( expected_data ) <= set( config_info.keys() ): # If all the right keys are in the file
	# 	print( "Description file must have all of: {}".format( ','.join(expected_data) ) )
	# 	return None
	if len( [header for header in expected_headers if header not in headers] ) > 0:
		raise Exception( f"Description file must have header: {','.join(expected_headers)}" )

	config_info = [Device_Info(*row) for row in spamreader]

	return config_info
