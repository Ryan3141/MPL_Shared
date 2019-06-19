from PyQt5 import QtNetwork, QtCore, QtGui, uic, QtWidgets

import os

base_path = os.path.dirname( os.path.realpath(__file__) )

def resource_path(relative_path):  # Define function to import external files when using PyInstaller.
    """ Get absolute path to resource, works for dev and for PyInstaller """
    return os.path.join(base_path, relative_path)

qtConfigurationUIFile = resource_path( "Temperature_Controller_Settings.ui" ) # GUI layout file.
Ui_ConfigurationWindow, QtBaseClass2 = uic.loadUiType(qtConfigurationUIFile)

class TemperatureControllerSettingsWindow(QtWidgets.QWidget, Ui_ConfigurationWindow):
	def __init__(self, parent=None):
		QtWidgets.QWidget.__init__(self, parent)
		Ui_ConfigurationWindow.__init__(self)
		self.setupUi(self)

	def Connect_Functions( self, temp_controller ):
		self.kp_lineEdit.returnPressed.connect( lambda tc=temp_controller : self.Send_New_PID_Coefficients( tc ) )
		self.ki_lineEdit.returnPressed.connect( lambda tc=temp_controller : self.Send_New_PID_Coefficients( tc ) )
		self.kd_lineEdit.returnPressed.connect( lambda tc=temp_controller : self.Send_New_PID_Coefficients( tc ) )
		self.updatePads_pushButton.clicked.connect( lambda x, tc=temp_controller : self.Send_New_Selected_Pads( tc ) )
		temp_controller.PID_Coefficients_Changed.connect( self.PID_Coefficients_Updated )
		temp_controller.Pads_Selected_Changed.connect( self.Pads_Selected_Updated )
		temp_controller.Pads_Selected_Invalid.connect( self.Pads_Selected_Error )

	def Send_New_PID_Coefficients( self, temp_controller ):
		try:
			kp = float(self.kp_lineEdit.text())
			ki = float(self.ki_lineEdit.text())
			kd = float(self.kd_lineEdit.text())
			temp_controller.Set_PID( (kp, ki, kd) )
			self.kp_lineEdit.setStyleSheet("QLineEdit { background-color: rgba(255,255,0,255); color: rgba(0, 0, 0,255); }")
			self.ki_lineEdit.setStyleSheet("QLineEdit { background-color: rgba(255,255,0,255); color: rgba(0, 0, 0,255); }")
			self.kd_lineEdit.setStyleSheet("QLineEdit { background-color: rgba(255,255,0,255); color: rgba(0, 0, 0,255); }")
		except:
			pass

	def Send_New_Selected_Pads( self, temp_controller ):
		try:
			pad1 = int(self.pad1_lineEdit.text())
			pad2 = int(self.pad2_lineEdit.text())
			temp_controller.Set_Active_Pads( pad1, pad2 )
			self.pad1_lineEdit.setStyleSheet("QLineEdit { background-color: rgba(255,255,0,255); color: rgba(0, 0, 0,255); }")
			self.pad2_lineEdit.setStyleSheet("QLineEdit { background-color: rgba(255,255,0,255); color: rgba(0, 0, 0,255); }")
		except:
			self.Pads_Selected_Error()

	def PID_Coefficients_Updated( self, pid_coefficients ):
		print( "PID Coefficients: {}".format(pid_coefficients) )
		self.kp_lineEdit.setText( str( pid_coefficients[0] ) )
		self.ki_lineEdit.setText( str( pid_coefficients[1] ) )
		self.kd_lineEdit.setText( str( pid_coefficients[2] ) )
		self.kp_lineEdit.setStyleSheet("QLineEdit { background-color: rgba(0,255,0,255); color: rgba(0, 0, 0,255); }")
		self.ki_lineEdit.setStyleSheet("QLineEdit { background-color: rgba(0,255,0,255); color: rgba(0, 0, 0,255); }")
		self.kd_lineEdit.setStyleSheet("QLineEdit { background-color: rgba(0,255,0,255); color: rgba(0, 0, 0,255); }")

	def Pads_Selected_Updated( self, pads_selected, is_reversed ):
		print( "Pads Connected: {}".format(pads_selected) )
		self.pad1_lineEdit.setText( str( pads_selected[0] )  )
		self.pad2_lineEdit.setText( str( pads_selected[1] ) )
		self.pad1_lineEdit.setStyleSheet("QLineEdit { background-color: rgba(0,255,0,255); color: rgba(0, 0, 0,255); }")
		self.pad2_lineEdit.setStyleSheet("QLineEdit { background-color: rgba(0,255,0,255); color: rgba(0, 0, 0,255); }")

	def Pads_Selected_Error( self ):
		print( "Error Connecting Pads {} and {}".format( self.pad1_lineEdit.text(), self.pad2_lineEdit.text() ) )
