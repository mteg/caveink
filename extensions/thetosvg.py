#!/usr/bin/env python2
# -*- coding: utf-8 -*-

help = '''

Converts PocketTopo sketches, exported as Therion files (*.the) into SVG files.
Usage: python thetosvg.py [OPTIONS] FILE.the

  --scale=ARG        Import with a scale of 1:ARG (default 1000)
  --view=[0,1,2]     0: Plan (default), 1: Profile, 2: Extend
  --bearing=[0-359]  Bearing in degrees north (default 0)
  --markers=[0-2]    0: No station markers, 1: Display stations as small
                     circles (default), 2: ditto as triangles
  --station-names=[0,1]  Display station names? (default: 1)
  --font-size=N      Font size in points (default: 5pt)
  --splays=[0,1]     Display splay shots (default: 1)
  --dpi=ARG          Resolution in DPI (default 90)
  
Copyright (C) 2013 Mateusz Golicz
Uses code from 3dtosvg, which is Copyright (C) 2008 Thomas Holder, http://sf.net/users/speleo3/

Distributed under the terms of the GNU General Public License v2
'''

import sys, math, os, string

class TheFile:
	'''
	Class for handling Pocket Topo Therion Export files

	Contains a file reading routine (in the object initializer),
	as well as code to generate projected elevation from extended
	elevation
	'''
	def __init__(self, infile, bearing = 0):			
		# Prototype extent dictionary
		self.ex = {'min-x': 1000000000, 'min-y': 1000000000, 'max-x': -1000000000, 'max-y': -1000000000}

		self.shots = []
		# List of shots between stations in form of tuples (from, to)

		self.drawings = {'PLAN': {'shots': [], 'stations': {}, 'all_stations': [], 'sset': [], 'lines': {}, 'extent': dict(self.ex)},
			    'ELEVATION': {'shots': [], 'stations': {}, 'all_stations': [], 'sset': [], 'lines': {}, 'extent': dict(self.ex)}}
		# Drawing structure
		# For every drawing, it holds:
		#  sset - List of all ORIGINAL station coordinates, as occuring in the drawing 
		#         Used to identify which shots are MAIN centerline shots (ie. between two stations)
		#         as opposed to splay shots
		#  stations - Dictionary of TRANSFORMED station coordinates (ie. station name -> (x, y))
		#  extent - Drawing extent (bounding box) in a structure as above
		#  shots - List of lines representing measurement shots, as tuples of four pairs:
		#          ((ox1, oy1), (ox2, oy2), (x1, y1), (x2, y2))
		#          ox1, oy1 - ox2, oy2 are the original coordinates defining a shot
		#          (that can then be related to the sset list)
		#          x1, y1 - x2, y2 are the transformed (rotated to view bearing) coordinates
		# lines - a dictionary relating line COLOR to line list
		#          ie. lines["BLACK"] contains a list of all black lines
		#          every line is a a simple list of transformed line coordinates
		#          eg. lines["BLACK"] = [ [(x, y), (x, y), ...], [(x, y), (x, y), ...], ...]

		mode = ""
		# This is a FSM state variable that 
		# holds the name of .the file section that is currently parsed

		# Let's read the drawing file
		f = open(infile, 'rb')

		# For every line
		for l in f.readlines():
			# Remove unnecessary white space characters
			l = l.strip()
			if len(l) == 0: 
				# Empty line
				continue
			if l in ("PLAN", "ELEVATION"):
				# Now let's direct input to a particular drawing
				drawing = self.drawings[l]
				
				# Compute rotation coefficients for the set bearing
				if l == "PLAN":
					# Compute rotation coefficients
					self._cos = math.cos(math.radians(bearing))
					self._sin = math.sin(math.radians(bearing))
				else:
					# Do not rotate anything in the elevation view
					self._cos = 1
					self._sin = 0

			elif l in ("STATIONS", "SHOTS", "DATA"):
				# Sub-sections of a drawing
				mode = l
			elif l.startswith("POLYLINE"):
				# Polyline within a drawing
				mode, color = l.split(" ")
				
				if not color in drawing['lines']:
					# Define a new color
					drawing['lines'][color] = []

				# Define a new line
				line = []
				drawing['lines'][color].append(line)
			elif l[0] in string.ascii_letters:
				# Unsupported file section
				mode = "" 
			else:
				# Line starts not with an alphanumeric character
				# Assuming it is data, depending on current file section let's process accordingly
				if mode == "STATIONS":
					# Station marks
					line = l.split("\t")
					if len(line) == 3:
						x, y, n = line

						# Add station coordinates to station set
						drawing['sset'].append((x.strip(), y.strip()))
						
						# Rotate station coordinates to specified view bearing
						x, y = self.rot(x, y)
						
						# Update image extent
						self.update_extent(drawing['extent'], x, y)

						# Identically named stations may be specified multiple times
						# eg. in case there are cross-sections put on the drawing
						n = n.strip()
						if n not in drawing['stations']:
							drawing['stations'][n] = (x, y)
						drawing['all_stations'].append((n, x, y))
				elif mode == "SHOTS":
					# Shot data, ie. coordinates defining a line
					# either between centerline station
					# or a centerline station and an unnamed splay 
					# measurement station

					x1, y1, x2, y2 = l.split("\t")
					
					# We need to store both the original
					# coordinates (id1 and id2), as well
					# as transformed coordinates ((x1, y1), (x2, y2))
					
					id1 = (x1.strip(), y1.strip())
					id2 = (x2.strip(), y2.strip())
					x1, y1 = self.rot(x1, y1)
					x2, y2 = self.rot(x2, y2)
					self.update_extent(drawing['extent'], x1, y1)
					self.update_extent(drawing['extent'], x2, y2)
					
					drawing['shots'].append((id1, id2, (x1, y1), (x2, y2)))
				elif mode == "POLYLINE":
					# Subsequent coordinates of a polyline
					x, y = l.split("\t")
					
					# Parse, transform and store
					x, y = self.rot(x, y)
					self.update_extent(drawing['extent'], x, y)
					line.append((x, y))
				elif mode == "DATA":
					# Survey data: From/To/Compass/Clino/Tape
					a = l.split("\t")
					
					# If all is well...
					if len(a) >= 5:
						fr, to = a[0].strip(), a[1].strip()
						# If this is a centerline shot...
						if len(to):
							# Store this shot
							self.shots.append((fr, to))

	def rot(self, x, y):
		'''
		Rotate a point to configured view bearing
		'''
		x = float(x)
		y = float(y)
		return x * self._cos - y * self._sin, x * self._sin + self._cos * y

	def update_extent(self, extent, xp, yp):
		'''
		Update extent, taking point (xp, yp) under account
		'''
		extent['min-x'] = min(extent['min-x'], xp)
		extent['min-y'] = min(extent['min-y'], yp)
		extent['max-x'] = max(extent['max-x'], xp)
		extent['max-y'] = max(extent['max-y'], yp)


	def gp_clip(self, x0, x1, y1, x2, y2):
		'''
		Helper function for generating a projected elevation
		from extended elevation.
		
		Computes coordinates of line defined
		by (x1, y1) - (x2, y2) at x = x0
		'''
		y = y1 + (y2 - y1) / (x2 - x1) * (x0 - x1)
		return (x0, y)

	def gp_transform_point(self, dir, src_xs, src_xe, dst_xs, dst_xe, x):
		'''
		Helper function for generating a projected elevation
		from extended elevation.
		
		Transforms proportionally x defined in range (src_xs, src_xe)
		into x defined in (dst_xs, dst_xe), flipping if necessary
		'''
		x -= src_xs
		if src_xe  == src_xs:
			src_xe += 0.001
		x /= src_xe - src_xs
		x *= dst_xe - dst_xs

		if dir > 0:
			x += dst_xs
		else:
			x = dst_xe - x
		
		return x

		

	def gp_transform(self, dir, x1, y1, x2, y2, src_xs, src_xe, dst_xs, dst_xe):
		'''
		Helper function for generating a projected elevation from
		extended elevation.
		
		Transforms a polyline segment (x1, y1) - (x2, y2) from a
		coordinate system in slice defined by x = src_xs ... src_ys
		into slice contained between x = dst_xs ... dst_xe
		
		Only the first (x) coordinate is altered.
		'''

		# Normalize line segment - ensure that always x1 < x1
		if x1 > x2: x1, y1, x2, y2 = x2, y2, x1, y1

		# Sort out segments not intersecting current slice
		if x1 > src_xe: return [0, (0, 0), (0, 0)]
		if x2 < src_xs: return [0, (0, 0), (0, 0)]

		# Clip line segment to this slice
		if x1 < src_xs: (x1, y1) = self.gp_clip(src_xs, x1, y1, x2, y2)
		if x2 > src_xe: (x2, y2) = self.gp_clip(src_xe, x1, y1, x2, y2)
			
		# Transform line segment to new coordinate system
		x1 = self.gp_transform_point(dir, src_xs, src_xe, dst_xs, dst_xe, x1)
		x2 = self.gp_transform_point(dir, src_xs, src_xe, dst_xs, dst_xe, x2)

		# Return new coordinates
		return [1, (x1, y1), (x2, y2)]

	def gen_projected(self):
		'''
		Generate projected elevation from extended elevation
		
		The plan drawing is also used to determine projected leg
		lengths (actually, their horizontal extents) in
		the resulting drawing.
		'''
		
		shots = self.shots
		drawings = self.drawings
		
		# Prepare new drawing structure
		d = {"shots": [], "stations": {}, "sset": drawings["ELEVATION"]["sset"], "lines": {}, 'extent': dict(self.ex)}

		# For every shot - ie. for every slice of the extended elevation
		for fr, to in shots:
			try:
				# Retrieve station coordinates on the extended elevation drawing
				src_x1, fr_y = drawings["ELEVATION"]["stations"][fr]
				src_x2, to_y = drawings["ELEVATION"]["stations"][to]

				# Retrieve X station coordinates on the PLAN drawing
				dst_x1 = drawings["PLAN"]["stations"][fr][0]
				dst_x2 = drawings["PLAN"]["stations"][to][0]
			except:
				# No such station in one of the drawings!
				continue
			
			
			# The idea is to translate and stretch (only in the X axis)
			# the slice of the elevation drawing contained between
			# src_x1 - src_x2 to fit x = dst_x1 - dst_x2
			
			# The station coordinates on the new drawing will be as follows
			d["stations"][fr] = (dst_x1, fr_y)
			d["stations"][to] = (dst_x2, to_y)
			
			# We may need to flip the whole slice, dir = -1 in that case
			# or dir = 1 if the shot runs in the same direction on both
			# drawings
			dir = math.copysign(1, (src_x2 - src_x1) * (dst_x2 - dst_x1))
			
			# Let's normalize the slice coordinates
			src_xs = min(src_x1, src_x2)
			src_xe = max(src_x1, src_x2)
			dst_xs = min(dst_x1, dst_x2)
			dst_xe = max(dst_x1, dst_x2)
			
			# src_xs < src_xe = Source slice coordinates
			# dst_xs < dst_xe = Destination slice coordinates
			
			# Transform shots
			for id1, id2, (x1, y1), (x2, y2) in drawings["ELEVATION"]["shots"]:
				# For every shot
				# Transform the shot
				s, (x1, y1), (x2, y2) = self.gp_transform(dir, x1, y1, x2, y2, src_xs, src_xe, dst_xs, dst_xe)
				if s:
					# ... include in the drawing only if the shot is within slice
					self.update_extent(d["extent"], x1, y1)
					self.update_extent(d["extent"], x2, y2)
					
					# store as in case of other drawings
					d["shots"].append((id1, id2, (x1, y1), (x2, y2)))
			
			# Transform lines
			for color, line_list in drawings["ELEVATION"]["lines"].iteritems():
				# For every line color
			
				# Define the color in the new drawing
				if not color in d["lines"]:
					d["lines"][color] = []
			
				# For every line of this color, in the source drawing
				for line in line_list:
					# Mark that no segment has been read yet
					x1 = y1 = None
					
					# For every coordinate of that line
					for x2, y2 in line:
						# If this is not the the first coordinate - we have a line segment (x1, y1) - (x2, y2)
						if x1 != None:
							# Transform this line segment
							s, p1, p2 = self.gp_transform(dir, x1, y1, x2, y2, src_xs, src_xe, dst_xs, dst_xe)
							
							if s:
								# Include only if is within the slice
								d["lines"][color].append([p1, p2])
								self.update_extent(d["extent"], p1[0], p1[1])
								self.update_extent(d["extent"], p2[0], p2[1])
						
						x1, y1 = x2, y2
					
		self.drawings["PROJECTED"] = d

if __name__ != '__main__':
	sys.exit(0)

# Default arguments
args = {
	'scale': 1000,
	'view': 0,
	'bearing': 0,
	'markers': 1,
	'dpi': 90,
	'station-names': 1,
	'font-size': 5,
	'splays': 1,

}

# Fatal error reporting function
def die(msg):
	sys.stderr.write(msg + "\n")
	sys.stderr.write(help)
	sys.exit(1)

infile = ''

# Parse arguments into args[] dictionary
sys.argv.pop(0)
for arg in sys.argv:
	if arg.startswith('--'):
		pair = arg[2:].split('=', 2)
		if pair[1].isdigit():
			pair[1] = int(pair[1])
		elif pair[1] == 'true':
			pair[1] = 1
		elif pair[1] == 'false':
			pair[1] = 0
		args[pair[0]] = pair[1]
	else:
		infile = arg

if len(infile) == 0:
	die("No filename was given")

# Read the input file
d = TheFile(infile, args["bearing"])

# will be transforming meters to millimeters
args['scale'] /= 1000.0
scale = args['dpi'] / 25.4 / args['scale']

# Path style shorthand
style = [
	'fill:none',
	'stroke-linecap:round',
	'stroke-linejoin:round',
]

style = ';'.join(style)

if args['view'] == 0:
	drawing = d.drawings["PLAN"]
elif args['view'] == 2:
	drawing = d.drawings["ELEVATION"]
else:
	d.gen_projected()
	drawing = d.drawings["PROJECTED"]

extent = drawing['extent']
width = extent['max-x'] - extent['min-x']
height = extent['max-y'] - extent['min-y']


# Output the SVG header

print """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
	xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
	xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
	xmlns:xlink="http://www.w3.org/1999/xlink"
	xmlns:therion="http://therion.speleo.sk/therion"
	width="%f"
	height="%f">
<sodipodi:namedview
	inkscape:document-units="mm"
	units="mm" />
<defs>
	<symbol id="point-station-0">
		<path
			d="M -1.8,1 1.8,1 0,-2 -1.8,1 z"
			style="fill:white;stroke-width:0.4;stroke-linejoin:miter;fill-opacity:0.5" />
		<path
			d="M 0,0 0,0"
			style="fill:none;stroke-width:0.7;stroke-linecap:round" />
	</symbol>
	<marker style="overflow:visible" id="StationCircle">
		<circle r="2"
			style="fill:none;stroke:#666;stroke-width:0.7" />
	</marker>
	<marker style="overflow:visible" id="StationTriangle">
		<use xlink:href="#point-station-0" style="stroke:#666" transform="scale(1.5)" />
	</marker>
	<symbol id="point-station" transform="scale(%f)">
		<use xlink:href="#point-station-0" style="stroke:black" />
	</symbol>
</defs>
<g id="pocket_topo"
	style="font-size:10"
	transform="scale(%f)">
	<!-- imported with scale 1:%d from %s -->
""" % (
		width * scale,
		height * scale,
		1.0 / scale,
		scale,
		args['scale'],
		'file', # UTF-8 containing file names causing problems!
	)

def print_path(c):
	'''
	Print an SVG path
	
	c - list of path coordinates
	'''
	if len(c) < 2:
		return
	print '<path d="',
	print "M %.2f,%.2f" % (c[0][0] - extent['min-x'], -c[0][1] + extent['max-y']),
	for i in c[1:]:
		print " L %.2f,%.2f" % (i[0] - extent['min-x'], -i[1] + extent['max-y']),
	print '" />'

def print_stationnames(s):
	'''
	Print station names
	s - dictionary of stations (name => (x,y)) 
	'''
	for (label, x, y) in s:
		print '<text style="font-size: %spt;" transform="translate(%.2f,%.2f) scale(%f) translate(4,2)"' \
			% (args["font-size"], x -extent['min-x'], -y + extent['max-y'], 1 / scale)
		print '  >%s</text>' % (label)


# Prepare shots for printing

# Will split shots into separate lists of centerline and splay shots
stations = set(drawing["sset"])
shots_centerline = []
shots_splay = []

for id1, id2, s1, s2 in drawing["shots"]:
	# SVG code for this shot
	shot = "<path d='M %.2f,%.2f L %.2f,%.2f' />" % (s1[0] - extent['min-x'], -s1[1] + extent['max-y'],
				s2[0] - extent['min-x'], -s2[1] + extent['max-y']) 
	if (id1 in stations) and (id2 in stations):
		# Shot between stations?
		shots_centerline.append(shot)
	else:
		# Shot between station and non-station
		shots_splay.append(shot)

print "<g id='shots'>";

# Output centerline shots
marker = {
	1: 'url(#StationCircle)',
	2: 'url(#StationTriangle)',
}.get(args['markers'], 'none')

centerline_style = ';'.join([
	'marker-start:' + marker,
	'marker-mid:' + marker,
	'marker-end:' + marker])

print "<g id='shots_centerline' style='stroke: red; stroke-width: %s; %s; %s'>" % (str(1 / scale), style, centerline_style)
print "".join(shots_centerline)
print "</g>"

if args["splays"]:
	# Output splay shots
	print "<g id='shots_splay' style='stroke: #f88; stroke-width: %s; %s'>" % (str(0.5 / scale), style)
	print "".join(shots_splay)
	print "</g>"

# End shots
print "</g>"

# Output station names
if args["station-names"]:
	print "<g id='station_names'>"
	print_stationnames(drawing["all_stations"])
	print "</g>"

# Output strokes (polylines)
for k, v in drawing["lines"].iteritems():
	print "<g style='stroke: %s; stroke-width: %smm; %s' id='stroke_%s'>" % (k.lower(), str(0.1 / scale), style, k)
	for l in v:
		print_path(l)
	print "</g>"

print '</g>'
print "</svg>"
