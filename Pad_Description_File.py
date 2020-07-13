import csv


def Get_Device_Description_File( file_path ):
	config_info = {}
	try:
		csvfile = open( file_path )
	except:
		return None
	spamreader = csv.reader( csvfile, delimiter=',' )
	labels = next( spamreader )
	for label in labels:
		config_info[ label ] = []

	for row in spamreader:
		for label, datum in zip( labels, row ):
			config_info[label].append( datum )

	expected_data = ["Negative Pad","Positive Pad","Device Area (um^2)","Device Perimeter (um)","Device Location"]
	if not set( expected_data ) <= set( config_info.keys() ): # If all the right keys are in the file
		print( "Description file must have all of: {}".format( ','.join(expected_data) ) )
		return None

	return config_info
