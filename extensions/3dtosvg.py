#!/usr/bin/env python
# -*- coding: utf-8 -*-

# BADLY NEEDS A REWRITE!

help = '''
Copyright (C) 2008 Thomas Holder, http://sf.net/users/speleo3/
Distributed under the terms of the GNU General Public License v2

Modified by Mateusz Golicz in 04.2013, 11.2013, 08.2016.

Converts Survex 3D files (*.3d) to SVG.
Usage: python 3dtosvg.py [OPTIONS] FILE.3d

  --scale=ARG        Import with a scale of 1:ARG (default 100)
  --view=[0,1,2]     0: Plan (default), 1: Profile, 2: Extend
  --bearing=[0-359]  Bearing in degrees north (default 0)
  --path=ARG         Control generation of centerline. Use 'none', 'plain',
                     'circle-marked' or 'triangle-marked'
  --stations=ARG     Control generation of stations. Use 'none', 'just-name',
                     'triangle-clones', 'labeled-triangle-clones', 'caveink-groups'
  --dpi=ARG          Resolution in DPI (default 90)
  --extend-cmd=ARG   The "extend" program is part of Survex and required
                     for --view=2. If it is not found inside PATH, you may
                     specify the absolute path for the binary with ARG.
                     Example: --extend-cmd="C:\Programme\Survex\extend.exe"
                     Example: --extend-cmd="/usr/local/bin/extend"
  --scalebar=[0,1]   1: Draw scalebar
  --annotate=[0,1]   1: Annotate for Therion Export
  --filter=prefix    Filter by label prefix and trim prefix off (TODO: implement and check therion book)

If you select extend view and there is a *.espec file with same
basename as the *.3d file, it will be passed to the extend binary
with the --specfile option. See "extend" manpage for details.

Related:
 * http://survex.com/
 * http://trac.survex.com/browser/trunk/doc/3dformat.htm

Changelog:
 * 2011-01-23: New args use_inkscape_label, use_therion_attribs
 * 2013-04-20: Each survey traverse becomes a separate path
 * 2013-04-20: Groupping of SVG paths accordingly to perfix hierarchy
 * 2013-11-26: Support for v8 Survex format. Now it became really filthy code!
 * 2016-08-30: Added support for station markers compatible with other caveink extensions
               Removed --marker and --stationnames in favour of --stations and --path
'''

import sys, math, os

args = {
	'scale': 100,
	'view': 0,
	'bearing': 0,
	'dpi': 90,
	'extend-cmd': 'extend',
	'scalebar': 1,
	'stations': 'caveink-groups',
	'path': 'plain',
	'annotate': 1,
	'use_inkscape_label': 1,
	'use_therion_attribs': 0,

	'filter': '',
}

infile = ''

# from th2ex
def name_survex2therion(name):
	x = name.split('.')
	if len(x) == 1:
		return name
	return x[-1] + '@' + '.'.join(reversed(x[:-1]))

def die(msg):
	sys.stderr.write(msg + "\n")
	sys.stderr.write(help)
	sys.exit(1)

sys.argv.pop(0)
for arg in sys.argv:
	if arg.startswith('--'):
		pair = arg[2:].split('=', 2)
		if pair[0] == 'filter':
			pass
		elif pair[1].isdigit():
			pair[1] = int(pair[1])
		elif pair[1] == 'true':
			pair[1] = 1
		elif pair[1] == 'false':
			pair[1] = 0
		args[pair[0]] = pair[1]
	else:
		infile = arg

args['use_inkscape_label'] *= args['annotate']
args['use_therion_attribs'] *= args['annotate']
filter_len = len(args['filter'])

if len(infile) == 0:
	die("no filename given")

if args['view'] == 2:
	if not infile.endswith('_extend.3d'):
		command = args['extend-cmd'] + ' "' + infile + '"'
		if os.path.exists(infile[:-3] + '.espec'):
			command += ' --specfile="' + infile[:-3] + '.espec"'
		pipe = os.popen(command)
		if pipe.close() != None:
			die("extend failed")
		infile = infile[:-3] + '_extend.3d'
	args['bearing'] = 0

f = open(infile, 'rb')

line = f.readline() # File ID
if not line.startswith('Survex 3D Image File'):
	die("not a Survex 3D File, aborting")

line = f.readline() # File format version
assert line[0] == 'v'
ff_version = int(line[1:])

line = unicode(f.readline(), 'latin1') # Survex title
if line.rstrip().endswith(' (extended)'):
	args['view'] = 2
	args['bearing'] = 0

line = f.readline() # Timestamp

_cos = math.cos(math.radians(args['bearing']))
_sin = math.sin(math.radians(args['bearing']))

paths = {'': []}
hierarchy = {}
curr_label = ''
curr_path = paths['']
curr_path_label = curr_label
curr_splay = False
last_xyz = [0, 0]
labels = {}

min_x = 1000000000
max_x = -min_x
min_y = min_x
max_y = -min_y

def read_xyz():
	x = read_int(4, 1)
	y = read_int(4, 1)
	z = read_int(4, 1)
	if args['bearing']:
		global _cos, _sin
		[ x, y ] = [ x * _cos - y * _sin, x * _sin + _cos * y ]
	if args['view'] > 0:
		[ y, z ] = [ z, y ]
	return [ x, -y, z ]

def read_int(len, sign):
	int = 0
	for i in range(len):
		int |= read_byte() << (8 * i)
	if sign and (int >> (8 * len - 1)):
		int -= (1 << 8 * len)
	return int

def read_len():
	len = read_byte()
	if len == 0xfe:
		len += read_int(2, 0)
	elif len == 0xff:
		len = read_int(4, 0)
	return len

def read_label():
	len = read_len()
	if len > 0:
		global curr_label
		curr_label += skip_bytes(len)

def read_v8label(common_flag, common_val):
	global curr_label
	if common_flag:
		if common_val == 0: return 0
		cadd = common_val
		cdel = common_val
	else:
		ch = read_byte()
		if ch != 0:
			cdel = ch >> 4
			cadd = ch & 0xf
		else:
			ch = read_byte()
			if ch != 0xff:
				cdel = ch
			else:
				cdel = read_int(4, 0)

			ch = read_byte()
			if ch != 0xff:
				cadd = ch
			else:
				cadd = read_int(4, 0)
				
	if cdel:
		debug_3d(0, " trim label by " + str(cdel))
		curr_label = curr_label[:-cdel]
	
	if cadd:
		string = skip_bytes(cadd)
		debug_3d(0, " expand label by " + str(cadd) + ": " + string)
		curr_label += string
				

def skip_bytes(n):
	return f.read(n)

def read_byte():
	byte = f.read(1)
	if len(byte) != 1:
		return -1
	return ord(byte)

def update_hierarchy(h, label):
	current_h = h
	for p in label.split('.'):
		if not p in current_h:
			current_h[p] = {}
		current_h = current_h[p]
	return h		

def debug_3d(byte, msg):
	pass
#	print ("%02x (%02d): %s") % (byte, byte, msg)



if ff_version == 8:
	while 1:
		byte = read_byte()
		debug_3d(byte, "... processing")
		mode = ""
		if byte == -1:
			break
		
		if (byte >> 6) == 0:
			if byte <= 4:
				debug_3d(byte, "EOD/STYLE")
				# End of data or style
				pass
			elif byte == 0x10:
				debug_3d(byte, "DATE INFO1")
				# No date info
				pass
			elif byte == 0x11:
				debug_3d(byte, "DATE INFO2")
				# Date1
				skip_bytes(2)
			elif byte == 0x12:
				debug_3d(byte, "DATE INFO3")
				# Date2
				skip_bytes(3)
			elif byte == 0x13:
				debug_3d(byte, "DATE INFO4")
				# Date3
				skip_bytes(3)
			elif byte == 0x1f:
				debug_3d(byte, "ERROR INFO")
				# error info
				skip_bytes(5 * 4)
			elif byte == 0x30 or byte == 0x31:
				read_v8label(0, 0)
				debug_3d(byte, "LRUD")
				# LRUD
				skip_bytes(4 * 2)
			elif byte == 0x30 or byte == 0x31:
				read_v8label(0, 0)
				debug_3d(byte, "BIG LRUD")
				# BIG LRUD
				skip_bytes(4 * 4)
			elif byte == 0x0f:
				# MOVE
				xyz = read_xyz()

				debug_3d(byte, "MOVETO " + str(xyz[0]) + ", " + str(xyz[1]) + ", " + str(xyz[2]))
				last_xyz = xyz[:]

				# Create new label next time a line is produced 
				curr_path_label = '..'
			else:
				# Wrong, error
				debug_3d(byte, "WRONG!")
				pass
		elif byte >= 0x80:
			read_v8label(0, 0)
			xyz = read_xyz()
			debug_3d(byte, "LABEL " + curr_label + " " + str(xyz[0]) + ", " + str(xyz[1]) + ", " + str(xyz[2]))
			if filter_len == 0:
				labels[curr_label] = xyz[0:2]
			elif curr_label.startswith(args['filter']):
				tmp_label = curr_label[filter_len:]
				labels[tmp_label] = xyz[0:2]
		elif (byte >> 6) == 1:
			# LINE
			read_v8label(byte & 0x20, 0)
			splay = True if (byte & 0x04) else False;
			if curr_label != curr_path_label or splay != curr_splay:
				# Create new label and new path
				curr_splay = splay
				curr_path_label = curr_label
				curr_path = ['S' if splay else 'M', last_xyz[0], last_xyz[1]]
				if not curr_label in paths:
					paths[curr_label] = []
				update_hierarchy(hierarchy, curr_label)
				paths[curr_label].append(curr_path)
			
			xyz = read_xyz()
			last_xyz = xyz[:]

			curr_path.append('L')
			curr_path.append(xyz[0])
			curr_path.append(xyz[1])

			debug_3d(byte, "LEG " + curr_label + " " + str(xyz[0]) + ", " + str(xyz[1]) + ", " + str(xyz[2]))

			if (min_x > xyz[0]): min_x = xyz[0]
			if (max_x < xyz[0]): max_x = xyz[0]
			if (min_y > xyz[1]): min_y = xyz[1]
			if (max_y < xyz[1]): max_y = xyz[1]
		else:
			# Wrong
			debug_3d(byte, "WRONG!")
			pass
					




else:
	while 1:
		byte = read_byte()
		if byte == -1:
			break
		
		if byte == 0x00:
			# STOP
			debug_3d(byte, "STOP")
			curr_label = ''
		elif byte <= 0x0e:
			# TRIM
			(i,n) = (-16,0)
			
			while n < byte:
				i -= 1
				if curr_label[i] == '.': n += 1
			curr_label = curr_label[:i + 1]

			debug_3d(byte, "TRIM: " + curr_label)
		elif byte <= 0x0f:
			# MOVE
			xyz = read_xyz()

			debug_3d(byte, "MOVETO " + str(xyz[0]) + ", " + str(xyz[1]) + ", " + str(xyz[2]))
			last_xyz = xyz[:]

			# Create new label next time a line is produced 
			curr_path_label = '..'
			
		elif byte <= 0x1f:
			# TRIM
			curr_label = curr_label[:15 - byte]
			debug_3d(byte, "TRIM " + str(15 - byte) + ": " + curr_label)
		elif byte <= 0x20:
			debug_3d(byte, "DATE1")
			# DATE
			if ff_version < 7:
				skip_bytes(4)
			else:
				skip_bytes(2)
		elif byte <= 0x21:
			debug_3d(byte, "DATE2")
			# DATE
			if ff_version < 7:
				skip_bytes(8)
			else:
				skip_bytes(3)
		elif byte <= 0x22:
			debug_3d(byte, "Error info")
			# Error info
			skip_bytes(5 * 4)
		elif byte <= 0x23:
			debug_3d(byte, "DATE")
			# DATE
			skip_bytes(4)
		elif byte <= 0x24:
			debug_3d(byte, "DATE")
			# DATE
			continue
		elif byte <= 0x2f:
			debug_3d(byte, "RSVD")
			# Reserved
			continue
		elif byte <= 0x31:
			debug_3d(byte, "XSECT")
			# XSECT
			read_label()
			skip_bytes(4 * 2)
		elif byte <= 0x33:
			debug_3d(byte, "XSECT")
			# XSECT
			read_label()
			skip_bytes(4 * 4)
		elif byte <= 0x3f:
			debug_3d(byte, "RSVD")
			# Reserved
			continue
		elif byte <= 0x7f:
			# LABEL
			read_label()
			xyz = read_xyz()
			debug_3d(byte, "LABEL " + curr_label + str(xyz[0]) + ", " + str(xyz[1]) + ", " + str(xyz[2]))
			if filter_len == 0:
				labels[curr_label] = xyz[0:2]
			elif curr_label.startswith(args['filter']):
				tmp_label = curr_label[filter_len:]
				labels[tmp_label] = xyz[0:2]
		elif byte <= 0xbf:
			# LINE
			read_label()
			splay = True if (byte & 0x04) else False;
			if curr_label != curr_path_label or splay != curr_splay:
				# Create new label and new path
				curr_splay = splay
				curr_path_label = curr_label
				curr_path = ['S' if splay else 'M', last_xyz[0], last_xyz[1]]
				if not curr_label in paths:
					paths[curr_label] = []
				update_hierarchy(hierarchy, curr_label)
				paths[curr_label].append(curr_path)
			
			xyz = read_xyz()
			last_xyz = xyz[:]

			curr_path.append('L')
			curr_path.append(xyz[0])
			curr_path.append(xyz[1])

			debug_3d(byte, "LEG " + curr_label + str(xyz[0]) + ", " + str(xyz[1]) + ", " + str(xyz[2]))

			if (min_x > xyz[0]): min_x = xyz[0]
			if (max_x < xyz[0]): max_x = xyz[0]
			if (min_y > xyz[1]): min_y = xyz[1]
			if (max_y < xyz[1]): max_y = xyz[1]

		elif byte <= 0xff:
			debug_3d(byte, "RSVD")
			
			# Reserved
			continue

# extend
width = max_x - min_x;
height = max_y - min_y

scale = args['dpi'] / 2.54 / args['scale']

marker = {
	'circle-marked': 'url(#StationCircle)',
	'triangle-marked': 'url(#StationTriangle)',
}.get(args['path'], 'none')

style = [
	'fill:none',
	'stroke:#900',
	'stroke-width:' + str(args['scale'] / 50),
	'stroke-linecap:round',
	'stroke-linejoin:round',
	'marker-start:' + marker,
	'marker-mid:' + marker,
	'marker-end:' + marker,
]

splay_style = [
	'fill:none',
	'stroke:#900',
	'stroke-width:' + str(args['scale'] / 50 / 2),
	'stroke-linecap:round',
	'stroke-linejoin:round',
]

def print_path(coords):
	if coords[0] == 'S':
		s = splay_style
		coords[0] = 'M'
	else:
		s = style
		
	print '<path style="%s"' % (';'.join(s))
	if args['use_therion_attribs']:
		print '  therion:type="survey"'
	if args['use_inkscape_label']:
		print '  inkscape:label="line survey"'
	sys.stdout.write('d="')
	for i in range(0, len(coords), 3):
		sys.stdout.write(coords[i] + " " +
			str(coords[i + 1] - min_x) + "," +
			str(coords[i + 2] - min_y) + " ")
	sys.stdout.write('"');
	print ' />'

def print_points():
	prev = [ -1, -1 ]
	for label,xy in labels.iteritems():
		if xy == prev:
			continue
		label = name_survex2therion(label)
		print '<use transform="translate(%f,%f)" xlink:href="#point-station"' \
			% (xy[0] - min_x, xy[1] - min_y)
		if args['use_therion_attribs']:
			print '  therion:role="point" therion:type="station"'
		if args['use_inkscape_label']:
			print '  inkscape:label="point station -name %s" />' % (label)
		else:
			print '  inkscape:label="%s" />' % (label)
		prev = xy

def print_points_in_groups():
	prev = [ -1, -1 ]
	for label,xy in labels.iteritems():
		if xy == prev:
			continue
		print '<g transform="translate(%f,%f)"><use xlink:href="#point-station" />'  % (xy[0] - min_x, xy[1] - min_y)
		print '<text x="10" y="0">%s</text></g>' % label
		prev = xy


def print_stationnames():
	for label,xy in labels.iteritems():
		label = label.rsplit('.', 1)[-1]
		print '<text transform="translate(%f,%f) scale(%f) translate(4,2)"' \
			% (xy[0] - min_x, xy[1] - min_y, args['scale'] / 50)
		if args['use_therion_attribs']:
			print '  therion:role="point" therion:type="station-name"'
		if args['use_inkscape_label']:
			print '  inkscape:label="point station-name"'
		print '  >%s</text>' % (label)

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
<g	id="import"
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

def print_hierarchy(hname, h):
	if hname != '':
		hname += '.'
	for k, child in h.iteritems():
		label = hname + k
		print "<g id='%s'>" % label
		if label in paths:
			for p in paths[label]:
				print_path(p)
		print_hierarchy(label, child)
		print "</g>"

if args['path'] <> 'none':	
	print_hierarchy('', hierarchy)

if args['stations'] == 'triangle-clones' or args['stations'] == 'labeled-triangle-clones':
	print_points()
	if args['stations'] == 'labeled-triangle-clones': print_stationnames()
elif args['stations'] == 'caveink-groups':
	print "<g style='font-size: 30px'>"
	print_points_in_groups()
	print "</g>"
elif args['stations'] <> 'none':
	print_stationnames()

print '</g>'

if args['scalebar']:
	try:
		from render_scalebar import Scalebar
		scalebar = Scalebar(args['scale'], args['dpi'])
		print scalebar.get_xml()
	except:
		print "<text>Scalebar import failed</text>";

print "</svg>"
