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

class SpeleoMerge(speleo_grid.SpeleoEffect):
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
	
	# Recursively find layers with same names as the current and its sub-layers
	def findTwins(self, node, active):
	        # Do not go into the active layer!
	        if node == active: return
	        if node.get(inkex.addNS('groupmode', 'inkscape')) == 'layer':
	                # Skip if invisible
	                # TODO ... and requested as such
	                if self.styleIfPresent(node, "display") == "none":
	                        return

	                # Did we have this name in current layer tree?
	                name = node.get(inkex.addNS('label', 'inkscape'))
	                if name in self.targets:
	                        # Move all objects in this layer!
	                        # TODO: handle unusual transform scenarios (transforms on layers)
	                        for i in node:
	                                self.targets[name].append(i)
                                
                                # Delete this layer
                                # TODO: ... if requested
                                node.getparent().remove(node)
	        
	                # Recurse
	                for i in node:
        	                self.findTwins(i, active)

	# Make an index of names appearing in layer hierarchy
	def scanLayerTree(self, node):
	        if node.get(inkex.addNS('groupmode', 'inkscape')) == 'layer':
	                # Skip if invisible
	                # TODO ... and requested as such
	                if self.styleIfPresent(node, "display") == "none":
	                        return

	                # Get layer name
	                name = node.get(inkex.addNS('label', 'inkscape'))
	                
	                # Put it in the dictionary
	                if not (name in self.targets):
        	                self.targets[name] = node
	        
	                # Recurse
	                for i in node:
        	                self.scanLayerTree(i)
                
	
	def effect(self):
	        # Configure logging
	        if len(self.options.debug):
	                logging.basicConfig(level = logging.DEBUG)

                self.targets = {}
                root = self.get_current_layer()
                if root <> None:
                        self.scanLayerTree(root)
                        for i in self.document.getroot():
                                self.findTwins(i, root)


if __name__ == '__main__':
	e = SpeleoMerge()
	e.affect()

