# -*- coding: utf-8 -*-
'''
Inkscape plugin for randomly rotating stones on cave maps

Copyright (C) 2013, 2016 Mateusz Golicz, http://jaskinie.jaszczur.org
Distributed under the terms of the GNU General Public License v2
'''

import inkex
import simpletransform
import string
import random
import re
from speleo_fix import SpeleoFix
from speleo import SpeleoTransform

class SpeleoRandstones(SpeleoFix):
  def processTree(self, node):
    '''
    Recursively walk the SVG tree and randomize all rock/pebble symbols on the way
    '''
    
    # Is this a symbol reference?
    if node.tag == inkex.addNS('use', 'svg'):
      # Is this one of our rock/pebble symbols?
      m = re.match('#(gr|un|)?([ra])b([0-9]+)[a-z]', str(node.get(inkex.addNS("href", "xlink"))))
      if m:
        # Add translation, if present
        x = float(node.get("x"))
        y = float(node.get("y"))
        
        if x <> 0 or y <> 0:
          node.set("x", "0")
          node.set("y", "0")
          currentTr = node.get("transform")
          if currentTr == None: currentTr = ""
          node.set("transform", currentTr + (" translate(%.6f, %.6f) " % (x, y)))

        # Get current symbol transform
        tr = SpeleoTransform.getTotalTransform(node)
        
        # Move it back to 0,0 for rotation
        simpletransform.applyTransformToNode(SpeleoTransform.invertTransform(tr), node)

        # Select a new, random symbol ID (matching the symbol family)
        new_id = m.group(1) + m.group(2) + "b" + m.group(3) + random.choice("abcdefghij")
        
        # Make sure the new symbol type is with us
        if self.ensureSymbol(new_id):
          node.set(inkex.addNS("href", "xlink"), "#" + new_id)
          # If not, we just leave the type as it is.

        # Apply random rotation
        simpletransform.applyTransformToNode(simpletransform.parseTransform("rotate(" + str(random.randint(0, 359)) + ")"), node)
        
        # Return the symbol to where it was
        simpletransform.applyTransformToNode(tr, node)


    # For compatibility with old maps, using speleoUIS3
    if (node.tag == inkex.addNS('tspan', 'svg') or node.tag == inkex.addNS('text', 'svg')) and node.text:
      if len(node.text) == 1:
        if node.text in string.ascii_lowercase:
          node.text = random.choice(string.ascii_lowercase)
        elif node.text in string.ascii_uppercase:
          node.text = random.choice(string.ascii_uppercase)
        if (node.text in string.ascii_letters):
          node.set("rotate",  str(random.randint(0, 359)))

    # Recurse!
    for child in node:
      self.processTree(child);
    
  def effect(self):
    # Initialize symbol knowledge
    self.initSymbols()
    
    # Recursively process everything selected
    for id, node in self.selected.iteritems():
      self.processTree(node);
      
if __name__ == '__main__':
  e = SpeleoRandstones()
  e.affect()
