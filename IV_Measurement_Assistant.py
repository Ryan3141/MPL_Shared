try:
	import visa
except:
	Ask_For_Install( "PyVisa" )
	import visa
import matplotlib.pyplot as plt
import numpy as np
import time

from PyQt5 import QtCore


class IV_Controller( QtCore.QObject ):
	newSweepStarted_signal = QtCore.pyqtSignal()
	dataPointGotten_signal = QtCore.pyqtSignal(float, float)
	sweepFinished_signal = QtCore.pyqtSignal(np.ndarray, np.ndarray)

	ivControllerConnected_signal = QtCore.pyqtSignal()
	ivControllerDisconnected_signal = QtCore.pyqtSignal()

	def __init__(self, parent=None):
		super(IV_Controller, self).__init__(parent)
		self.Keithly = None
		self.debug = 1
		self.stop_measurement_early = False

	def run(self):
		self.resource_manager = visa.ResourceManager()
		self.Initialize_Connection()


	def Close_Connection():
		self.Keithly.close()
		self.Keithly = None
		self.ivControllerDisconnected_signal.emit()


	def Initialize_Connection( self ):
		if self.Keithly != None:
			return
	#print( rm.list_resources() + "\n" ) # List available machines to connect to

		try:
			self.Keithly = self.resource_manager.open_resource('GPIB::26::INSTR') # Keithly 236's address on GPIB connection with IEEE-446 protocol
			self.ivControllerConnected_signal.emit()
			self.Keithly.clear()
			return self.Keithly
		except:
			return None

	def Close_Connection( self ):
		if self.Keithly == None:
			return

		self.Keithly.close()
		self.Keithly = None


	def Voltage_Sweep( self, input_start, input_end, input_step ):
		Keithly = self.Keithly
		if Keithly == None:
			print( "Keithly not connected, cannot run voltage sweep" )
			return
		
		Keithly = self.Keithly
		self.newSweepStarted_signal.emit()
		Keithly.write( "J0X" ) # Reset everything to known good state (factory defaults)
		Keithly.write( "F0,1X" ) # Source voltage (0), and measure dc current (0), then sweep (1) not dc (0)

		Keithly.write( "P1X" ) # Take 2^1 = 32 readings each measurement
		Keithly.write( "O1X" ) # Change to remote sensing (4 point probe)
		Keithly.write( "L25E-3,0X" ) # Set compliance to 25 mA, range (0 for autorange)
		Keithly.write( "S2X" ) # Integration time = 16.67 msec (for 60Hz power line)
		Keithly.write( "R0X" ) # Disable Triggers
		Keithly.write( "T4,0,0,0X" ) # Set triggering after H0X command and continue immediately
		Keithly.write( "R1X" ) # Enable Triggers

		Keithly.write( "Q1,{},{},{},0,10X".format( input_start, input_end, input_step ) ) # Linear stair step voltage (1), start, stop, step, range (0 for autorange), delay

		#timestr = time.strftime("%Y%m%d-%H%M%S")

		Keithly.write( "N1X" ) # Set machine to active mode
		Keithly.write( "H0X" ) # Send immediate trigger
		Keithly.write( "G4,2,1X" ) # Set reading format to read raw results one by one
		results = []
		x_values = np.arange( int(input_start * 1E9), int(input_end * 1E9) + 1, int(input_step * 1E9) ) / 1E9
		for index, x in enumerate(x_values):
			data = Keithly.read()
			#print( data )
			results.append( float(data) )
			self.dataPointGotten_signal.emit( x, float(data) )
			if index % 10 == 0:
				QtCore.QCoreApplication.processEvents()
				if self.stop_measurement_early == True:
					self.stop_measurement_early = False
					break

		Keithly.write( "N0X" ) # Return machine to standby[3:]

		#Keithly.write( "B0.1,0,200X" ) # Set bias to 0.1 V, autorange the bias range, delay in milliseconds

		#Keithly.write( "G4,2,2X" ) # Set the read to just spit out the raw current values (in A) when we call read, final 2 means give all lines of sweep data per talk
		#results = Keithly.read()
		Keithly.timeout = 120000 # The measurement may take up to 120 seconds
		results = Keithly.query_ascii_values('G4,2,2X', container=np.array)
		self.sweepFinished_signal.emit( x_values, np.array(results) )




