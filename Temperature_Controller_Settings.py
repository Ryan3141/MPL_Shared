from PyQt5 import QtNetwork, QtCore, QtGui, uic, QtWidgets

import os

from .GUI_Tools import resource_path, debug_print


qtConfigurationUIFile = resource_path( "Temperature_Controller_Settings.ui" ) # GUI layout file.
Ui_ConfigurationWindow, QtBaseClass2 = uic.loadUiType(qtConfigurationUIFile)
yellow_background_text = "QLineEdit { background-color: rgba(255,255,0,255); color: rgba(0, 0, 0,255); }"
green_background_text = "QLineEdit { background-color: rgba(0,255,0,255); color: rgba(0, 0, 0,255); }"
yellow_background_text_button = "QPushButton { background-color: rgba(255,255,0,255); color: rgba(0, 0, 0,255); }"
green_background_text_button = "QPushButton { background-color: rgba(0,255,0,255); color: rgba(0, 0, 0,255); }"
class TemperatureControllerSettingsWindow(QtWidgets.QWidget, Ui_ConfigurationWindow):
	Temperature_Change_Requested = QtCore.pyqtSignal(float, float, float) # kp, ki, kd
	Pad_Change_Requested = QtCore.pyqtSignal(int, int)
	Transimpedance_Change_Requested = QtCore.pyqtSignal(int)

	def __init__(self, parent=None):
		QtWidgets.QWidget.__init__(self, parent)
		Ui_ConfigurationWindow.__init__(self)
		self.setupUi(self)

		self.transimpedance_buttons = [self.transimpedanceGainOff_pushButton, self.transimpedanceGain100_pushButton, self.transimpedanceGain1000_pushButton, self.transimpedanceGain10000_pushButton, self.transimpedanceGain100000_pushButton]
		self.transimpedance_settings = [0, 100, 1000, 10000, 100000]

	def Connect_Functions( self, temp_controller ):
		self.kp_lineEdit.returnPressed.connect( self.Send_New_PID_Coefficients )
		self.ki_lineEdit.returnPressed.connect( self.Send_New_PID_Coefficients )
		self.kd_lineEdit.returnPressed.connect( self.Send_New_PID_Coefficients )
		self.kp_lineEdit.textChanged.connect( lambda : self.kp_lineEdit.setStyleSheet( yellow_background_text ) )
		self.ki_lineEdit.textChanged.connect( lambda : self.ki_lineEdit.setStyleSheet( yellow_background_text ) )
		self.kd_lineEdit.textChanged.connect( lambda : self.kd_lineEdit.setStyleSheet( yellow_background_text ) )
		self.pad1_lineEdit.textChanged.connect( lambda : self.pad1_lineEdit.setStyleSheet( yellow_background_text ) )
		self.pad2_lineEdit.textChanged.connect( lambda : self.pad2_lineEdit.setStyleSheet( yellow_background_text ) )
		self.pad1_lineEdit.returnPressed.connect( self.Send_New_Selected_Pads )
		self.pad2_lineEdit.returnPressed.connect( self.Send_New_Selected_Pads )

		for gain, button in zip( self.transimpedance_settings, self.transimpedance_buttons ):
			button.clicked.connect( lambda *args, gain=gain : self.Transimpedance_Change_Requested.emit( gain ) )
			button.clicked.connect( lambda : [x.setStyleSheet( yellow_background_text_button ) for x in self.transimpedance_buttons ] )
		self.Transimpedance_Change_Requested.connect( temp_controller.Set_Transimpedance_Gain )
		temp_controller.Transimpedance_Gain_Changed.connect( self.Transimpedance_Selected )

		self.Temperature_Change_Requested.connect( temp_controller.Set_PID )
		self.Pad_Change_Requested.connect( temp_controller.Set_Active_Pads )
		self.updatePads_pushButton.clicked.connect( self.Send_New_Selected_Pads )
		temp_controller.PID_Coefficients_Changed.connect( self.PID_Coefficients_Updated )
		temp_controller.Pads_Selected_Changed.connect( self.Pads_Selected_Updated )
		temp_controller.Pads_Selected_Invalid.connect( self.Pads_Selected_Error )

	def Transimpedance_Selected( self, gain ):
		for setting, button in zip( self.transimpedance_settings, self.transimpedance_buttons ):
			if setting == gain:
				button.setStyleSheet( green_background_text_button )
			else:
				button.setStyleSheet( yellow_background_text_button )

	def Send_New_PID_Coefficients( self ):
		try:
			kp = float( self.kp_lineEdit.text() )
			ki = float( self.ki_lineEdit.text() )
			kd = float( self.kd_lineEdit.text() )
			self.Temperature_Change_Requested.emit( kp, ki, kd )
			#temp_controller.Set_PID( (kp, ki, kd) )
			#self.kp_lineEdit.setStyleSheet( yellow_background_text )
			#self.ki_lineEdit.setStyleSheet( yellow_background_text )
			#self.kd_lineEdit.setStyleSheet( yellow_background_text )
		except Exception:
			pass

	def Send_New_Selected_Pads( self ):
		try:
			pad1 = int( self.pad1_lineEdit.text() )
			pad2 = int( self.pad2_lineEdit.text() )
			self.Pad_Change_Requested.emit( pad1, pad2 )
			#temp_controller.Set_Active_Pads( pad1, pad2 )
			#self.pad1_lineEdit.setStyleSheet( yellow_background_text )
			#self.pad2_lineEdit.setStyleSheet( yellow_background_text )
		except Exception:
			self.Pads_Selected_Error()

	def PID_Coefficients_Updated( self, pid_coefficients ):
		debug_print( "PID Coefficients: {}".format(pid_coefficients) )
		self.kp_lineEdit.setText( str( pid_coefficients[0] ) )
		self.ki_lineEdit.setText( str( pid_coefficients[1] ) )
		self.kd_lineEdit.setText( str( pid_coefficients[2] ) )
		self.kp_lineEdit.setStyleSheet( green_background_text )
		self.ki_lineEdit.setStyleSheet( green_background_text )
		self.kd_lineEdit.setStyleSheet( green_background_text )

	def Pads_Selected_Updated( self, pads_selected, is_reversed ):
		debug_print( "Pads Connected: {}".format(pads_selected) )
		self.pad1_lineEdit.setText( str( pads_selected[0] )  )
		self.pad2_lineEdit.setText( str( pads_selected[1] ) )
		self.pad1_lineEdit.setStyleSheet( green_background_text )
		self.pad2_lineEdit.setStyleSheet( green_background_text )

	def Pads_Selected_Error( self ):
		print( "Error Connecting Pads {} and {}".format( self.pad1_lineEdit.text(), self.pad2_lineEdit.text() ) )
