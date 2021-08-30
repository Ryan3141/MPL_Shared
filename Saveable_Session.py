import configparser

class Saveable_Session:
	def __init__( self, text_boxes ):
		self.text_boxes = text_boxes

	def Save_Session( self, file_path ):
		# Save textbox contents from session
		configuration_file = configparser.ConfigParser()
		configuration_file.read( file_path )
		configuration_file['TextBoxes'] = {}
		for box, name in self.text_boxes:
			configuration_file['TextBoxes'][name] = box.text()
		with open( file_path, 'w' ) as configfile:
			configuration_file.write( configfile )

	def Restore_Session( self, file_path ):
		# Fill in user entry gui from config file entry
		configuration_file = configparser.ConfigParser()
		configuration_file.read( file_path )
		for box, name in self.text_boxes:
			try:
				text = configuration_file['TextBoxes'][name]
				if text:
					box.setText( text )
			except Exception: pass

