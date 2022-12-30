#from PyQt5.QtChart import QChart, QChartView, QLineSeries, QDateTimeAxis, QValueAxis
from PyQt5.QtGui import QPolygonF, QPainter, QBrush, QGradient, QLinearGradient, QColor, QFont, QPen
from PyQt5.QtCore import Qt, QDateTime, QDate, QTime, QPointF
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout

# needs_reload = False
# from importlib import reload


import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
# import matplotlib.animation as animation

import numpy as np
import time

import matplotlib.cm as cm

class Graph( QWidget ):
	def __init__(self, parent=None):
		super().__init__(parent=parent)

		self.all_graphs = {}
		self.plot_names = []
		#self.graph_colors = cm.get_cmap('seismic')(np.linspace(0, 1, 10))
		self.graph_colors = cm.rainbow(np.linspace(0, 1, 10))
		self.current_color = 0
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
		self.ax2 = self.ax.twinx()
		self.figure.tight_layout()

	def set_labels( self, title, x_label, y_label ):
		self.ax.set_xlabel( x_label )
		self.ax.set_ylabel( y_label )
		self.ax.set_title( title )
		self.figure.tight_layout()

	def close( self ):
		# global needs_reload
		# needs_reload = True
		del self.figure

	def plot( self, plot_name : str, x_data, y_data, axis = 0 ):
		self.plot_names.append( plot_name )
		if not plot_name in self.all_graphs.keys():
			color = self.graph_colors[ self.current_color ]
			self.current_color = (self.current_color + 1) % len( self.graph_colors )
			if axis == 0:
				self.all_graphs[ plot_name ], = self.ax.plot( x_data, y_data, label=plot_name, color=color )
			else:
				self.all_graphs[ plot_name ], = self.ax2.plot( x_data, y_data, label=plot_name, color=color )
			self.ax.legend()
		else:
			self.all_graphs[ plot_name ].set_data( x_data, y_data )
		self.ax.relim()
		self.ax.autoscale_view(True,True,True)
		self.canvas.draw()
		self.canvas.show()


	def clear_all_plots( self ):
		for name, graph in self.all_graphs.items():
			graph.remove()
		self.all_graphs.clear()
		self.plot_names.clear()



