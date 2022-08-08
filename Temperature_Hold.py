from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget
try:
	from PyQt5 import uic
except ImportError:
	import sip

from .GUI_Tools import resource_path

Ui_Widget, QtBaseClass = uic.loadUiType( resource_path("Temperature_Hold.ui") ) # GUI layout file.


class Temperature_Hold( QWidget, Ui_Widget ):
	tempHoldRequest_signal = QtCore.pyqtSignal( float )
	tempHoldStop_signal = QtCore.pyqtSignal()

	def __init__( self, parent=None ):
		QWidget.__init__( self, parent )
		Ui_Widget.__init__( self )
		self.setupUi(self)

		self.Stop_Set_Temperature()

	def Connect_To_Temperature_Controller( self, temp_controller ):
		self.tempHoldRequest_signal.connect( temp_controller.Set_Temp_And_Turn_On )
		self.tempHoldStop_signal.connect( temp_controller.Turn_Off )

	def Start_Set_Temperature( self ):
		try: self.tempHoldRequest_signal.emit( float(self.currentTemperature_lineEdit.text()) )
		except ValueError: return

		self.setTemperature_pushButton.setText( "Stop Temperature Hold" )
		self.setTemperature_pushButton.setStyleSheet("QPushButton { background-color: rgba(0,255,0,255); color: rgba(0, 0, 0,255); }")
		try: self.setTemperature_pushButton.clicked.disconnect()
		except Exception: pass
		self.setTemperature_pushButton.clicked.connect( self.Stop_Set_Temperature )

	def Stop_Set_Temperature( self ):
		self.tempHoldStop_signal.emit()

		self.setTemperature_pushButton.setText( "Hold Temperature" )
		self.setTemperature_pushButton.setStyleSheet("QPushButton { background-color: rgba(255,0,0,255); color: rgba(0, 0, 0,255); }")
		try: self.setTemperature_pushButton.clicked.disconnect()
		except Exception: pass
		self.setTemperature_pushButton.clicked.connect( self.Start_Set_Temperature )
