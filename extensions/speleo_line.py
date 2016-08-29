# -*- coding: utf-8 -*-
'''
Uses the 'text along path' feature to quickly style paths
into step symbols, dripline etc.

Needs the Speleo Sans font, version 2!

Copyright (C) 2013 Mateusz Golicz, http://jaskinie.jaszczur.org
Distributed under the terms of the GNU General Public License v2
'''

import inkex
from speleo import SpeleoEffect, SpeleoTransform

class SpeleoLine(SpeleoEffect):
	def initOptions(self):
		self.OptionParser.add_option("--fontsize",
				action="store", type="float", 
				dest="fontsize", default=6)
		self.OptionParser.add_option("--fontstroke",
				action="store", type="float", 
				dest="fontstroke", default=0.2)
		self.OptionParser.add_option("--linetype",
				action="store", type="int", 
				dest="linetype", default=1)
		self.OptionParser.add_option("--linewidth",
				action="store", type="float", 
				dest="linewidth", default=0.5)
		self.OptionParser.add_option("--char",
				action="store", type="string", 
				dest="char", default=1)

	
	def effect(self):
		char = ['', '!', '{', '}', '(', ')', '<', '^'][int(self.options.char)]
#		inkex.debug("id = " + str(int(self.options.char)) + " ch = " + char)
		
		for id, node in self.selected.iteritems():
			t = self.options.linetype
			
			if node.tag != inkex.addNS("path", "svg"):
				continue

			tr = SpeleoTransform.getTotalTransform(node.getparent())
			parent_scale = (tr[0][0] + tr[1][1]) / 2.0

			tr = SpeleoTransform.getTotalTransform(node)
			this_scale = (tr[0][0] + tr[1][1]) / 2.0

			fontsize = self.options.fontsize / parent_scale
			linewidth = self.options.linewidth / this_scale
			fontstroke = self.options.fontstroke / parent_scale

#			inkex.debug("scale = " + str(tr[0][0]) + ", " + str(tr[1][1]) + " fsize = " + str(fontsize))
			
			if t == 1:
				line_style = 'stroke:#000000;stroke-width:%.3fmm;fill:none' % linewidth
				text_style = 'font-size:%.3fpt' % fontsize
				text = char * 100 
			elif t == 2:
				line_style = 'stroke:#000000;fill:none;stroke-width:0.5mm;stroke-opacity:0.005'
				text_style = 'font-size:%.3fpt;stroke:#000000;stroke-width:%.3fmm' % (fontsize, fontstroke)
				text = char * 100 
			
		
			node.set('style', line_style)
			tx = inkex.etree.Element('text')
			tp = inkex.etree.Element('textPath')
			tspan = inkex.etree.Element('tspan')

			tp.set(inkex.addNS('href', 'xlink'), '#' + id)
			tspan.set('style', 'font-family:Speleo3;-inkscape-font-specification:Speleo3;' + text_style)
			tspan.text = text

			tp.append(tspan)
			tx.append(tp)
			
			grp = inkex.etree.SubElement(node.getparent(), "g")
			tx.set(inkex.addNS('insensitive', 'sodipodi'), 'true')
			grp.append(node)
			grp.append(tx)
			
#			node.getparent().append(tx)

if __name__ == '__main__':
	e = SpeleoLine()
	e.affect()

