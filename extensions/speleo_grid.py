# -*- coding: utf-8 -*-
'''
Generate a grid for cave plan, with coordinates printed out

Copyright (C) 2013 Mateusz Golicz, http://jaskinie.jaszczur.org
Distributed under the terms of the GNU General Public License v2
'''

import math
import inkex
import simpletransform

class SpeleoEffect(inkex.Effect):
	'''
	Generic effect class, shared by other "speleo" effects
	'''
	def invert_transform(self, transform):
		'''
		Compute inverse of transform
		'''
		(a, b, c) = transform[0]
		(d, e, f) = transform[1]
		
		# Formulas for inverting a 3x3 matrix; see SVG specification for more details
		det = a*e - b*d
		inverse = [[e/det, -b/det, (b*f - c*e)/det], [-d/det, a/det, (c*d - a*f)/det]]
		
		return inverse	

	def get_transform(self, node):
		'''
		Recursively compute the composite transform
		that all parent nodes apply to a node
		'''
		if node == None:
			# Recursion stopping condition - we have
			# reached the document root
			
			# Return identity transform
			return [[1, 0, 0], [0, 1, 0]]
		
		# Get transform attached to this particular node
		m1 = simpletransform.parseTransform(node.get('transform'))
		
		# Get a combined transform from all parent nodes
		m2 = self.get_transform(node.getparent())
		
		# Combine these two transforms
		return simpletransform.composeTransform(m2, m1)
	
	def get_current_layer(self):
		'''
		Get the 'nearest' true layer
		'''
		layer = self.current_layer
		while True:
			groupmode = layer.get(inkex.addNS('groupmode', 'inkscape'))
			if groupmode == 'layer':
				break
			parent = layer.getparent()
			if parent == None:
				break
			layer = parent
		return layer
	

class SpeleoGrid(SpeleoEffect):
	def __init__(self):
		inkex.Effect.__init__(self)
		self.OptionParser.add_option("--spacing",
				action="store", type="float", 
				dest="spacing", default=50)
		self.OptionParser.add_option("--scale",
				action="store", type="float", 
				dest="scale", default=1000)
		self.OptionParser.add_option("--draw-coords",
				action="store", type="string", 
				dest="coords", default="none")
		self.OptionParser.add_option("--type",
				action="store", type="string", 
				dest="type", default="line")

	
	def effect(self):
		if self.options.coords == "rotate":
			rot = " rotate(270)"
		else:
			rot = ""
			
		try:
			id, obj = self.selected.popitem()
			try:
				x_center = float(obj.get("x"))
				y_center = float(obj.get("y"))
			except:
				x_center = 0
				y_center = 0
			
			tr = self.get_transform(obj)
			x_center += tr[0][2]
			y_center += tr[1][2]
		except:
			x_center = 0
			y_center = 0
		
		doc_w = self.unittouu(self.document.getroot().get('width'))
		doc_h = self.unittouu(self.document.getroot().get('height'))
		uu_spacing = self.options.spacing / self.options.scale * 1000.0 / 25.4 * 90.0
		
		x_start = x_center - math.floor(x_center / uu_spacing) * uu_spacing
		y_start = y_center - math.floor(y_center / uu_spacing) * uu_spacing
		num_x = int(math.ceil(doc_w / uu_spacing))
		num_y = int(math.ceil(doc_h / uu_spacing))

		layer = self.get_current_layer()
		g = inkex.etree.SubElement(layer, 'g')

		if self.options.coords != "none":
			cg = inkex.etree.SubElement(g, "g")
			g = inkex.etree.SubElement(g, "g")
			cg.set('style', 'stroke:none;font-size:10pt;fill:#888;text-anchor:end;text-align:end')

		g.set('style', 'stroke:#888;stroke-width:0.2mm')

		# Vertical lines and coordinates
		for x in range(0, num_x):
			x = x_start + x * uu_spacing
			if x > doc_w: break
			
			if self.options.type == "line":
#				l = inkex.etree.SubElement(g, 'line')
#				l.set('x1', str(x))
#				l.set('x2', str(x))
#				l.set('y1', "0")
#				l.set('y2', str(doc_h))

				l = inkex.etree.SubElement(g, 'path')
				l.set('d', 'M ' + str(x) + ",0 L " + str(x) + "," + str(doc_h))
		
			if self.options.coords != "none":
				l = inkex.etree.SubElement(cg, 'text')
				l.text = str(int(round((x - x_center) / uu_spacing * self.options.spacing))) + " m"
				l.set("style", "text-anchor:end;text-align:end")
				l.set("transform", ("translate(%.2f,15)" + rot) % (x - 5))
		
		# Horizontal lines and coordinates
		for y in range(0, num_y):
			y = y_start + y * uu_spacing
			if y > doc_h: break

			if self.options.type == "line":
#				l = inkex.etree.SubElement(g, 'line')
#				l.set('y1', str(y))
#				l.set('y2', str(y))
#				l.set('x1', "0")
#				l.set('x2', str(doc_w))
				l = inkex.etree.SubElement(g, 'path')
				l.set('d', 'M 0,' + str(y) + " L " + str(doc_w) + "," + str(y))

			if self.options.coords != "none":
				l = inkex.etree.SubElement(cg, 'text')
				l.text = str(int(-round((y - y_center) / uu_spacing * self.options.spacing))) + " m"
				l.set("style", "text-anchor:end;text-align:end")
				l.set("transform", "translate(45,%.2f)" % (y - 5))

		if self.options.type == "cross":
			l = inkex.etree.SubElement(g, 'path')
			path_id = self.uniqueId("gridCross", True)
			l.set('d', "M -10,0 10,0 M 0,-10 0,10")
			l.set("transform", "translate(%.2f, %.2f)" % (x_center, y_center))
			l.set("id", path_id)
			
			for x in range(0, num_x):
				x_doc = x_start + x * uu_spacing - x_center
				if x_doc > doc_w: break
	
				for y in range(0, num_y):
					if x == 0 and y == 0: continue

					y_doc = y_start + y * uu_spacing - y_center
					if y_doc > doc_h: break
					
					l = inkex.etree.SubElement(g, 'use')
					l.set(inkex.addNS('href', 'xlink'), '#' + str(path_id))
					l.set("transform", "translate(%.2f,%.2f)" % (x_doc, y_doc))
					

if __name__ == '__main__':
	e = SpeleoGrid()
	e.affect()

