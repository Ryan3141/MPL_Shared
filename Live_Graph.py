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

import matplotlib.cm as cm

class Live_Graph( QWidget ):
	def __init__(self, parent=None):
		super().__init__(parent=parent)

		self.current_graph_data = []
		self.current_graph = None
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
		#self.ax.plot( [1,2,3,4], [1,2,3,4], 'b-')
		self.all_graphs = []
		self.debug_counter = 0
		#self.current_graph, = self.ax.plot( [], [], 'b-')
		#self.canvas.show()

	def set_labels( self, title, x_label, y_label ):
		self.ax.set_xlabel( x_label )
		self.ax.set_ylabel( y_label )
		self.ax.set_title( title )
		self.figure.tight_layout()

	def close( self ):
		global needs_reload
		needs_reload = True
		del self.figure

	def new_plot( self ):
		#cm.get_cmap('seismic')(np.linspace(0, 1, 6)
		self.current_graph, = self.ax.plot( [], [], color=self.graph_colors[self.debug_counter])
		self.running_graph, = self.ax.plot( [], [], 'ro-' )
		self.debug_counter = (self.debug_counter + 1) % 10
		self.all_graphs.append( self.current_graph )
		#self.ax.set_xlim([50,100])
		self.current_graph_data = []
		self.newest_data = None
		self.ani = animation.FuncAnimation(self.figure, self.replot, blit=False, interval=10,
                              repeat=True)

	def replot( self, frame_number ):
		if self.figure == None:
			return
		if len( self.current_graph_data ) > 0:
			self.current_graph.set_data( *zip(*self.current_graph_data) )

		if self.newest_data is not None:
			self.running_graph.set_data( [self.newest_data[0]], [self.newest_data[1]] )
		# refresh canvas
		self.ax.relim()
		#self.ax.autoscale_view()
		#self.ax.autoscale(enable=True, axis='y')
		self.ax.autoscale_view(True,True,True)
		self.figure.tight_layout()
		#plt.pause(0.05)
		#self.canvas.draw()
		#self.canvas.show()
		return self.all_graphs + [self.running_graph]

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


