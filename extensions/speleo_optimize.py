# -*- coding: utf-8 -*-
'''
Cut out unneeded styles and tspans from text elements
'''

import math
import inkex
import simpletransform
import speleo_grid
import string
import random
import sys
import re

class SpeleoOptimize(speleo_grid.SpeleoEffect):
	def __init__(self):
		inkex.Effect.__init__(self)
		self.defaults = { \
			'font-style': 'normal', \
			'font-variant': 'normal', \
			'font-weight': 'normal', \
			'font-stretch': 'normal', \
			'text-anchor': 'start', \
			'writing-mode': 'lr-tb', \
			'letter-spacing': '0px', \
			'word-spacing': '0px', \
			'fill-opacity': '1',
			'display': 'inline'}


	def optimize(self, node):
		for child in node:
			# If this child is the only <tspan> contained within <text>...
			if child.tag == inkex.addNS('tspan', 'svg') and node.tag == inkex.addNS('text', 'svg') and len(node) == 1 :
				# Now, if the font is Speleo3 within the <tspan>
					# ... or there is no family specification within the <tspan>, but <text> says it's Speleo3...
#				sys.stderr.write(str(child.get('style')) + "/" +  str(node.get('style')) + "/" + str(len(node)))
				if re.match('.*font-family: *Speleo3.*', str(child.get("style"))) or \
					((not re.match('.*font-family:.*', str(child.get("style")))) and \
						re.match('.*font-family: *Speleo3.*', str(node.get("style")))):
					
					# Retrieve style
					style = {}
					for s in [node.get("style"), child.get("style")]:
						if s:
							for pair in s.split(";"):
								k, v = pair.split(":", 2)
								style[k] = v.strip()
					
					# Remove default properties
					for k, v in self.defaults.iteritems():
						if k in style:
							if style[k] == v:
								del style[k]
					
					# Unset meaningless properties
					for i in ['text-align', 'line-height', 'stroke-dasharray', 'stroke-miterlimit']:
						if i in style:
							del style[i]
					
					# remove the TSPAN
					node.text = child.text
					node.remove(child)
					
					# set filtered out style
					node.set("style", ';'.join('%s:%s' % (k, v) for k, v in style.iteritems()))					
			else:
				self.optimize(child)
	
	def effect(self):
		self.optimize(self.document.getroot());
			
if __name__ == '__main__':
	e = SpeleoOptimize()
	e.affect()
