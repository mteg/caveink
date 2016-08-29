# -*- coding: utf-8 -*-
'''
Inkscape plugin for making "windows" into the layer hierarchy with
alternative stacking/opacities/visibility settings.

Useful for depicting intersecting passages on cave maps.

Copyright (C) 2016 Mateusz Golicz, http://jaskinie.jaszczur.org
Distributed under the terms of the GNU General Public License v2
'''

import math
import inkex
import simpletransform
import simplestyle
import logging
from speleo import SpeleoEffect, SpeleoTransform

class SpeleoWindow(SpeleoEffect):
  def initOptions(self):
    self.OptionParser.add_option("--opacity",
                    action="store", type="string", 
                    dest="opacity", default="clone")
    self.OptionParser.add_option("--parent",
                    action="store", type="string", 
                    dest="parent", default="root")

  def findLeafLayers(self, node, collection, isVisible = True):
    '''
    Recursively collects all leaf layers into a list of tuples (node, isVisible)
    '''
    
    self.log("Entering addVisibleLeafLayers for " + node.get("id"))
    
    # If it is not a group, it is not interesting
    if node.tag != inkex.addNS('g','svg') and node.tag != inkex.addNS('svg','svg'):
      self.log("Node " + node.get("id") + " is not a group, skipping")
      return False

    # If it's not visible, we need to propagate down this information
    if self.hasDisplayNone(node):
      self.log("Node " + node.get("id") + " is not actually displayed")
      isVisible = False
    
    # Process all child groups, noting whether there are any leaf layers down there
    layersInChildren = False
    for child in node.getchildren():
      hierarchyResult = self.findLeafLayers(child, collection, isVisible)
      layersInChildren = layersInChildren or hierarchyResult
    
    # See if it's worth collecting
    if node.tag == inkex.addNS('g', 'svg'): # Could be an <svg> element as well
      if layersInChildren == False and self.isLayer(node):
        # It is a leaf layer.
        collection.append((node, isVisible))
        
    # Tell the caller if they have children or not.
    return layersInChildren or self.isLayer(node)
    
  
  def effect(self):
    # Configure logging
    if len(self.options.debug): logging.basicConfig(level = logging.DEBUG)
    
    # Get root node
    root = self.getRoot() if self.options.parent == "root" else self.currentLayer()

    # Collect all leaf layers 
    layers = []
    self.findLeafLayers(root, layers)
    
    # Create a group object to contain our clones
    output = inkex.etree.SubElement(root, 'g')
    
    # Go through all collected layers
    for (node, isVisible) in layers:
      # Skip invisible ones
      if not isVisible: continue
      
      # Clone the layer
      clone = inkex.etree.SubElement(output, 'use', {
        inkex.addNS('href', 'xlink'):  '#' + str(node.get("id"))
      })

      # Set opacity according to options
      if self.options.opacity == "copy" or self.options.opacity == "copy-reset":
        clone.set("style", "opacity: " + self.getOpacity(node))
      if self.options.opacity == "copy-reset":
        self.changeStyleKey(node, "opacity", 1)

      self.log("Node " + node.get("id") + " IS CLONED")
    
    # Now clip to desired shape

    selected = self.selected.iteritems()
    if len(self.selected) > 0:
      
      # Create a new clipPath in defs
      defs = self.getDefs()
      clip_path = inkex.etree.SubElement(self.getDefs(), inkex.addNS("clipPath", "svg"), {
        "clipPathUnits": "userSpaceOnUse",
        "id": self.uniqueId("clipPath")
      });
              
      # Move all selected objects into the clipPath
      for id, obj in selected:
        clip_path.append(obj)

      # Clip output using this clipPath
      output.set("clip-path", "url(#" + clip_path.get("id") + ")")

if __name__ == '__main__':
  e = SpeleoWindow()
  e.affect()

