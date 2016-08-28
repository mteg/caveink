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
import os
from lxml import etree

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

	def scanDefs(self, file, dict):
		defs = file.xpath('/svg:svg//svg:defs', namespaces=inkex.NSS)[0]
		for node in defs:
			dict[node.get("id")] = node
		return defs

	
	def loadSymbols(self, file):
		try:
			fh = open(os.path.join(os.path.dirname(__file__), "..", "symbols", file), "r")
			p = etree.XMLParser(huge_tree=True)
			self.scanDefs(etree.parse(fh, parser=p), self.extSymbols)
			
		except Exception:
			pass
	
	def ensureSymbol(self, id):
		if id in self.ownSymbols: return True
		if self.extSymbols == None:
			self.extSymbols = {}
			self.loadSymbols("cave_rocks.svg")
			self.loadSymbols("cave_rocks_gray.svg")
			self.loadSymbols("cave_rocks_unstyled.svg")
			
		if id in self.extSymbols:
			self.defs.append(self.extSymbols[id])
			self.ownSymbols[id] = self.extSymbols[id]
			return True
		
		return False

	def randstones(self, node):
		if node.tag == inkex.addNS('use', 'svg'):
			m = re.match('#(gr|un|)?([ra])b([0-9]+)[a-z]', str(node.get(inkex.addNS("href", "xlink"))))
			if m:
#				sys.stderr.write("#" + m.group(1) + "b" + m.group(2) + random.choice("abcdefghijklmn"))

				tr = self.get_transform(node)
				simpletransform.applyTransformToNode(self.invert_transform(tr), node)

				new_id = m.group(1) + m.group(2) + "b" + m.group(3) + random.choice("abcdefghij")
				if self.ensureSymbol(new_id):
					node.set(inkex.addNS("href", "xlink"), "#" + new_id)

				simpletransform.applyTransformToNode(simpletransform.parseTransform("rotate(" + str(random.randint(0, 359)) + ")"), node)
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
		self.extSymbols = None
		self.ownSymbols = {}
		self.defs = self.scanDefs(self.document, self.ownSymbols)
		for id, node in self.selected.iteritems():
			self.randstones(node);
			
if __name__ == '__main__':
	e = SpeleoRandstones()
	e.affect()
