import time

from PyQt5 import QtCore
from itertools import product

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


class Async_Iterator( QtCore.QObject ):
	def __init__( self, values_to_run, context, requests_to_prepare, inform_its_ready, quit_early ):#, call_this_on_finish = lambda value_run : None ):
		QtCore.QObject.__init__(self)
		self.should_quit_early = False
		self.values_to_run = values_to_run
		self.request = Run_Async( context, requests_to_prepare )
		self.inform_its_ready = inform_its_ready
		quit_early.connect( self.Quit_Early )

	def Results_In( self, *results ):
		self.results = results
		self.finished_once = True

	def Quit_Early( self, *args ):
		# print( "Quit Early" )
		self.should_quit_early = True

	def __iter__( self ):
		self.loop_instance = self.loop()
		self.results = None
		self.finished_once = False
		return self

	def __next__( self ):
		return next( self.loop_instance )

	def loop( self ):
		for value in self.values_to_run:
			if self.should_quit_early:
				return
			self.inform_its_ready.connect( self.Results_In )
			self.request.Run( value )

			while self.finished_once == False:
				time.sleep( 1 )
				QtCore.QCoreApplication.processEvents()
				if self.should_quit_early:
					return
			self.inform_its_ready.disconnect( self.Results_In )
			self.finished_once = False
			if value is None:
				yield self.results
			elif len( self.results ) == 0:
				yield value
			else:
				yield value, self.results
