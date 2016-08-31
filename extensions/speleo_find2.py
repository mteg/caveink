# -*- coding: utf-8 -*-
'''
Inkscape plugin for searching & replacing symbols

Copyright (C) 2016 Mateusz Golicz, http://jaskinie.jaszczur.org
Distributed under the terms of the GNU General Public License v2
'''

import inkex
import simpletransform

from speleo import SpeleoEffect, SpeleoTransform
from speleo_randstones import SpeleoRandstones

class SpeleoFind2(SpeleoRandstones):
  def initOptions(self):
    self.OptionParser.add_option("--group",
        action="store", type="inkbool", 
        dest="group", default=True)
    self.OptionParser.add_option("--replace",
        action="store", type="string", 
        dest="replace", default="")
  
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
    
    # Is this the right symbol?
    if href == sel:
      # Move to our group
      if group <> None:
        # Get total transform of this symbol
        transform = SpeleoTransform.getTotalTransform(node)
        
        # Group it together with others
        group.append(node)

        # Reset this node transform
        node.set("transform", simpletransform.formatTransform(
                    simpletransform.composeTransform(correctiveTransform, transform)
              ))
      
      # Did anyone order a replace?
      if self.options.replace:
        node.set(inkex.addNS('href', 'xlink'), '#' + self.options.replace)
                
  def effect(self):
    # Initialize symbol knowledge
    self.initSymbols()
    
    if self.options.replace:
      self.ensureSymbol(self.options.replace)

    symbol_ids = []
    # Go through all selected ...
    for id, obj in self.selected.iteritems():
      # Get unique symbol IDs
      symbol_ids.append(obj.get(inkex.addNS("href", "xlink")))
    
    # For all found distinct symbol IDs ...
    for link in set(symbol_ids):
      # Perhaps not a symbol? 
      if link == None: continue
      
      if self.options.group:
        # Create a group
        group = inkex.etree.SubElement(self.currentLayer(), "g", {"style": "stroke:black; stroke-width: 0.28mm;"})
        
        # Compute corrective transform
        correctiveTransform = SpeleoTransform.invertTransform(SpeleoTransform.getTotalTransform(group))
      else:
        # No group, no transform!
        group = None
        correctiveTransform = None
      
      # Look for our symbols!
      self.scanTree(self.document.getroot(), link, group, correctiveTransform)

if __name__ == '__main__':
  e = SpeleoFind2()
  e.affect()

