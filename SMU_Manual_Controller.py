from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget
try:
	from PyQt5 import uic
except ImportError:
	import sip

from .GUI_Tools import resource_path

Ui_Widget, QtBaseClass = uic.loadUiType( resource_path("SMU_Manual_Controller.ui") ) # GUI layout file.


class SMU_Manual_Controller( QWidget, Ui_Widget ):
	biasOn_signal = QtCore.pyqtSignal( float )
	biasOff_signal = QtCore.pyqtSignal()

	def __init__( self, parent=None ):
		QWidget.__init__( self, parent )
		Ui_Widget.__init__( self )
		self.setupUi(self)

		self.Bias_Turned_Off()

	def Current_Changed( self, new_current_a ):
		self.currentOutput_lineEdit.setText( f"{new_current_a:0.2e} A" )

	def Connect_To_IV_Controller( self, iv_controller ):
		iv_controller.Bias_Is_Set.connect( lambda voltage, current : self.Bias_Value_Changed( voltage ) )
		iv_controller.Bias_Is_Set.connect( lambda voltage, current : self.Update_Button_Bias_Turned_On() )
		iv_controller.Bias_Is_Off.connect( self.Update_Button_Bias_Turned_Off )
		iv_controller.Current_Output.connect( self.Current_Changed )
		self.biasOff_signal.connect( iv_controller.Turn_Off_Bias )
		self.biasOn_signal.connect( iv_controller.Set_Bias )

	def Bias_Value_Changed( self, voltage_v ):
		self.bias_mV_doubleSpinBox.setValue( voltage_v * 1000 )

	def Bias_Turned_On( self ):
		self.biasOn_signal.emit( float(self.bias_mV_doubleSpinBox.value()) / 1000 )
		self.Update_Button_Bias_Turned_On()

	def Update_Button_Bias_Turned_On( self ):
		self.turnBiasOn_pushButton.setText( "Turn Bias Off" )
		self.turnBiasOn_pushButton.setStyleSheet("QPushButton { background-color: rgba(0,255,0,255); color: rgba(0, 0, 0,255); }")
		try: self.turnBiasOn_pushButton.clicked.disconnect()
		except Exception: pass
		self.turnBiasOn_pushButton.clicked.connect( self.Bias_Turned_Off )

	def Bias_Turned_Off( self ):
		self.biasOff_signal.emit()
		self.Update_Button_Bias_Turned_Off()

	def Update_Button_Bias_Turned_Off( self ):
		self.turnBiasOn_pushButton.setText( "Turn Bias On" )
		self.turnBiasOn_pushButton.setStyleSheet("QPushButton { background-color: rgba(255,0,0,255); color: rgba(0, 0, 0,255); }")
		try: self.turnBiasOn_pushButton.clicked.disconnect()
		except Exception: pass
		self.turnBiasOn_pushButton.clicked.connect( self.Bias_Turned_On )
