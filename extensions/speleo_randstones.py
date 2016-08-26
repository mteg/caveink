# -*- coding: utf-8 -*-
'''
Randstones
'''

import math
import inkex
import simpletransform
import speleo_grid
import string
import random
import sys
import re

class SpeleoRandstones(speleo_grid.SpeleoEffect):
	def __init__(self):
		inkex.Effect.__init__(self)
		
	def randrotate(self, p, cx = 0, cy = 0):
#		p = node.getparent()
		
		tr = self.get_transform(p)
		simpletransform.applyTransformToNode(self.invert_transform(tr), p)

		try:
			x = float(p.get("x"))
			y = float(p.get("y"))
			
			p.attrib.pop("x")
			p.attrib.pop("y")
		except:
			x = 0
			y = 0
		
		if cx != 0 and cy != 0:
			simpletransform.applyTransformToNode(simpletransform.parseTransform("translate(" + str(-cx) + ", " + str(-cy) + ")"), p)
			
		simpletransform.applyTransformToNode(simpletransform.parseTransform("rotate(" + str(random.randint(0, 359)) + ")"), p)
		
		if cx != 0 and cy != 0:
			simpletransform.applyTransformToNode(simpletransform.parseTransform("translate(" + str(cx) + ", " + str(cy) + ")"), p)
	
		simpletransform.applyTransformToNode(simpletransform.parseTransform("translate(" + str(x) + ", " + str(y) + ")"), p)
		simpletransform.applyTransformToNode(tr, p)


	def randstones(self, node):
		if node.tag == inkex.addNS('use', 'svg'):
			m = re.match('#([ra])b([0-9]+)[a-z]', str(node.get(inkex.addNS("href", "xlink"))))
			if m:
#				sys.stderr.write("#" + m.group(1) + "b" + m.group(2) + random.choice("abcdefghijklmn"))

				tr = self.get_transform(node)
				simpletransform.applyTransformToNode(self.invert_transform(tr), node)

				xmin,xmax,ymin,ymax = simpletransform.computeBBox([node])
				cx1 = (xmin + xmax) / 2
				cy1 = (ymin + ymax) / 2

				node.set(inkex.addNS("href", "xlink"), "#" + m.group(1) + "b" + m.group(2) + random.choice("abcdefghijklmn"))

				xmin,xmax,ymin,ymax = simpletransform.computeBBox([node])
				cx2 = (xmin + xmax) / 2
				cy2 = (ymin + ymax) / 2

				simpletransform.applyTransformToNode(simpletransform.parseTransform("translate(" + str(-cx2) + ", " + str(-cy2) + ")"), node)
				simpletransform.applyTransformToNode(simpletransform.parseTransform("rotate(" + str(random.randint(0, 359)) + ")"), node)
				simpletransform.applyTransformToNode(simpletransform.parseTransform("translate(" + str(cx1) + ", " + str(cy1) + ")"), node)
				simpletransform.applyTransformToNode(tr, node)


				
#				sys.stderr.write("cx = " + str(cx) + ", cy = " + str(cy))


		if (node.tag == inkex.addNS('tspan', 'svg') or node.tag == inkex.addNS('text', 'svg')) and node.text:
			if len(node.text) == 1:
				if node.text in string.ascii_lowercase:
					node.text = random.choice(string.ascii_lowercase)
				elif node.text in string.ascii_uppercase:
					node.text = random.choice(string.ascii_uppercase)
				
				if (node.text in string.ascii_letters):
					node.set("rotate",  str(random.randint(0, 359)))

		
		for child in node:
			self.randstones(child);
	
	def effect(self):
		for id, node in self.selected.iteritems():
			self.randstones(node);
			
if __name__ == '__main__':
	e = SpeleoRandstones()
	e.affect()
