from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QLayout, QWidget, QLabel, QVBoxLayout, QFileDialog

from .Async_Iterator import Run_Async


def Controller_Connected( label, *identifiers ):
	label.setText( ' '.join(identifiers) )
	label.setStyleSheet("QLabel { background-color: rgba(0,255,0,255); color: rgba(0, 0, 0,255) }")

def Controller_Disconnected( label, *identifiers ):
	label.setText( ' '.join(identifiers) + " Not Connected " )
	label.setStyleSheet("QLabel { background-color: rgba(255,0,0,255); color: rgba(0, 0, 0,255) }")

def Add_To_Status_Widget( layout, subsystem ):
	label = QLabel()
	Controller_Disconnected( label, "" )
	layout.addWidget( label )
	subsystem.Device_Connected.connect(    lambda *identifiers, label=label : Controller_Connected(    label, *identifiers ) )
	subsystem.Device_Disconnected.connect( lambda *identifiers, label=label : Controller_Disconnected( label, *identifiers ) )

	return label

def Make_Threaded_System( parent, controller ):
	thread = QtCore.QThread( parent )
	controller.moveToThread( thread )
	thread.started.connect( controller.thread_start )
	thread.finished.connect( controller.thread_stop )
	return thread

class Threaded_Subsystems:
	# def __init__( self ):

	def Make_Subsystems( self, parent, layout_for_status, *subsystems ):
		self.subsystems = subsystems
		self.subsystem_threads = [ Make_Threaded_System(parent, s) for s in subsystems ]

		if layout_for_status is not None:
			self.status_labels = [Add_To_Status_Widget( layout_for_status, s ) for s in subsystems]

		return subsystems

	def Start_Subsystems( self ):
		for t in self.subsystem_threads:
			t.start()

	def closeEvent( self, event ):
		# self.Make_Safe()
		for thread in self.subsystem_threads:
			thread.quit()
		for thread in self.subsystem_threads:
			thread.wait()

	def Make_Safe( self ):
		for s in self.subsystems:
			Run_Async( s, lambda : s.Make_Safe() ).Run()
