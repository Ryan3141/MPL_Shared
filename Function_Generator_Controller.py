from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget
try:
	from PyQt5 import uic
except ImportError:
	import sip

import pyvisa as visa
from .GUI_Tools import resource_path

Ui_Widget, QtBaseClass = uic.loadUiType( resource_path("Function_Generator_Controller.ui") ) # GUI layout file.


class Function_Generator_Controller( QWidget, Ui_Widget ):
	outputOn_signal = QtCore.pyqtSignal()
	outputOff_signal = QtCore.pyqtSignal()

	def __init__( self, parent=None ):
		QWidget.__init__( self, parent )
		Ui_Widget.__init__( self )
		self.setupUi(self)

		self.func_gen = None
		self.Connect_To_Function_Generator()
		self.Set_Output_Off()

	def Connect_To_Function_Generator( self ):
		rm = visa.ResourceManager()
		if "GPIB0::10::INSTR" in rm.list_resources():
			self.func_gen = rm.open_resource( "GPIB0::10::INSTR" )

	def Set_Output_On( self ):
		if self.func_gen == None:
			print( "Not connected to the function generator" )
			return
		self.func_gen.write( "OUTPUT ON" )
		self.outputOn_signal.emit()

		self.turnOutputOn_pushButton.setText( "Turn Output OFF" )
		self.turnOutputOn_pushButton.setStyleSheet("QPushButton { background-color: rgba(0,255,0,255); color: rgba(0, 0, 0,255); }")
		try: self.turnOutputOn_pushButton.clicked.disconnect()
		except Exception: pass
		self.turnOutputOn_pushButton.clicked.connect( self.Set_Output_Off )

	def Set_Output_Off( self ):
		if None == self.func_gen:
			return
		self.func_gen.write( "OUTPUT OFF" )
		self.outputOff_signal.emit()

		self.turnOutputOn_pushButton.setText( "Turn Output ON" )
		self.turnOutputOn_pushButton.setStyleSheet("QPushButton { background-color: rgba(255,0,0,255); color: rgba(0, 0, 0,255); }")
		try: self.turnOutputOn_pushButton.clicked.disconnect()
		except Exception: pass
		self.turnOutputOn_pushButton.clicked.connect( self.Set_Output_On )
