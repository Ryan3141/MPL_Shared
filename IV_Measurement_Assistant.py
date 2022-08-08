# from .Install_If_Necessary import Ask_For_Install
try:
	import pyvisa as visa
except ImportError:
	# Ask_For_Install( "PyVisa" )
	import pyvisa as visa
import matplotlib.pyplot as plt
import numpy as np
import time
import csv
from PyQt5 import QtCore


class IV_Controller( QtCore.QObject ):
	newSweepStarted_signal = QtCore.pyqtSignal()
	dataPointGotten_signal = QtCore.pyqtSignal(float, float) # Voltage (in V), Current (in A)
	sweepFinished_signal = QtCore.pyqtSignal(np.ndarray, np.ndarray) # Voltages (in V), Currents (in A)
	noiseMeasurementFinished_signal = QtCore.pyqtSignal(np.ndarray) # Currents (in A)

	Device_Connected = QtCore.pyqtSignal(str,str)
	Device_Disconnected = QtCore.pyqtSignal(str,str)
	Bias_Is_Set = QtCore.pyqtSignal( float, float ) # args: Voltage set (in V), Current (in A)

	Error_signal = QtCore.pyqtSignal( str )

	def __init__( self, parent=None, machine_type="Keithley" ):
		super(IV_Controller, self).__init__(parent)
		self.machine_type = machine_type
		self.gpib_resource = None
		self.stop_measurement_early = False

	def thread_start( self ):
		self.Initialize_Connection()

	def thread_stop( self ):
		self.Close_Connection()

	def Make_Safe( self ):
		self.Turn_Off_Bias()

	def Check_Connection_Then_Run( self, func ):
		def newfunc( *args, **kargs ):
			if self.gpib_resource == None:
				print( func )
				self.Error_signal.emit( "IV controller not connected" )
				return
			try:
				return func( *args, **kargs )
			except Exception as e:
				self.Device_Disconnected.emit( self.machine_type, self.supported_devices[ self.machine_type ][0] )
				print( func )
				self.Error_signal.emit( f"IV controller not connected {str(e)}" )
				return

		newfunc.func = func
		return newfunc

	def Initialize_Connection( self ):
		if self.gpib_resource != None:
			self.gpib_resource.close()
			self.gpib_resource = None
		#print( rm.list_resources() + "\n" ) # List available machines to connect to

		# whats_available = rm.list_resources()
		self.supported_devices = { "Keysight" : ( 'GPIB::23::INSTR', (self.Voltage_Sweep_Keysight, self.Set_Bias_Keysight, self.Turn_Off_Bias_Keysight) ), # Keysight B2962A's address on GPIB connection with IEEE-446 protocol
								   "Keithley" : ( 'GPIB::26::INSTR', (self.Voltage_Sweep_Keithley, self.Set_Bias_Keithley, self.Turn_Off_Bias_Keithley) ) } # Keithley 236's address on GPIB connection with IEEE-446 protocol

		try:
			lambda *args, **kargs : self.Check_Connection()
			address = self.supported_devices[ self.machine_type ][0]
			self._Voltage_Sweep, self._Set_Bias, self._Turn_Off_Bias = ( self.Check_Connection_Then_Run(x) for x in self.supported_devices[ self.machine_type ][1] )
			self.resource_manager = visa.ResourceManager()
			self.gpib_resource = self.resource_manager.open_resource(address)
			self.gpib_resource.clear()
			self.Device_Connected.emit( self.machine_type, self.supported_devices[ self.machine_type ][0] )
			self.is_connected = True
			return self.gpib_resource
		except Exception:
			self.is_connected = False

		self.debug = 1
		return None


	def Close_Connection( self ):
		if self.gpib_resource == None:
			return
		self.gpib_resource.close()
		self.gpib_resource = None

		self.Device_Disconnected.emit( self.machine_type, self.supported_devices[ self.machine_type ][0] )


	def Set_Bias( self, bias_V ):
		self._Set_Bias( bias_V )

	def Turn_Off_Bias( self ):
		self._Turn_Off_Bias()

	def Voltage_Sweep( self, input_start, input_end, input_step, time_interval ):
		self._Voltage_Sweep( input_start, input_end, input_step, time_interval )

	def _Set_Bias( self, bias_V ):
		pass

	def _Turn_Off_Bias( self ):
		print( "Running Default Turn_Off_Bias" )
		pass

	def _Voltage_Sweep( self, input_start, input_end, input_step, time_interval ):
		x_values = np.arange( input_start, input_end + input_step / 2, input_step )
		self.newSweepStarted_signal.emit()
		time.sleep( 0.1 )
		y_values = np.array( [x * 100E-3 * self.debug for x in x_values] )
		for x, y in zip(x_values, y_values):
			self.dataPointGotten_signal.emit( x, y )
			time.sleep( 0.01 )
		self.sweepFinished_signal.emit( x_values, y_values )
		self.debug += 1
		return

	def Set_Bias_Keithley( self, bias_V ):
		K = self.gpib_resource
		compliance_A = 25E-3 # Amps
		range = 0 # auto
		delay = 1 # in milliseconds
		K.write( "F0,1X" ) # Source voltage (0), and measure dc current (0), then sweep (1) not dc (0)
		K.write( f"B{bias_V},{range},{delay}X" )

		# K.write( "T4,0,0,0X" ) # Set triggering after H0X command and continue immediately
		# K.write( "R1X" ) # Enable Triggers

		K.write( "N1X" ) # Set machine to active mode
		# K.write( "H0X" ) # Send immediate trigger
		K.timeout = 20 * 1000 # Timeout in milliseconds

		K.write( "G4,2,1X" ) # Set reading format to read raw results one by one
		try:
			current = float( K.read() )
			print( f"Bias = {bias_V} V" )
			print( f"current = {current} A" )
			self.Bias_Is_Set.emit( bias_V, current )
		except visa.errors.VisaIOError as e:
			print( f"Failed to set Bias: {str(e)}" )

	def Turn_Off_Bias_Keithley( self ):
		K = self.gpib_resource
		K.write( "N0X" ) # Return machine to standby

	def Voltage_Sweep_Keithley( self, input_start, input_end, input_step, time_interval ):
		time.sleep( 2 ) # Sleep to make sure heater has time to turn off
		Keithley = self.gpib_resource
		self.newSweepStarted_signal.emit()
		Keithley.write( "J0X" ) # Reset everything to known good state (factory defaults)
		Keithley.write( "F0,1X" ) # Source voltage (0), and measure dc current (0), then sweep (1) not dc (0)

		Keithley.write( "P5X" ) # Take 2^5 = 32 readings each measurement
		Keithley.write( "O1X" ) # Change to remote sensing (4 point probe) O1 or 2 point probe O0
		Keithley.write( "L25E-3,0X" ) # Set compliance to 25 mA, range (0 for autorange)
		Keithley.write( "S2X" ) # Integration time = 16.67 msec (for 60Hz power line)
		Keithley.write( "R0X" ) # Disable Triggers
		Keithley.write( "T4,0,0,0X" ) # Set triggering after H0X command and continue immediately
		Keithley.write( "R1X" ) # Enable Triggers

		initial_delay_ms = 200
		delay_ms = time_interval * 1E3
		v_range = 0
		# Keithley.write( f"Q0,{input_start},{v_range},{initial_delay_ms},1X" ) # Hold first voltage for 1 count
		Keithley.write( f"Q1,{input_start},{input_end},{input_step},{v_range},{delay_ms}X" ) # Linear stair step voltage (1), start, stop, step, range (1 for 1V range, 0 for autorange), delay
		# Keithley.write( f"Q0,{input_end},{v_range},{initial_delay_ms},1X" ) # Hold first voltage for 1 count

		#timestr = time.strftime("%Y%m%d-%H%M%S")

		Keithley.write( "N1X" ) # Set machine to active mode
		Keithley.write( "H0X" ) # Send immediate trigger
		Keithley.write( "G4,2,1X" ) # Set reading format to read raw results one by one
		results = []
		x_values = np.arange( int(input_start * 1E9), int(input_end * 1E9) + 1, int(input_step * 1E9) ) / 1E9
		for index, x in enumerate(x_values):
			data = Keithley.read()
			#print( data )
			results.append( float(data) )
			self.dataPointGotten_signal.emit( x, float(data) )
			if index % 10 == 0:
				QtCore.QCoreApplication.processEvents()
				if self.stop_measurement_early == True:
					self.stop_measurement_early = False
					break

		Keithley.write( "N0X" ) # Return machine to standby

		#Keithley.write( "B0.1,0,200X" ) # Set bias to 0.1 V, autorange the bias range, delay in milliseconds

		#Keithley.write( "G4,2,2X" ) # Set the read to just spit out the raw current values (in A) when we call read, final 2 means give all lines of sweep data per talk
		#results = Keithley.read()
		Keithley.timeout = 10 * 120000 # The measurement may take up to 1200 seconds
		try:
			results = Keithley.query_ascii_values('G4,2,2X', container=np.array)
		except visa.errors.VisaIOError as e:
			print( "Failed to measure before timeout" )
			results = []
		if len(x_values) != len(results):
			print( f"Error len(x_values)={len(x_values)} and len(results)={len(results)}" )
		else:
			self.sweepFinished_signal.emit( x_values, np.array(results) )

	def Set_Bias_Keysight( self, bias_V ):
		K = self.gpib_resource
		channel = 1 # or 2
		compliance_A = 2E-3 # Amps
		K.write(f":SOUR{channel}:FUNC:MODE VOLT") # Source voltage (VOLT) not current (CURR)
		K.write(f":SOUR{channel}:VOLT {bias_V}") # Set amount
		K.write(f":SENS{channel}:REM ON") # Enable remote sense (4-wire)

		K.write(f":SENS{channel}:CURR:PROT {compliance_A}")  # Set compliance current
		K.write(f":OUTP{channel} ON")  # Enable channel
		try:
			current = K.query_ascii_values(':MEAS:CURR?', container=np.array) # Read current values
			print( f"Bias = {bias_V} V" )
			print( f"current = {current} A" )
			if len(current) > 0:
				self.Bias_Is_Set.emit( bias_V, current[0] )
		except visa.errors.VisaIOError as e:
			print( "Failed to measure bias" )

	def Turn_Off_Bias_Keysight( self ):
		K = self.gpib_resource
		channel = 1 # or 2
		K.write(f":OUTP{channel} OFF")  # Enable channel

	def Voltage_Sweep_Keysight( self, input_start, input_end, input_step, delay_after_source ):
		K = self.gpib_resource

		K.write("*RST") # Reset everything to known good state (factory defaults)
		time.sleep( 2 ) # Sleep to make sure heater has time to turn off
		K.write(":SYST:LFR 60") # Set powerline cycle to 60 Hz
		self.newSweepStarted_signal.emit()

		# compliances = [1E-8, 1E-5, 1E-2]
		compliances = [1E-8, 1E-7, 1E-6, 1E-5, 1E-4, 1E-3, 1E-2]
		channel = 1 # or 2
		delay_to_source_start = 0.001 # Seconds
		number_of_powerline_cycles = 1
		voltages = np.arange( int(input_start * 1E9), int(input_end * 1E9) + 1, int(input_step * 1E9) ) / 1E9

		left = np.arange( int(-2.0 * 1E9), int(-0.1 * 1E9) + 1, int(0.05 * 1E9) ) / 1E9
		middle = np.arange( int(-0.1 * 1E9), int(0.1 * 1E9) + 1, int(0.001 * 1E9) ) / 1E9
		right = np.arange( int(0.1 * 1E9), int( 2.0 * 1E9) + 1, int(0.05 * 1E9) ) / 1E9
		voltages = np.concatenate( (left, middle, right), axis=0 )
		# print( voltages )
		# voltages = np.linspace( 0.0, 1.0, 5 )
		results_by_compliance = []
		for compliance_A in compliances:
			### For voltage sweep ###
			K.write(f":SOUR{channel}:FUNC:MODE VOLT") # Source voltage (VOLT) not current (CURR)
			K.write(f":SOUR{channel}:VOLT:MODE LIST") # We will run a list of voltages
			K.write(f":SOUR{channel}:VOLT:RANG:AUTO ON") # Automatically set range
			K.write(f":SOUR{channel}:LIST:VOLT {','.join( map(str,voltages) )}") # List out the voltages in volts
			# K.write(f":SOUR{channel}:LIST:STAR 0") # Start with list index 0
			K.write(f":SENS{channel}:FUNC CURR")  # Set to measure current
			K.write(f":SENS{channel}:CURR:PROT {compliance_A}")  # Set compliance current
			### For current sweep ###
	#		K.write(f":SOUR{channel}:FUNC:MODE CURR") # Source voltage (VOLT) or current (CURR)
	#		# K.write(f":SOUR{channel}:CURR:MODE LIST") # We will run a list of voltages
	#		# K.write(f":SOUR{channel}:LIST:CURR {','.join( map(str,voltages) )}") # List out the voltages in volts (or currents in Amps)
	#		# # K.write(f":SOUR{channel}:LIST:STAR 0") # Start with list index 0
	#
	#		### Try as sweep rather than list
	#		K.write(f":SOUR{channel}:CURR:MODE SWE")
	#		K.write(f":SOUR{channel}:CURR:STAR {input_start}")
	#		K.write(f":SOUR{channel}:CURR:STOP {input_end}")
	#		K.write(f":SOUR{channel}:CURR:POIN {len(voltages)}")
	#		K.write(f":SENS{channel}:FUNC VOLT")  # Set to measure current
	#		K.write(f":SENS{channel}:VOLT:PROT {compliance_A}")  # Set compliance current


			K.write(f":SENS{channel}:CURR:NPLC {number_of_powerline_cycles}")
			# measurement_period = 5E-5 # in seconds
			# K.write(f":SENS{channel}:CURR:APER {measurement_period}")
			K.write(f":SENS{channel}:REM ON") # Enable remote sense (4-wire)
			### Set delay values ###
			K.write(f":TRIG{channel}:ACQ:DEL {delay_after_source}") # Acquire delay
			# K.write(f":SENS:WAIT {delay_after_source}") # Acquire delay
			K.write(f":TRIG{channel}:TRAN:DEL {delay_to_source_start}") # Acquire delay
			# K.write(f":SENS:CURR:APER {measurement_aperture_s}")

			K.write(f":TRIG{channel}:SOUR AINT") # Selects trigger source
			# K.write(f":TRIG{channel}:TIM {trigger_interval}") # Sets trigger interval
			K.write(f":TRIG{channel}:COUN {len(voltages)}") # Sets trigger count
			# K.write(f":TRIG{channel}:") # Sets trigger delay

			K.write(f":OUTP{channel} ON")  # Enable channel
			# K.write(f":OUTP:HCAP ON")
	#		K.write(f":INIT:AINT")  # Initiate transition and acquire (AINT for automatic trigger, BUS for remote trigger, TIM for internal timer, INTn for a signal from the internal bus n=1 or 2, EXTm for a signal from the GPIO pin m (m=1 to 14), or LAN for the LXI trigger)

			K.timeout = 5 * 60 * 1000 # The measurement may take up to 5 minutes
			K.write(f":INIT{channel}")  # Initiate transition and acquire (AINT for automatic trigger, BUS for remote trigger, TIM for internal timer, INTn for a signal from the internal bus n=1 or 2, EXTm for a signal from the GPIO pin m (m=1 to 14), or LAN for the LXI trigger)
			try:
				currents = K.query_ascii_values(':FETC:ARR:CURR? ', container=np.array) # Read current values
				results_by_compliance.append( currents )

				filter_over_compliance = (currents - compliance_A > -1E-2 * compliance_A) | (currents + compliance_A < 1E-2 * compliance_A)
				needs_higher_compliance = np.any( filter_over_compliance )
				if not needs_higher_compliance:
					break
			except visa.errors.VisaIOError as e:
				pass
	#		results = K.query_ascii_values(f':FETC:ARR:VOLT?', container=np.array) # Read current values

		K.write(f":OUTP{channel} OFF")  # Disable channel

		if len(results_by_compliance) == 0:
			return

		output_y = results_by_compliance[0]
		for c, y in zip( compliances[:-1], results_by_compliance[1:] ):
			filter_over_compliance = (y - c > -1E-2 * c) | (y + c < 1E-2 * c)
			output_y[ filter_over_compliance ] = y[ filter_over_compliance ]

		# K.timeout = 120000 # The measurement may take up to 120 seconds
		self.sweepFinished_signal.emit( voltages, np.array(output_y) )

	def Voltage_Noise_Keysight( self, bias_v, integration_time_s, sample_count ):
		K = self.gpib_resource

		K.write("*RST") # Reset everything to known good state (factory defaults)
		time.sleep( 2 ) # Sleep to make sure heater has time to turn off
		K.write(":SYST:LFR 60") # Set powerline cycle to 60 Hz
		self.newSweepStarted_signal.emit()

		# compliances = [1E-8, 1E-5, 1E-2]
		compliances = [1E-8, 1E-7, 1E-6, 1E-5, 1E-4, 1E-3, 1E-2]
		channel = 1 # or 2

		def prepare_measurement():
			K.write(f":SOUR{channel}:FUNC:MODE VOLT") # Source voltage (VOLT) not current (CURR)
			K.write(f":SOUR{channel}:VOLT {bias_v}") # Run a single voltage
			K.write(f":SENS{channel}:FUNC CURR")  # Set to measure current
			K.write(f":SENS{channel}:REM ON") # Enable remote sense (4-wire)

			### Set delay values ###
			# K.write(f":SENS:WAIT {delay_after_source}") # Acquire delay
			# K.write(f":TRIG{channel}:TRAN:DEL {delay_to_source_start}") # Acquire delay
			K.write(f":SENS{channel}:CURR:APER {integration_time_s}") # How long to aquire current data per measurement

			# K.write(f":TRIG{channel}:TIM {trigger_interval}") # Sets trigger interval
			# K.write(f":TRIG{channel}:") # Sets trigger delay

		prepare_measurement()
		compliance_to_use = 1E-2
		for compliance_A in compliances:
			K.write(f":SENS{channel}:CURR:PROT {compliance_A}")  # Set compliance current
			K.write(f":OUTP{channel} ON")  # Enable channel
			K.write(f":TRIG{channel}:ACQ:DEL {1E-3}") # Acquire delay

			K.timeout = 5 * 60 * 1000 # The measurement may take up to 5 minutes
			try:
				current = K.query_ascii_values(f':MEAS:CURR?', container=np.array)[0] # Read current values
				print( current )
				if abs(current) < 0.9 * compliance_A:
					compliance_to_use = compliance_A
					break
			except visa.errors.VisaIOError as e:
				print( e )

		# for compliance_A in compliances:
		if True:
			# K.write(f":OUTP{channel} OFF")  # Disable channel
			prepare_measurement()
			# K.write(f":SENS{channel}:CURR:PROT {compliance_A}")  # Set compliance current
			K.write(f":SENS{channel}:CURR:PROT {compliance_to_use}")  # Set compliance current
			# K.write(f":SOUR{channel}:CURR:RANG {compliance_to_use}")  # Set range current
			# K.write(f":OUTP{channel} ON")  # Enable channel
			K.write(f":SOUR{channel}:VOLT:MODE SWE") # Run a single voltage
			K.write(f":SOUR{channel}:VOLT:STAR {bias_v}") # Run a single voltage
			K.write(f":SOUR{channel}:VOLT:STOP {bias_v}") # Run a single voltage
			K.write(f":SOUR{channel}:VOLT:POIN {sample_count}") # Run a single voltage
			K.write(f":SOUR{channel}:SWE:RANG BEST") # Set range
			K.write(f":TRIG{channel}:ACQ:DEL {0}") # Acquire delay

			K.timeout = 5 * 60 * 1000 # The measurement may take up to 5 minutes
			K.write(f":TRIG{channel}:SOUR AINT") # Selects trigger source
			K.write(f":TRIG{channel}:COUN {sample_count}") # Sets trigger count
			K.write(f":INIT (@{channel})")  # Initiate transition and acquire (AINT for automatic trigger, BUS for remote trigger, TIM for internal timer, INTn for a signal from the internal bus n=1 or 2, EXTm for a signal from the GPIO pin m (m=1 to 14), or LAN for the LXI trigger)
			try:
				currents = K.query_ascii_values(':FETC:ARR:CURR?', container=np.array) # Read current values
				print( f"Compliance: {compliance_A} {abs(currents[0]) < 0.9 * compliance_A}")
				self.noiseMeasurementFinished_signal.emit( currents )
				print( currents )
				plt.plot( currents, label=f"{compliance_A}")
				
			except visa.errors.VisaIOError as e:
				print( e )

		K.write(f":OUTP{channel} OFF")  # Disable channel
		with open( "test_noise.csv", 'w' ) as csvfile:
			csvwriter = csv.writer( csvfile )
			for c in currents:
				csvwriter.writerow( [c], lineterminator="\n" )
		plt.legend()
		plt.show(block=True)


if __name__ == "__main__":
	iv = IV_Controller( machine_type="Keysight" )
	iv.Initialize_Connection()
	iv.Voltage_Noise_Keysight( bias_v=-0.025, integration_time_s=5E-5, sample_count=10000 )
	iv.Turn_Off_Bias_Keysight()