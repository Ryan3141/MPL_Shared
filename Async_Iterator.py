import time

from PyQt5 import QtCore
from itertools import product
from threading import Event

class Quitting_Early_Exception( Exception ):
	pass

class Run_Async( QtCore.QObject ):
	RunRequest_signal = QtCore.pyqtSignal( object, object )
	def __init__( self, context, function_to_run ):
		QtCore.QObject.__init__( self )
		self.function_to_run = function_to_run
		self.moveToThread( context.thread() )
		self.RunRequest_signal.connect( self._Async_Run )

	def Run( self, *args, **kargs ):
		# print( "Run Thread:", QtCore.QThread.currentThread() )
		# print( f"args={args} kargs={kargs}")
		self.RunRequest_signal.emit( args, kargs )
		QtCore.QCoreApplication.processEvents()

	def _Async_Run( self, args, kargs ):
		# print( "Async_Run Thread:", QtCore.QThread.currentThread() )
		self.function_to_run( *args, **kargs )

class Run_Async2( QtCore.QObject ):
	RunRequest_signal = QtCore.pyqtSignal( object, object )
	ResultsAcquired_signal = QtCore.pyqtSignal( object )
	def __init__( self, context, function_to_run, quit_early_flag ):
		QtCore.QObject.__init__( self )
		self.quit_early = quit_early_flag
		self.awaiting_results = True
		self.function_to_run = function_to_run
		self.ResultsAcquired_signal.connect( self.Results_Obtained )
		self.moveToThread( context.thread() )
		self.RunRequest_signal.connect( self._Async_Run )

	def Results_Obtained( self, results ): # Run on calling thread
		self.results = results
		self.awaiting_results = False

	def Run( self, *args, **kargs ): # Run on calling thread
		# print( "Run Thread:", QtCore.QThread.currentThread() )
		# print( f"args={args} kargs={kargs}")
		self.RunRequest_signal.emit( args, kargs )
		while( self.awaiting_results ):
			if self.quit_early.is_set():
				raise Quitting_Early_Exception()
			QtCore.QCoreApplication.processEvents()
		return self.results

	def _Async_Run( self, args, kargs ): # Run on other thread
		# print( "Async_Run Thread:", QtCore.QThread.currentThread() )
		results = self.function_to_run( *args, **kargs )
		self.ResultsAcquired_signal.emit( results )

quit_early_flag = Event()
def Get_Quit_Early_Flag():
	global quit_early_flag
	return quit_early_flag
def Run_Func_Async( context, function, *args, **kargs ):
	global quit_early_flag
	x = Run_Async2( context, function, quit_early_flag )
	return x.Run( *args, **kargs )

if __name__ == "__main__": # Test the threading
	import time
	class Test_Threading_Class( QtCore.QObject ):
		def __init__( self ):
			QtCore.QObject.__init__(self)
			print( "__init__" )
		def thread_start( self ):
			for i in range( 5 ):
				print( f"Sleeping {i}" )
				# QtCore.QCoreApplication.processEvents()
				time.sleep( 2 )

		def test( self, x, y ):
			print( "test" )
			return x + y

	from PyQt5 import QtWidgets
	import sys
	app = QtWidgets.QApplication( sys.argv )
	controller = Test_Threading_Class()
	thread = QtCore.QThread()
	controller.moveToThread( thread )
	thread.started.connect( controller.thread_start )
	thread.start()
	print( "Waiting for results" )
	results = Run_Func_Async( controller, controller.test, 40, 2 )
	print( results )

class Async_Iterator( QtCore.QObject ):
	def __init__( self, values_to_run, context, requests_to_prepare, inform_its_ready, should_quit_early ):#, call_this_on_finish = lambda value_run : None ):
		QtCore.QObject.__init__(self)
		self.should_quit_early = False
		self.values_to_run = values_to_run
		self.request = Run_Async( context, requests_to_prepare )
		self.inform_its_ready = inform_its_ready
		self.should_quit_early = should_quit_early

	def Results_In( self, *results ):
		self.results = results
		self.finished_once = True

	def __iter__( self ):
		self.loop_instance = self.loop()
		self.results = None
		self.finished_once = False
		return self

	def __next__( self ):
		return next( self.loop_instance )

	def loop( self ):
		for value in self.values_to_run:
			if self.should_quit_early.is_set():
				return
			self.inform_its_ready.connect( self.Results_In )
			self.request.Run( value )

			while self.finished_once == False:
				time.sleep( 1 )
				QtCore.QCoreApplication.processEvents()
				if self.should_quit_early.is_set():
					return
			self.inform_its_ready.disconnect( self.Results_In )
			self.finished_once = False
			if value is None:
				if len( self.results ) == 1:
					yield self.results[ 0 ]
				else:
					yield self.results
			elif len( self.results ) == 0:
				yield value
			else:
				if len( self.results ) == 1:
					yield value, self.results[ 0 ]
				else:
					yield value, self.results
