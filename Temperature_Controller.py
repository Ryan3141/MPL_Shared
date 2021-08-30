from .Install_If_Necessary import Ask_For_Install
try:
	import serial
except ImportError:
	Ask_For_Install( "PySerial" )
	import serial

import re
import glob
import sys
import configparser
import numpy as np
from time import sleep

from PyQt5 import QtCore

from .Device_Communicator import Device_Communicator

class Current_State:
	def __init__( self ):
		self.pid_is_on = False
		self.set_temperature = 0
		self.pads_selected = (1, 2)
		self.pid_settings = [500.0, 10.0, 0.1] # With 24V supply and still LN2
		# self.pid_settings = [10.0, 2.0, 0.5] # Directly on copper pad
		#self.pid_settings = [20, 2, 0] # On PCB

class Temperature_Controller( QtCore.QObject ):
	"""Interface with serial com port to control temperature"""
	Temperature_Changed = QtCore.pyqtSignal(float)
	Case_Temperature_Changed = QtCore.pyqtSignal(float)
	PID_Output_Changed = QtCore.pyqtSignal(float)
	Setpoint_Changed = QtCore.pyqtSignal(float)
	Device_Connected = QtCore.pyqtSignal(str,str)
	Device_Disconnected = QtCore.pyqtSignal(str,str)
	PID_Coefficients_Changed = QtCore.pyqtSignal(tuple) # Kp, Ki, Kd actually set
	Pads_Selected_Changed = QtCore.pyqtSignal(tuple, bool) # Pads actually connected, were they connected in reverse order
	Pads_Selected_Invalid = QtCore.pyqtSignal()
	Temperature_Stable = QtCore.pyqtSignal()
	Heater_Output_On = QtCore.pyqtSignal()
	Heater_Output_Off = QtCore.pyqtSignal()

	def __init__( self, configuration_file, parent=None, connection_timeout=1000 ):
		super().__init__( parent )

		self.configuration_file = configuration_file
		self.connection_timeout = connection_timeout
		self.triggered_temp_stable_already = False

	def thread_start( self ):
		config = configparser.ConfigParser()
		config.read( self.configuration_file )
		self.status = Current_State()
		success = False
		self.serial_connection = None
		self.identifier_string = config['Temperature_Controller']['Listener_Type']

		try:
			self.device_communicator = Device_Communicator( self, identifier_string=self.identifier_string, listener_address=None,
													port=config['Temperature_Controller']['Listener_Port'] )
			self.device_communicator.Poll_LocalIPs_For_Devices( config['Temperature_Controller']['ip_range'] )
			success = True
			self.device_communicator.Reply_Recieved.connect( lambda message, device : self.ParseMessage( message ) )
			self.device_communicator.Device_Connected.connect( lambda peer_identifier : self.Device_Connected.emit( peer_identifier, "Wifi" ) )
			self.device_communicator.Device_Disconnected.connect( lambda peer_identifier : self.Device_Disconnected.emit( peer_identifier, "Wifi" ) )

			self.device_communicator.Device_Connected.connect( lambda peer_identifier : self.Share_Current_State() )

		except Exception as e:
			print( e )
			self.device_communicator = None

		if( not success ):
			raise Exception( "Issue connecting to wifi with given configuration.ini, please make sure it is connected" )

		self.current_temperature = None
		self.setpoint_temperature = None
		self.partial_serial_message = ""
		self.past_temperatures = []
		self.stable_temperature_sample_count = 20#120#480 # 4 minutes

		# Continuously recheck temperature controller
		self.connection_timeout_timer = QtCore.QTimer( self )
		self.connection_timeout_timer.timeout.connect( self.Update )
		self.connection_timeout_timer.start( self.connection_timeout )



	def Share_Current_State( self ):
		self.Set_Temperature_In_K( self.status.set_temperature )
		self.Set_PID( *self.status.pid_settings )
		self.Set_Active_Pads( *self.status.pads_selected )
		if self.status.pid_is_on:
			self.Turn_On()
		else:
			self.Turn_Off()

	def Set_PID( self, kp, ki, kd ):
		self.status.pid_settings = ( kp, ki, kd )
		message = ("Set PID {} {} {};\n".format( *self.status.pid_settings ) )
		if self.serial_connection is not None:
			self.serial_connection.write( message.encode() )

		self.device_communicator.Send_Command( message )

	def Set_Active_Pads( self, pad1, pad2 ):
		self.status.pads_selected = (pad1, pad2)
		message = ("set pads {} {};\n".format( pad1, pad2 ) )
		if self.serial_connection is not None:
			self.serial_connection.write( message.encode() )

		self.device_communicator.Send_Command( message )

	def Attempt_Serial_Connection( self ):
		for port in GetAvailablePorts():
			try:
				self.serial_connection = serial.Serial(port, 115200, timeout=0)
				self.serial_port = port
				return True
			except Exception:
				pass

		return False

	def Update( self ):
		if( self.device_communicator.No_Devices_Connected() ):
			self.device_communicator.Poll_LocalIPs_For_Devices( '192.168.1-2.2-254' )
			#if not self.serial_connection:
			#	self.Attempt_Serial_Connection()

		if False: #self.serial_connection is not None:
			if not self.device_communicator.No_Devices_Connected():
				self.serial_connection.close()
				self.serial_connection = None
			else:
				try:
					temp = self.serial_connection.readline()
					self.partial_serial_message += temp.decode("utf-8", "ignore")
					split_into_messages = self.partial_serial_message.split( '\n' )
					self.partial_serial_message = split_into_messages[ -1 ]
					for message in split_into_messages[:-1]:
						self.ParseMessage( message )

				except serial.SerialTimeoutException:
					pass
					#print('Data could not be read')
				except serial.serialutil.SerialException:
					self.serial_connection.close()
					self.serial_connection = None

	def Set_Temperature_In_K( self, temperature_in_k ):
		print( "Setting output temperature to " + str(temperature_in_k) )
		self.status.set_temperature = temperature_in_k
		temperature_in_c = temperature_in_k - 273.15
		self.setpoint_temperature = temperature_in_k
		message = ("Set Temp " + str(temperature_in_c) + ";\n")
		if self.serial_connection is not None:
			self.serial_connection.write( message.encode() )

		self.device_communicator.Send_Command( message )
		self.triggered_temp_stable_already = False

	def Turn_On( self ):
		self.status.pid_is_on = True
		print( "Turning heater On" )
		message = ("turn on;\n")
		if self.serial_connection is not None:
			self.serial_connection.write( message.encode() )

		self.device_communicator.Send_Command( message )
		self.triggered_temp_stable_already = False

	def Turn_Off( self ):
		self.status.pid_is_on = False
		print( "Turning heater off" )
		message = ("turn off;\n")
		if self.serial_connection is not None:
			self.serial_connection.write( message.encode() )

		self.device_communicator.Send_Command( message )

	def Get_Temperature_In_K( self ):
		return self.current_temperature

	def ParseMessage( self, message ):
		#print( message )
		pattern_of_a_float = r'[+-]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?'
		debug_pattern = re.compile( r"Temperature setpoint changed to " );

		temperature_pattern = re.compile( '(Cold Junction |Thermocouple )?Temperature = ({})'.format( pattern_of_a_float ) ) # Grab any properly formatted floating point number
		m = temperature_pattern.match( message )
		if( m ):
			if m.group( 1 ) == "Cold Junction ":
				pass
			elif m.group( 1 ) == "Thermocouple ":
				temp = float( m.group( 2 ) )
				if( temp < -273.15 or temp > 1000 ):
					return
				self.Case_Temperature_Changed.emit( temp )
			else: # RTD Sensor
				temp = float( m.group( 2 ) ) + 273.15
				#print( "Reading Temperature = {}".format( temp ) )
				if( temp < 0 or temp > 1000 ):
					return
				self.current_temperature = temp
				self.Temperature_Changed.emit( self.current_temperature )

				if( self.Check_If_Temperature_Is_Stable( self.current_temperature ) and not self.triggered_temp_stable_already ):
					self.triggered_temp_stable_already = True
					print( "Temperature stable around: " + str(self.setpoint_temperature) + '\n' )
					self.Temperature_Stable.emit()

		pid_output_pattern = re.compile( 'PID Output:\s*({})'.format( pattern_of_a_float ) ) # Grab any properly formatted floating point number
		m2 = pid_output_pattern.search( message )
		if( m2 ):
			output_pid = float( m2.group( 1 ) )
			self.PID_Output_Changed.emit( output_pid )

		setpoint_pattern = re.compile( 'Setpoint:\s*({})'.format( pattern_of_a_float ) ) # Grab any properly formatted floating point number
		m3 = setpoint_pattern.search( message )
		if( m3 ):
			setpoint = float( m3.group( 1 ) ) + 273.15
			self.Setpoint_Changed.emit( setpoint )

		pid_coefficients_pattern = re.compile( 'PID coefficients changed to ({})\s+({})\s+({})'.format( *(3 * [pattern_of_a_float]) ) ) # Grab any properly formatted floating point number
		m4 = pid_coefficients_pattern.search( message )
		if( m4 ):
			pid_coefficients = tuple( float( m4.group(i) ) for i in range(1, 4) )
			self.PID_Coefficients_Changed.emit( pid_coefficients )

		pads_selected_pattern = re.compile( 'Pads connected (\d+)\s+(\d+)( reversed)?' ) # Grab any properly formatted floating point number
		m5 = pads_selected_pattern.search( message )
		if( m5 ):
			pads_connected = tuple( int( m5.group(i) ) for i in range(1, 3) )
			if m5.group(3) == " reversed":
				is_reversed = True
			else:
				is_reversed = False
			self.Pads_Selected_Changed.emit( pads_connected, is_reversed )

		if( message.find( "Unable to connect pads" ) != -1 ):
			self.Pads_Selected_Invalid.emit()

		if( debug_pattern.match( message ) ):
			print( message )
		if( message.find( self.identifier_string ) != -1 ):
			self.Device_Connected.emit( str(self.serial_port), "Serial" )

		if( message.find( "Turning output on" ) != -1 ):
			self.Heater_Output_On.emit()
		if( message.find( "Turning output off" ) != -1 ):
			self.Heater_Output_Off.emit()
			self.Setpoint_Changed.emit( 0.0 )
		#else:
		#	print( message )

	def Set_Temp_And_Turn_On( self, temperature_in_k ):
		if temperature_in_k is None:
			return
		self.Set_Temperature_In_K( temperature_in_k )
		self.Turn_On()

	def Check_If_Temperature_Is_Stable( self, new_temperature_in_k ):
		self.past_temperatures.append( new_temperature_in_k )
		if( len(self.past_temperatures) > self.stable_temperature_sample_count ):
			self.past_temperatures = self.past_temperatures[-self.stable_temperature_sample_count:]

		if( len(self.past_temperatures) < self.stable_temperature_sample_count ):
			return False
		error = np.array( self.past_temperatures ) - self.setpoint_temperature
		if np.amax( np.fabs( error ) ) > 1:
			return False
		else:
			return True
#		deviation = np.std( error )
#		average_error = np.mean( error )
#		if( abs(average_error) < .5 and deviation < 0.2 ):
#			return True
#		else:
#			return False

# Function from: https://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python/14224477#14224477
def GetAvailablePorts():
	""" Lists serial port names

		:raises EnvironmentError:
			On unsupported or unknown platforms
		:returns:
			A list of the serial ports available on the system
	"""
	if sys.platform.startswith('win'):
		ports = ['COM%s' % (i + 1) for i in range(256)]
	elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
		# this excludes your current terminal "/dev/tty"
		ports = glob.glob('/dev/tty[A-Za-z]*')
	elif sys.platform.startswith('darwin'):
		ports = glob.glob('/dev/tty.*')
	else:
		raise EnvironmentError('Unsupported platform')

	result = []
	for port in ports:
		try:
			s = serial.Serial(port)
			s.close()
			result.append(port)
		except (OSError, serial.SerialException):
			pass
	return result

