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

class SpeleoPack(speleo_grid.SpeleoEffect):
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
	
	def packLayers(self, node, move = False):
	        if node.get(inkex.addNS('groupmode', 'inkscape')) == 'layer':
                        if self.styleIfPresent(node, "display") == "none":
                                node.getparent().remove(node)
                                return
	                node.attrib.pop(inkex.addNS('groupmode', 'inkscape'))
	                node.set("class", "wasLayer")
	                if move: self.box.append(node)

	
	        for child in node:
                        self.packLayers(child)
        
        def transformForUnpacking(self, node, transform):
                cName = node.get("class")
                if cName <> None:
                        if cName == "wasLayer":
                                # We have a layer, need to fix & recurse
                	        node.set(inkex.addNS('groupmode', 'inkscape'), "layer")
                	        node.attrib.pop("class")
                	        
                	        # It might have some own transform
                	        layerTransform = node.get("transform")
                	        if layerTransform <> None:
                	                node.attrib.pop("transform")
                	                transform = simpletransform.composeTransform(transform, simpletransform.parseTransform(layerTransform))
                	        
                	        for child in node:
                        	        self.transformForUnpacking(child, transform)

                	        return
                
                # Not a layer, just apply the transform, no recursion!
                simpletransform.applyTransformToNode(transform, node)
                                

        def unpackLayers(self, node, root, rootTransform):
                # Get transform to apply to all children
                thisTransform = simpletransform.composeParents(node, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
                
                # Composing order might be wrong
                thisTransform = simpletransform.composeTransform(rootTransform, thisTransform) 
                
                # Process children - should all be layers in fact!
                for child in node:
                        self.transformForUnpacking(child, thisTransform)
                        root.append(child)
                
                # Delete this very group
                node.getparent().remove(node)
	
	def effect(self):
	        # Configure logging
	        if len(self.options.debug):
	                logging.basicConfig(level = logging.DEBUG)
	        
	        if self.options.mode == "unpack":
	                # Unpack layers
	                # Get current layer
                        root = self.get_current_layer()
                        if root == None: root = self.document.getroot()
                        
                        if root.tag == inkex.addNS("svg", "svg"):
                                rootTransform = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
                        else:
                                # Get transform applying to this current layer
                                rootTransform = simpletransform.composeParents(root, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
                                # it should be an unitary transform, but sometimes there are strange cases!
                                
                                # invert it!
                                rootTransform = self.invert_transform(rootTransform)
	                
	                for id, node in self.selected.iteritems():
	                        if node.tag != inkex.addNS('g','svg'): continue
                                self.unpackLayers(node, root, rootTransform)

	        else:
	                # Pack layers
                        # Get root node
                        if self.options.pack == "root":
                                root = self.document.getroot()
                        else:
                                root = self.get_current_layer()
                        
                        # Create a containter to pack the box into
                        self.box = inkex.etree.SubElement(self.document.getroot(), "g")
                        for child in root:
                                self.packLayers(child, True)
                        
                        # Unmark any current layer setting
                        view = self.xpathSingle('//sodipodi:namedview')
                        if view != None:
                                current_layer = inkex.addNS('current-layer', 'inkscape')
                                view.attrib.pop(current_layer)


if __name__ == '__main__':
	e = SpeleoPack()
	e.affect()

