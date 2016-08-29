# -*- coding: utf-8 -*-
'''
Inkscape plugin for packing/unpacking a collection of layers into a group.

Useful for cut & paste across documents.

Copyright (C) 2016 Mateusz Golicz, http://jaskinie.jaszczur.org
Distributed under the terms of the GNU General Public License v2
'''

import math
import inkex
import simpletransform
from speleo import SpeleoEffect, SpeleoTransform

class SpeleoPack(SpeleoEffect):
  def initOptions(self):
    self.OptionParser.add_option("--mode",
        action="store", type="string", 
        dest="mode", default="pack")
    self.OptionParser.add_option("--pack",
        action="store", type="string", 
        dest="pack", default="root")

  def packLayers(self, node, move = False):
    '''
    Recursively pack layers into a group
    '''
    # Avoid infinite recursion
    if node == self.box: return
    
    # If it's a layer ...
    if self.isLayer(node):
      # If it's invisible...
      if self.hasDisplayNone(node):
        # Remove and go further
        node.getparent().remove(node)
        return
      # If it's visible...
      # Make it NOT a layer
      node.attrib.pop(inkex.addNS('groupmode', 'inkscape'))
      
      # Make a small mark, so that we later can remember!
      node.set("class", "wasLayer")
      
      # Move it to our container, if it's in the first generation of siblings 
      if move: self.box.append(node)

    # Go deep
    for child in node:
      self.packLayers(child)
        
  def unpackLayers(self, node, transform):
    '''
    Unpack a group back into layers and apply a transform accordingly
    '''
    
    # Was that a layer before going through packLayers() ?
    cName = node.get("class")
    if cName <> None:
      if cName == "wasLayer":
        # It seems so!

        # Revert changes made by packLayers()
        node.set(inkex.addNS('groupmode', 'inkscape'), "layer")
        node.attrib.pop("class")
        
        # The group could have acquired its own transform...
        layerTransform = node.get("transform")
        
        # Transforms on regular groups are nice, but we do not want to have a transform on a layer!
        if layerTransform <> None:
          # Remove the transform
          node.attrib.pop("transform")
          
          # Compose it with what we have
          transform = simpletransform.composeTransform(transform, simpletransform.parseTransform(layerTransform))
        
        # Transform all child nodes of this layer, unpacking sub-layers if there are any
        for child in node:
          self.unpackLayers(child, transform)

        return
    
    # It never was a layer! We can simply apply our transform and say goodbye!
    simpletransform.applyTransformToNode(transform, node)
                            
  def processLayerContainer(self, node, root, invertedRootTransform):
    '''
    Unpack layers contained in a layer container.
    
    Does some preparations, and then recursively calls unpackLayers()
    '''

    # The group might have been transformed
    thisTransform = SpeleoTransform.getTotalTransform(node)
    
    # Account for any transforms our target layer can possibly have
    # (it shouldn't have any!)
    thisTransform = simpletransform.composeTransform(invertedRootTransform, thisTransform) 
    
    # Process children - should all be layers in fact!
    for child in node:
      # Apply transforms and change groupping mode
      self.unpackLayers(child, thisTransform)
      # Move to our root
      root.append(child)
    
    # Delete the container
    node.getparent().remove(node)
  
  def effect(self):
    if self.options.mode == "unpack":
      # Unpack layers from a group
            
      # Get current layer
      root = self.currentLayer()
        
      # Are we in the root layer?
      invertedTransform = SpeleoTransform.invertTransform(SpeleoTransform.getTotalTransform(root))
      
      # Go through all selected layer containers
      for id, node in self.selected.iteritems():
        if node.tag != inkex.addNS('g','svg'): continue
        self.processLayerContainer(node, root, invertedTransform)
    else:
      # Pack layers into group
      
      # What to pack?
      if self.options.pack == "root":
        root = self.document.getroot()
      else:
        root = self.get_current_layer()
                        
      # Create a containter to pack the layers into
      self.box = inkex.etree.SubElement(self.document.getroot(), "g")
      
      # Pack all the layers!
      for child in root:
        self.packLayers(child, True)
                        
      # Unmark any current layer setting
      try:
        view = self.xpathSingle('//sodipodi:namedview')
        current_layer = inkex.addNS('current-layer', 'inkscape')
        view.attrib.pop(current_layer)
      except Exception:
        pass

if __name__ == '__main__':
  e = SpeleoPack()
  e.affect()

