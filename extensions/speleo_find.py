# -*- coding: utf-8 -*-
'''
Speleo_find
'''

import math
import inkex
import simpletransform
import speleo_grid
import string
import random
import sys

class SpeleoFind(speleo_grid.SpeleoEffect):
	def __init__(self):
		inkex.Effect.__init__(self)
		self.OptionParser.add_option("--char",
				action="store", type="string", 
				dest="char", default="none")

	def do_lookup(self, node, fstr, cgroup):
		if node.text:
			if node.tag == inkex.addNS('tspan', 'svg'):
				if len(node.text) == 1:
					if node.text in fstr:
						p = node.getparent()
						
	#					try:
	#						x = float(p.get("x"))
	#						y = float(p.get("y"))
							
	#						p.attrib.pop("x")
	#						p.attrib.pop("y")
	#					except:
	#						x = 0
	#						y = 0
						
						m1 = self.get_transform(p.getparent())
						cgroup.append(p)
						m2 = self.invert_transform(self.get_transform(p.getparent()))
						
	#					simpletransform.applyTransformToNode(simpletransform.parseTransform("translate(" + str(x) + ", " + str(y) + ")"), p)
						simpletransform.applyTransformToNode(simpletransform.composeTransform(m2, m1), p)

			if node.tag == inkex.addNS('text', 'svg'):
				if len(node.text) == 1:
					if node.text in fstr:
						p = node 
						
						m1 = self.get_transform(p.getparent())
						cgroup.append(p)
						m2 = self.invert_transform(self.get_transform(p.getparent()))
						
	#					simpletransform.applyTransformToNode(simpletransform.parseTransform("translate(" + str(x) + ", " + str(y) + ")"), p)
						simpletransform.applyTransformToNode(simpletransform.composeTransform(m2, m1), p)
					
			
		for child in node:
			self.do_lookup(child, fstr, cgroup);

	def effect(self):
		cgroup = None
		for id, node in self.selected.iteritems():
			if cgroup is None:
				cgroup = inkex.etree.Element('g')
				node.getparent().append(cgroup)

			self.do_lookup(node, self.options.char, cgroup)

		if cgroup is not None:
			if not len(cgroup):
				cgroup.getparent().remove(cgroup)

if __name__ == '__main__':
	e = SpeleoFind()
	e.affect()
