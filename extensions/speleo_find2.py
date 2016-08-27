# -*- coding: utf-8 -*-
'''
Copyright (C) 2008 Thomas Holder, http://sf.net/users/speleo3/
Distributed under the terms of the GNU General Public License v2
'''

import math
import inkex
import simpletransform
import speleo_grid
import simplestyle
import logging
import simplepath
import sys

class SpeleoFind2(speleo_grid.SpeleoEffect):
	def __init__(self):
		inkex.Effect.__init__(self)
		self.OptionParser.add_option("--debug",
				action="store", type="string", 
				dest="debug", default="")
		self.OptionParser.add_option("--mode",
				action="store", type="string", 
				dest="mode", default="pack")
		self.OptionParser.add_option("--pack",
				action="store", type="string", 
				dest="pack", default="root")

	def styleIfPresent(self, node, key, default = ''):
	        style = node.get('style')
	        if style:
	        	style = simplestyle.parseStyle(style)
                        if style.has_key(key):
                                return style[key]
                
                return ""
	

	# Make an index of names appearing in layer hierarchy
	def scanTree(self, node, sel):
	        if node == self.group: return
	        if node.get(inkex.addNS('groupmode', 'inkscape')) == 'layer':
	                # Skip if invisible
	                # TODO ... and requested as such
	                if self.styleIfPresent(node, "display") == "none":
	                        return
                
                href = node.get(inkex.addNS('href', 'xlink'))
                if href <> None:
                        if href == sel and self.group <> node:
                                # Get transform
                                thisTransform = simpletransform.composeParents(node, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
                                self.group.append(node)
                                # Reset this node transform
                                node.set("transform", simpletransform.formatTransform(thisTransform))
                
                for i in node:
                        self.scanTree(i, sel)

	
	def effect(self):
	        # Configure logging
	        if len(self.options.debug):
	                logging.basicConfig(level = logging.DEBUG)


                for id, obj in self.selected.iteritems():
                        link = obj.get(inkex.addNS("href", "xlink"))
                        if link == None: continue
                        
                        self.group = inkex.etree.SubElement(self.get_current_layer(), "g")
                        self.scanTree(self.document.getroot(), link)

if __name__ == '__main__':
	e = SpeleoFind2()
	e.affect()

