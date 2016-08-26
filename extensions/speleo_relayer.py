# -*- coding: utf-8 -*-
'''
Copyright (C) 2008 Thomas Holder, http://sf.net/users/speleo3/
Distributed under the terms of the GNU General Public License v2
'''

import math
import inkex
import simpletransform
import speleo_grid

class SpeleoRelayer(speleo_grid.SpeleoEffect):
	def __init__(self):
		inkex.Effect.__init__(self)
		self.OptionParser.add_option("--depth",
				action="store", type="int", 
				dest="depth", default=1)
		self.OptionParser.add_option("--mode",
				action="store", type="string", 
				dest="mode", default="relayer")
		self.OptionParser.add_option("--parent",
				action="store", type="string", 
				dest="parent", default="this")
	

	def relayer(self, node, depth):
		if depth <= 0: return
		if node.tag != inkex.addNS('g','svg'): return
		
		node.set(inkex.addNS('label', 'inkscape'), node.get('id'))
		node.set(inkex.addNS('groupmode', 'inkscape'), "layer")
		
		for child in node:
			self.relayer(child, depth - 1)
	
	def unlayer(self, node):
		if node.tag != inkex.addNS('g','svg'): return
		
		for child in node:
			try:
				child.attrib.pop(inkex.addNS('groupmode', 'inkscape'))
			except:
				pass
			self.unlayer(child)
	
	def effect(self):
		if self.options.mode == "unlayer":
			self.unlayer(self.get_current_layer())
		else:
			if self.options.parent == "this":
				parent = self.get_current_layer()
			else:
				parent = self.document.getroot()
			
			for id, node in self.selected.iteritems():
				m1 = self.get_transform(node.getparent())
				parent.append(node)
				m2 = self.invert_transform(self.get_transform(node.getparent()))
				simpletransform.applyTransformToNode(simpletransform.composeTransform(m2, m1), node)
				
				self.relayer(node, self.options.depth)
			

if __name__ == '__main__':
	e = SpeleoRelayer()
	e.affect()

