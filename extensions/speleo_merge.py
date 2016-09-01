# -*- coding: utf-8 -*-
'''
Inkscape plugin for merging layers with the same label

Copyright (C) 2016 Mateusz Golicz, http://jaskinie.jaszczur.org
Distributed under the terms of the GNU General Public License v2
'''

import inkex
import simpletransform
import logging
import sys

from speleo import SpeleoEffect, SpeleoTransform

class SpeleoMerge(SpeleoEffect):
  def mergeTwins(self, node, bigbrothers, active):
    '''
    Recursively merge layers into their older twins
    '''
    # If it's not a layer, end of story.
    if not self.isLayer(node): return
    
    # If it's invisible, end of story!
    if self.hasDisplayNone(node): return
    
    # Did we have this name in current layer tree?
    name = node.get(inkex.addNS('label', 'inkscape'))
    self.log("Processing " + name)

    # Recurse first
    for i in node:
     self.mergeTwins(i, bigbrothers, active)
    
    if name in bigbrothers:
      # Indeed! Let's merge this layer with it's bigger brother!
      bigBrother = bigbrothers[name]
      
      # Ain't that us?
      if bigBrother == node: return
      
      # Get transforms (ours & brother's)
      ourTransform = SpeleoTransform.getTotalTransform(node)
      bigTransform = SpeleoTransform.getTotalTransform(bigBrother)
      
      # Compose a transform to apply to child nodes to fix them in proper places
      transformFix = simpletransform.composeTransform(ourTransform, SpeleoTransform.invertTransform(bigTransform))
      
      # Move all nodes in this layer
      for i in node:
        bigBrother.append(i)
        simpletransform.applyTransformToNode(transformFix, i)
                  
      # Delete this layer
      # TODO: ... if requested
      node.getparent().remove(node)

  def scanLayerTree(self, node, index):
    '''
    Make a BFS index of layers by name
    '''
    bfsList = [node]
    while len(bfsList):
      node = bfsList.pop(0)
      
      # Not a layer? Goodbye!
      if not (self.isLayer(node) or node.tag == inkex.addNS("svg", "svg")): continue
    
      if self.isLayer(node):
        # Invisible? Goodbye!
        # TODO ... if requested as such
        if self.hasDisplayNone(node): continue

        # Get layer name
        name = node.get(inkex.addNS('label', 'inkscape'))
              
        # Put it in the dictionary
        if not (name in index):
          self.log("indexing " + str(node) + " as " + name)
          index[name] = node
  
      # Recurse
      for i in node:
        bfsList.append(i)
  
  def effect(self):
    # Configure logging
    if len(self.options.debug): logging.basicConfig(level = logging.DEBUG)

    # Get current layer
    root = self.currentLayer()

    # Make an index of targets
    targets = {}
    self.scanLayerTree(root, targets)
    self.scanLayerTree(self.getRoot(), targets)
    
    # Merge layers having same names!
    for i in self.getRoot():
      self.mergeTwins(i, targets, root)


if __name__ == '__main__':
  e = SpeleoMerge()
  e.affect()

