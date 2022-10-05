from PyQt5 import QtNetwork, QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QFileDialog
from PyQt5.QtCore import QMetaObject, Q_RETURN_ARG, Q_ARG
from PyQt5 import QtCore

import os
import inspect


def debug_print( *args, **kargs ):
	if False: # Whether or not it's debugging
		print( *args, **kargs )

def Popup_Error( title, message ):
	error = QtWidgets.QMessageBox()
	error.setIcon( QtWidgets.QMessageBox.Critical )
	error.setText( message )
	error.setWindowTitle( title )
	error.setStandardButtons( QtWidgets.QMessageBox.Ok )
	return_value = error.exec_()
	return

def Popup_Yes_Or_No( title, message ):
	error = QtWidgets.QMessageBox()
	error.setIcon( QtWidgets.QMessageBox.Critical )
	error.setText( message )
	error.setWindowTitle( title )
	error.setStandardButtons( QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No )
	return_value = error.exec_()
	return return_value == QtWidgets.QMessageBox.Yes

""" Get absolute path to resource, works for dev and for PyInstaller """
def resource_path( relative_path = "" ):  # Define function to import external files when using PyInstaller.
	caller_file = inspect.stack()[1][1] # Get the file location of the file who called this function
	base_path = os.path.dirname( os.path.realpath( caller_file ) )
	return os.path.join(base_path, relative_path)

class Measurement_Sweep_Runner( QtCore.QObject ):
	Finished_signal = QtCore.pyqtSignal()
	Error_signal = QtCore.pyqtSignal( str )
	def __init__( self, parent, finished, quit_early, Measurement_Sweep, *args, **kargs ):
		QtCore.QObject.__init__(self)
		self.Finished_signal.connect( finished )
		self.Measurement_Sweep = Measurement_Sweep
		self.args = args
		self.kargs = kargs
		self.quit_early = quit_early
		# self.Run()
		self.thread_to_use = QtCore.QThread( parent=parent )
		self.moveToThread( self.thread_to_use )
		self.thread_to_use.started.connect( self.Run )
		# self.thead_to_use.finished.connect( self.thead_to_use.deleteLater )
		self.thread_to_use.start()

	def Run( self ):
		# try:
		self.Measurement_Sweep( self.quit_early, *self.args, **self.kargs )
		self.Finished_signal.emit()
		# except Exception as e:
		# 	print( str(e) )
		# 	self.Error_signal.emit( str(e) )
		# finally:
		print( "Stopping Measurement_Sweep_Runner" )

	def wait( self ):
		self.thread_to_use.quit()
		self.thread_to_use.wait()


# class Basic_GUI:
# 	def Select_Device_File( self ):
# 		fileName, _ = QFileDialog.getOpenFileName( self, "QFileDialog.getSaveFileName()", "", "CSV Files (*.csv);;All Files (*)" )
# 		if fileName == "": # User cancelled
# 			return
# 		try:
# 			config_info = Get_Device_Description_File( fileName )
# 		except Exception as e:
# 			Popup_Error( "Error", str(e) )
# 			return

# 		self.descriptionFilePath_lineEdit.setText( fileName )

