# -*- coding: utf-8 -*-
### Still needs refactoring

'''
Generate a grid for cave plan, with coordinates printed out

Copyright (C) 2013, 2016 Mateusz Golicz, http://jaskinie.jaszczur.org
Distributed under the terms of the GNU General Public License v2
'''


import math
import inkex
import simpletransform

from speleo import SpeleoEffect, SpeleoTransform

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
		self.OptionParser.add_option("--units",
				action="store", type="string", 
				dest="units", default=" m")
		self.OptionParser.add_option("--origin-x",
				action="store", type="int", 
				dest="origin_x", default=0)
		self.OptionParser.add_option("--origin-y",
				action="store", type="int", 
				dest="origin_y", default=0)
		self.OptionParser.add_option("--font-size",
				action="store", type="int", 
				dest="fontsize", default=0)

	def drawGrid(self, x_center, y_center, doc_w, doc_h, pos_x = 0, pos_y = 0):

		if self.options.coords == "rotate":
			rot = " rotate(270)"
		else:
			rot = ""
			
		x_center -= pos_x
		y_center -= pos_y
		uu_spacing = self.options.spacing / self.options.scale * 1000.0 / 25.4 * 90.0		
		x_start = x_center - math.floor(x_center / uu_spacing) * uu_spacing
		y_start = y_center - math.floor(y_center / uu_spacing) * uu_spacing
		num_x = int(math.ceil(doc_w / uu_spacing))
		num_y = int(math.ceil(doc_h / uu_spacing))

		layer = self.currentLayer()

		g = inkex.etree.SubElement(layer, 'g')
		
		# Invert any sub-transforms of layer
		simpletransform.applyTransformToNode(SpeleoTransform.invertTransform(SpeleoTransform.getTotalTransform(g)), g)

		# Add translation
		simpletransform.applyTransformToNode(simpletransform.parseTransform("translate(%.6f, %.6f)" % (pos_x, pos_y)), g)

		if self.options.coords != "none":
			g.set('style', 'stroke:#888;fill:#888;stroke-width:0.2mm;font-size:' + str(self.options.fontsize) + 'pt;text-anchor:end;text-align:end')

			cg = inkex.etree.SubElement(g, "g")
			g = inkex.etree.SubElement(g, "g")

			g.set('style', 'fill:none;')
			cg.set('style', 'stroke:none;stroke-width:0')
		else:
			g.set('style', 'stroke:#888;fill:none;stroke-width:0.2mm')


		# Vertical lines and coordinates
		for x in range(0, num_x):
			x = x_start + x * uu_spacing
			if x > doc_w: break
			
			if self.options.type == "line":
				l = inkex.etree.SubElement(g, 'path')
				l.set('d', 'M ' + str(x) + ",0 L " + str(x) + "," + str(doc_h))
		
			if self.options.coords != "none":
				l = inkex.etree.SubElement(cg, 'text')
				l.text = str(int(round((x - x_center) / uu_spacing * self.options.spacing) + self.options.origin_x)) + self.options.units
				l.set("style", "text-anchor:end;text-align:end")
				l.set("transform", ("translate(%.2f,15)" + rot) % (x - 5))
		
		# Horizontal lines and coordinates
		for y in range(0, num_y):
			y = y_start + y * uu_spacing
			if y > doc_h: break

			if self.options.type == "line":
				l = inkex.etree.SubElement(g, 'path')
				l.set('d', 'M 0,' + str(y) + " L " + str(doc_w) + "," + str(y))

			if self.options.coords != "none":
				l = inkex.etree.SubElement(cg, 'text')
				l.text = str(int(-round((y - y_center) / uu_spacing * self.options.spacing) + self.options.origin_y)) + self.options.units
				l.set("style", "text-anchor:end;text-align:end")
				l.set("transform", "translate(45,%.2f)" % (y - 5))

		# Crosses, if requested
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
					
	
	def getBox(self, obj):
		x = y = w = h = 0
		try:
			x = float(obj.get("x"))
			y = float(obj.get("y"))
		except:
			pass
		tr = SpeleoTransform.getTotalTransform(obj)
		(x, y) = SpeleoTransform.transformCoords((x, y), tr)
		
		if obj.tag == inkex.addNS("rect", "svg"):
			try:
				x2 = float(obj.get("x")) + float(obj.get("width"))
				y2 = float(obj.get("y")) + float(obj.get("height"))
				(x2, y2) = SpeleoTransform.transformCoords((x2, y2), tr)
				w = abs(x2 - x)
				h = abs(y2 - y)
			except:
				pass
		
		return (x, y, w, h)
	
	
	def effect(self):
		doc_w = self.unittouu(self.document.getroot().get('width'))
		doc_h = self.unittouu(self.document.getroot().get('height'))
		pos_x = pos_y = 0
		
		if self.options.fontsize < 1:
			self.options.fontsize = 8

		if len(self.selected) == 0:
			# Start at (0, 0)
			xc = yc = 0
		elif len(self.selected) == 1:
			# A symbol or rectangle to mark origin
			id, obj = self.selected.popitem()
			(xc, yc, w, h) = self.getBox(obj)
		elif len(self.selected) == 2:
			id1, obj1 = self.selected.popitem()	
			id2, obj2 = self.selected.popitem()
			(xc1, yc1, w1, h1) = self.getBox(obj1)
			(xc2, yc2, w2, h2) = self.getBox(obj2)
			# Now, depending on area ...
			if (w1 * h1) > (w2 * h2): 
				(xc, yc) = (xc2, yc2)
				(pos_x, pos_y, doc_w, doc_h) = (xc1, yc1, w1, h1)
			else:				
				(xc, yc) = (xc1, yc1)
				(pos_x, pos_y, doc_w, doc_h) = (xc2, yc2, w2, h2)
				
		self.drawGrid(xc, yc, doc_w, doc_h, pos_x, pos_y)


if __name__ == '__main__':
	e = SpeleoGrid()
	e.affect()

