import matplotlib.pyplot as plt
import scipy.stats as stats
import matplotlib.patches as mpatches
import numpy as np
import csv

class auto_draw:
	def __init__(self, stare_posi):
		self.columns = []
		self.as_dict = None
		self.stare_posi = stare_posi
		self.color = 'r'

	def read(self, file):
		with open(file) as csvfile:
		    readCSV = csv.reader(csvfile, delimiter=',')
		    for row in readCSV:
		        if self.columns:
		            for i, value in enumerate(row):
		                self.columns[i].append(int(value))
		        else:
		            # first row
		            self.columns = [[value] for value in row]

		# you now have a column-major 2D array of your file.
		self.as_dict = {c[0] : c[1:] for c in self.columns}

	def finish(self, plt, address):
		red_patch = mpatches.Patch(color='red', label='dly')
		blue_patch = mpatches.Patch(color='blue', label='cue')
		green_patch = mpatches.Patch(color='green', label='vgs')
		c_patch = mpatches.Patch(color='c', label='mgs')
		black_patch = mpatches.Patch(color='black', label='zscore')

		plt.legend(handles=[red_patch, blue_patch, green_patch, c_patch])
		plt.grid()
		plt.savefig(address)
		plt.close()

	def draw_x(self, address, J = False):
		plt.ylabel('X')
		plt.xlabel('Label')
		limit = len(self.as_dict['sample'])
		z_score = stats.zscore(self.as_dict['x'])
		current = 0
		mgs_prev = 0
		plt.plot(self.as_dict['sample'], z_score, 'black')
		#Add legend
		#Specify the colors
		while(1):
			self.color = 'c'
			if self.stare_posi['cue'][current] < limit:
				plt.plot(self.as_dict['sample'][int(mgs_prev):int(self.stare_posi['cue'][current])], self.as_dict['x'][int(mgs_prev):int(self.stare_posi['cue'][current])], self.color)
			else:
				plt.plot(self.as_dict['sample'][int(mgs_prev):int(limit)], self.as_dict['x'][int(mgs_prev):int(limit)], self.color)
				self.finish(plt, address)
				return
			self.color = 'b'
			if self.stare_posi['vgs'][current] < limit:
				plt.plot(self.as_dict['sample'][int(self.stare_posi['cue'][current]):int(self.stare_posi['vgs'][current])], self.as_dict['x'][int(self.stare_posi['cue'][current]):int(self.stare_posi['vgs'][current])], self.color)
			else:
				plt.plot(self.as_dict['sample'][int(self.stare_posi['cue'][current]):int(limit)], self.as_dict['x'][int(self.stare_posi['cue'][current]):int(limit)], self.color)
				self.finish(plt, address)
				return
			self.color = 'g'
			if self.stare_posi['dly'][current] < limit:
				plt.plot(self.as_dict['sample'][int(self.stare_posi['vgs'][current]):int(self.stare_posi['dly'][current])], self.as_dict['x'][int(self.stare_posi['vgs'][current]):int(self.stare_posi['dly'][current])], self.color)
			else:
				plt.plot(self.as_dict['sample'][int(self.stare_posi['vgs'][current]):int(limit)], self.as_dict['x'][int(self.stare_posi['vgs'][current]):int(limit)], self.color)
				self.finish(plt, address)
				return
			self.color = 'r'
			if self.stare_posi['mgs'][current] < limit:
				plt.plot(self.as_dict['sample'][int(self.stare_posi['dly'][current]):int(self.stare_posi['mgs'][current])], self.as_dict['x'][int(self.stare_posi['dly'][current]):int(self.stare_posi['mgs'][current])], self.color)
			else:
				plt.plot(self.as_dict['sample'][int(self.stare_posi['dly'][current]):int(limit)], self.as_dict['x'][int(self.stare_posi['dly'][current]):int(limit)], self.color)
				self.finish(plt, address)
				return
			current += 1
			mgs_prev = self.stare_posi['mgs'][current-1]

		self.finish(plt, address)

	def draw_y(self, address, J = False):
		plt.ylabel('Y')
		plt.xlabel('Label')
		z_score = stats.zscore(self.as_dict['y'])
		plt.plot(self.as_dict['sample'], z_score, 'black')
		plt.plot(self.as_dict['sample'], self.as_dict['y'], self.color, label = 'y')

		self.finish(plt, address)

	def draw_r(self, address, J = False):
		plt.ylabel('R')
		plt.xlabel('Label')
		z_score = stats.zscore(self.as_dict['r'])
		plt.plot(self.as_dict['sample'], z_score, 'black')
		plt.plot(self.as_dict['sample'], self.as_dict['r'], self.color, label = 'r')

		self.finish(plt, address)

	def draw_blink(self, address, J = False):
		plt.ylabel('blink')
		plt.xlabel('Label')
		plt.plot(self.as_dict['sample'], self.as_dict['blink'], label = 'blink')

		self.finish(plt, address)

