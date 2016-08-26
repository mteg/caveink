# -*- coding: utf-8 -*-
'''
Speleo_find
'''

import inkex
import speleo_find
import string
import sys

class SpeleoOrder(speleo_find.SpeleoFind):
	def __init__(self):
		inkex.Effect.__init__(self)

	def effect(self):
		for ch in [string.ascii_letters, '"#?', '.:', ',;', '>', '~', "%"
				'*$&\'/045\\`|', '123', '6', '7', '89', '[]',
				'=+-', '@', '?', '^', '()', '{}']:
			
			cgroup = None
			for id, node in self.selected.iteritems():
				if cgroup is None:
					cgroup = inkex.etree.Element('g')
					node.getparent().append(cgroup)

				self.do_lookup(node, ch, cgroup)

			if cgroup is not None:
				if not len(cgroup):
					cgroup.getparent().remove(cgroup)	

if __name__ == '__main__':
	e = SpeleoOrder()
	e.affect()
