from .Install_If_Necessary import Ask_For_Install
try:
	import pyvisa as visa
except ImportError:
	Ask_For_Install( "PyVisa" )
	import pyvisa as visa
import matplotlib.pyplot as plt
import numpy as np
import time

from PyQt5 import QtCore


class IV_Controller( QtCore.QObject ):
	newSweepStarted_signal = QtCore.pyqtSignal()
	dataPointGotten_signal = QtCore.pyqtSignal(float, float) # Voltage (in V), Current (in A)
	sweepFinished_signal = QtCore.pyqtSignal(np.ndarray, np.ndarray) # Voltages (in V), Currents (in A)

	ivControllerConnected_signal = QtCore.pyqtSignal()
	ivControllerDisconnected_signal = QtCore.pyqtSignal()
	Bias_Is_Set = QtCore.pyqtSignal( float, float ) # args: Voltage set (in V), Current (in A)

	def __init__(self, parent=None):
		super(IV_Controller, self).__init__(parent)
		self.gpib_resource = None
		self.stop_measurement_early = False
		self.Voltage_Sweep_Func = lambda self, input_start, input_end, input_step, time_interval : (np.aray(), np.array())

	def Voltage_Sweep( self, input_start, input_end, input_step, time_interval ):
		return self.Voltage_Sweep_Func( input_start, input_end, input_step, time_interval )

	def Close_Connection():
		self.Keithley.close()
		self.Keithley = None
		self.ivControllerDisconnected_signal.emit()


	def Initialize_Connection( self, which_machine ):
		if self.gpib_resource != None:
			self.gpib_resource.close()
			self.gpib_resource = None
		#print( rm.list_resources() + "\n" ) # List available machines to connect to

		# whats_available = rm.list_resources()
		supported_devices = { "Keysight" : ( 'GPIB::23::INSTR', self.Voltage_Sweep_Keysight ), # Keysight B2962A's address on GPIB connection with IEEE-446 protocol
		                      "Keithley" : ('GPIB::26::INSTR', self.Voltage_Sweep_Keithly ) } # Keithley 236's address on GPIB connection with IEEE-446 protocol

		try:
			address, function = supported_devices[which_machine]
			self.resource_manager = visa.ResourceManager()
			self.gpib_resource = self.resource_manager.open_resource(address)
			self.Voltage_Sweep_Func = function
			self.gpib_resource.clear()
			self.ivControllerConnected_signal.emit()
			return self.gpib_resource
		except Exception:
			pass

		self.debug = 1
		self.Voltage_Sweep_Func = self.Voltage_Sweep_Dummy
		return None


	def Close_Connection( self ):
		if self.gpib_resource == None:
			return

		self.gpib_resource.close()
		self.gpib_resource = None

	def Voltage_Sweep_Dummy( self, input_start, input_end, input_step, time_interval ):
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

	def Voltage_Sweep_Keithly( self, input_start, input_end, input_step, time_interval ):
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

		Keithley.write( "N0X" ) # Return machine to standby[3:]

		#Keithley.write( "B0.1,0,200X" ) # Set bias to 0.1 V, autorange the bias range, delay in milliseconds

		#Keithley.write( "G4,2,2X" ) # Set the read to just spit out the raw current values (in A) when we call read, final 2 means give all lines of sweep data per talk
		#results = Keithley.read()
		Keithley.timeout = 10 * 120000 # The measurement may take up to 1200 seconds
		results = Keithley.query_ascii_values('G4,2,2X', container=np.array)
		if len(x_values) != len(results):
			print( f"Error len(x_values)={len(x_values)} and len(results)={len(results)}" )
		else:
			self.sweepFinished_signal.emit( x_values, np.array(results) )


	def Set_Bias( self, bias_V ):
		K = self.gpib_resource
		channel = 1 # or 2
		compliance_A = 0.025 # Amps
		K.write(f":SOUR{channel}:FUNC:MODE VOLT") # Source voltage (VOLT) not current (CURR)
		K.write(f":SOUR{channel}:VOLT {bias_V}") # Set amount

		K.write(f":SENS{channel}:CURR:PROT {compliance_A}")  # Set compliance current
		K.write(f":OUTP{channel} ON")  # Enable channel
		current = K.query_ascii_values(':MEAS:CURR?', container=np.array) # Read current values
		print( f"Bias = {bias_V} V" )
		print( f"current = {current} A" )
		self.Bias_Is_Set.emit( bias_V, current[0] )

	def Turn_Off_Bias( self ):
		K = self.gpib_resource
		channel = 1 # or 2
		K.write(f":OUTP{channel} OFF")  # Enable channel


	def Voltage_Sweep_Keysight( self, input_start, input_end, input_step, time_interval ):
		K = self.gpib_resource

		K.write("*RST") # Reset everything to known good state (factory defaults)
		time.sleep( 2 ) # Sleep to make sure heater has time to turn off
		K.write(":SYST:LFR 60") # Set powerline cycle to 60 Hz
		self.newSweepStarted_signal.emit()

		channel = 1 # or 2
		delay_after_source = time_interval
		trigger_interval = 0.001 # Seconds
		compliance_A = 0.025 # Amps
		number_of_powerline_cycles = 1
		x_values = np.arange( int(input_start * 1E9), int(input_end * 1E9) + 1, int(input_step * 1E9) ) / 1E9
		voltages = x_values
		# voltages = np.linspace( 0.0, 1.0, 5 )

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

		K.timeout = 12000000 # The measurement may take up to 120 seconds
		K.write(f":INIT{channel}")  # Initiate transition and acquire (AINT for automatic trigger, BUS for remote trigger, TIM for internal timer, INTn for a signal from the internal bus n=1 or 2, EXTm for a signal from the GPIO pin m (m=1 to 14), or LAN for the LXI trigger)
		results = K.query_ascii_values(':FETC:ARR:CURR? ', container=np.array) # Read current values
#		results = K.query_ascii_values(f':FETC:ARR:VOLT?', container=np.array) # Read current values

		K.write(f":OUTP{channel} OFF")  # Disable channel

		# K.timeout = 120000 # The measurement may take up to 120 seconds
		self.sweepFinished_signal.emit( x_values, np.array(results) )
