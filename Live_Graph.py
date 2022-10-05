#from PyQt5.QtChart import QChart, QChartView, QLineSeries, QDateTimeAxis, QValueAxis
from PyQt5.QtGui import QPolygonF, QPainter, QBrush, QGradient, QLinearGradient, QColor, QFont, QPen
from PyQt5.QtCore import Qt, QDateTime, QDate, QTime, QPointF
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout

needs_reload = False
from importlib import reload


import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.animation as animation

import numpy as np
import time

import matplotlib.cm as cm

class Live_Graph( QWidget ):
	def __init__(self, parent=None):
		super().__init__(parent=parent)

		#self.graph_colors = cm.get_cmap('seismic')(np.linspace(0, 1, 10))
		self.graph_colors = cm.rainbow(np.linspace(0, 1, 10))
		# a figure instance to plot on
		self.figure = plt.figure()
		# this is the Canvas Widget that displays the `figure`
		# it takes the `figure` instance as a parameter to __init__
		self.canvas = FigureCanvas( self.figure )
		# this is the Navigation widget
		# it takes the Canvas widget and a parent
		self.toolbar = NavigationToolbar( self.canvas, self )
		# set the layout
		plt.ion()
		layout = QVBoxLayout()
		layout.addWidget(self.canvas)
		layout.addWidget(self.toolbar)
		self.setLayout(layout)


		self.ax = self.figure.add_subplot(111)
		self.ax.grid(which='both')
		self.ax.grid(which='minor', alpha=0.2, linestyle='--')
		self.figure.tight_layout()

	def set_labels( self, title, x_label, y_label ):
		self.ax.set_xlabel( x_label )
		self.ax.set_ylabel( y_label )
		self.ax.set_title( title )
		self.figure.tight_layout()

	def close( self ):
		global needs_reload
		needs_reload = True
		del self.figure

	def prepare_blit_box( self ):
		self.canvas.draw()
		self.canvas.show()
		self.figure.canvas.flush_events()
		self.background = self.figure.canvas.copy_from_bbox(self.figure.bbox)

	def start_live_updates( self, list_of_graphs, update_interval_ms=20 ):
		# self.canvas.draw()
		# self.canvas.show()
		# self.figure.canvas.flush_events()
		# time.sleep( 0.5 )
		# plt.pause( 0.1 )
		# self.figure.canvas.pause(0.1) # Spin the event loop to let the backend process any pending operations
		# self.background = self.figure.canvas.copy_from_bbox(self.figure.bbox)
		def redraw_graphs():
			# reload_data_function()
			self.figure.canvas.restore_region( self.background )
			for graph in list_of_graphs:
				self.ax.draw_artist( graph )
			self.figure.canvas.blit( self.figure.bbox )
			self.figure.canvas.flush_events()
		# self.ani = animation.FuncAnimation(self.figure, run_func_return_graphs, blit=True, interval=update_interval_ms,
		#                       repeat=True)
		return redraw_graphs

	def add_new_data_point( self, x, y ):
		self.newest_data = (x,y)
		self.current_graph_data.append( (x, y) )
		self.ax.autoscale_view(True,True,True)

	def plot_finished( self, x_data, y_data ):
		self.ani._stop()
		self.running_graph.remove()
		self.current_graph.set_data( x_data, y_data )
		self.ax.relim()
		#self.ax.autoscale_view()
		self.ax.autoscale_view(True,True,True)
		self.figure.tight_layout()
		self.canvas.draw()
		self.canvas.show()

		# try:
		# 	z = np.polyfit(y_data, x_data, 1)
		# 	print( f"Resistance: {z[0]:g}, Offset: {z[1]:g}")
		# except Exception as e:
		# 	print( e )

	def clear_all_plots( self ):
		for graph in self.all_graphs:
			graph.remove()
		self.all_graphs.clear()
		# self.current_graph = None
		# self.running_graph = None


