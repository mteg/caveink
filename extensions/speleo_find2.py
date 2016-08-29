# -*- coding: utf-8 -*-
'''
Inkscape plugin for gathering all symbols of a particular kind

Copyright (C) 2016 Mateusz Golicz, http://jaskinie.jaszczur.org
Distributed under the terms of the GNU General Public License v2
'''

import inkex
import simpletransform

from speleo import SpeleoEffect, SpeleoTransform

class SpeleoFind2(SpeleoEffect):
  def scanTree(self, node, sel, group, correctiveTransform):
    '''
    Recursively look for <use>s referring to symbol sel
    
    Adds all these symbols to group 'group', applying transforms accordingly
    '''
    
    # Avoid too much recursion
    if node == group: return
    
    # Do not go into invisible layers
    if self.isLayer(node):
      if self.hasDisplayNone(node):
        return
    
    # Recurse first
    for i in node:
      self.scanTree(i, sel, group, correctiveTransform)
        
    # See if it's the symbol we need
    href = node.get(inkex.addNS('href', 'xlink'))
    
    # Perhaps not a reference at all...
    if href == None: return
    
    if href == sel:
      # Get total transform of this symbol
      transform = SpeleoTransform.getTotalTransform(node)
      
      # Group it together with others
      group.append(node)

      # Reset this node transform
      node.set("transform", simpletransform.formatTransform(
                  simpletransform.composeTransform(correctiveTransform, transform)
            ))
                
  def effect(self):
    symbol_ids = []
    # Go through all selected ...
    for id, obj in self.selected.iteritems():
      # Get unique symbol IDs
      symbol_ids.append(obj.get(inkex.addNS("href", "xlink")))
    
    # For all found distinct symbol IDs ...
    for link in set(symbol_ids):
      # Perhaps not a symbol? 
      if link == None: continue
      
      # Create a group
      group = inkex.etree.SubElement(self.currentLayer(), "g")
      
      # Compute corrective transform
      correctiveTransform = SpeleoTransform.invertTransform(SpeleoTransform.getTotalTransform(group))
      
      # Look for our symbols!
      self.scanTree(self.document.getroot(), link, group, correctiveTransform)

if __name__ == '__main__':
  e = SpeleoFind2()
  e.affect()

