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

log = logging.debug

class SpeleoWindow(speleo_grid.SpeleoEffect):
	def __init__(self):
		inkex.Effect.__init__(self)
		self.OptionParser.add_option("--debug",
				action="store", type="string", 
				dest="debug", default="")
		self.OptionParser.add_option("--opacity",
				action="store", type="string", 
				dest="opacity", default="clone")
		self.OptionParser.add_option("--parent",
				action="store", type="string", 
				dest="parent", default="selected-layer")
	

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
	
	def styleIfPresent(self, node, key, default = ''):
	        style = node.get('style')
	        if style:
	        	style = simplestyle.parseStyle(style)
                        if key in style:
                                return style[key]
                
                return ""

	
	def hasDisplayNone(self, node):
	        display = self.styleIfPresent(node, 'display')
                if self.styleIfPresent(node, 'display') == 'none':
                        log("Node " + node.get("id") + " has display = none, really!")
                        return True
                
                log("Returning False for " + node.get("id"))
	        return False

        def getOpacity(self, node):
                opacity = self.styleIfPresent(node, 'opacity')
                if opacity == "":
                        return "1"
                return opacity

        def changeStyleKey(self, node, key, value):
	        style = node.get('style')
	        if style:
	        	style = simplestyle.parseStyle(style)
                else:
                        style = {}
                style[key] = value
                node.set('style', simplestyle.formatStyle(style))

	# Returns False if no layers found within the hierarchy
	#         True if any child object or the object itself is a layer
	def addVisibleLeafLayers(self, node, keepAdding):
	        log("Entering addVisibleLeafLayers for " + node.get("id"))
		if node.tag != inkex.addNS('g','svg') and node.tag != inkex.addNS('svg','svg'):
		        log("Node " + node.get("id") + " is not a group, skipping")
			return False

		# If it's not displayed, then just go through the hierarchy
		if self.hasDisplayNone(node):
		        log("Node " + node.get("id") + " is not actually displayed, stopping any adds")
			keepAdding = False
		
		# Process all child groups
		layersInChildren = False
		for child in node.getchildren():
		        hierarchyResult = self.addVisibleLeafLayers(child, keepAdding)
			layersInChildren = layersInChildren or hierarchyResult
		
		if keepAdding and node.tag == inkex.addNS('g', 'svg'):
			# See if this one perhaps is to be added
			if layersInChildren == False and node.get(inkex.addNS('groupmode', 'inkscape')) == 'layer':
				# So, we have here: a visible layer, under lots of visible layers, that has no child layers
				# Clone it!
				
				clone = inkex.etree.SubElement(self.win_object, 'use')
				clone.set(inkex.addNS('href', 'xlink'), '#' + str(node.get("id")))
				# Set opacity 
				if self.options.opacity == "copy" or self.options.opacity == "copy-reset":
				        clone.set("style", "opacity: " + self.getOpacity(node))
                                if self.options.opacity == "copy-reset":
                                        self.changeStyleKey(node, "opacity", 1)
                                        
                                        
				
				
                                log("Node " + node.get("id") + " IS CLONED")
                        else:
                                log("Node " + node.get("id") + " does not like to be cloned")

		
		return layersInChildren or node.get(inkex.addNS('groupmode', 'inkscape')) == 'layer'
		
	
	def effect(self):
	        # Configure logging
	        if len(self.options.debug):
	                logging.basicConfig(level = logging.DEBUG)
	        
		# Get root node
                if self.options.parent == "root":
                        root = self.document.getroot()
                else:
                        root = self.get_current_layer()
		
		# Create a group object to contain our clones
		self.win_object = inkex.etree.Element('g')
		
		# Recursively add all visible leaf layers
		self.addVisibleLeafLayers(root, True)
		
		# Add the group to root
#		if len(self.win_object.getchildren()):
        	root.append(self.win_object)
        	
        	# Clip if exactly one object was selected
        	selected = self.selected.iteritems()
        	if len(self.selected) > 0:
        	        # Move this object(s) into a clipPath
        	        # Stupid warnings when no defs!
        	        defs = self.xpathSingle('/svg:svg//svg:defs')
        	        if defs == None:
        	                defs = self.document.getroot()

                        clip_path = inkex.etree.SubElement(defs, inkex.addNS("clipPath", "svg"), {
                                "clipPathUnits": "userSpaceOnUse",
                                "id": self.uniqueId("clipPath")
                        });
        	                
        	        for id, obj in selected:
        	                clip_path.append(obj)

                        self.win_object.set("clip-path", "url(#" + clip_path.get("id") + ")")
        	

if __name__ == '__main__':
	e = SpeleoWindow()
	e.affect()

