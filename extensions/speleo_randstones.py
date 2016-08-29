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
from lxml import etree

from speleo import SpeleoEffect, SpeleoTransform

class SpeleoRandstones(SpeleoEffect):
  def scanDefs(self, file, index):
    '''
    Index direct children of a <defs> element in an SVG tree by their ID
    '''
    
    # Find the <defs> element
    try:
      defs = file.xpath('/svg:svg//svg:defs', namespaces=inkex.NSS)[0]
    except Exception: 
      return None
    
    # Iterate through all direct children
    for node in defs:
      index[node.get("id")] = node
    
    return defs
  
  def loadSymbols(self, file):
    '''
    Try loading symbols from <defs> in an external file into self.extSymbols
    '''
    try:
      # Open the symbol file
      fh = open(os.path.join(os.path.dirname(__file__), "..", "symbols", file), "r")
      
      # Parse XML
      p = etree.XMLParser(huge_tree=True)
      
      # Load symbols
      self.scanDefs(etree.parse(fh, parser=p), self.extSymbols)
      
    except Exception:
      pass
  
  def ensureSymbol(self, id):
    '''
    See that current document has symbol with id = id
    
    If it is not present in <defs>, try adding it from our symbol libraries
    If it cannot be added, return False (otherwise True)
    '''
    
    # Perhaps it's in our own <defs>?
    if id in self.ownSymbols: return True
    
    # Nope. Did we already load our symbol libraries?
    if self.extSymbols == None:
      # No. Let's load them.
      self.extSymbols = {}
      self.loadSymbols("cave_rocks.svg")
      self.loadSymbols("cave_rocks_gray.svg")
      self.loadSymbols("cave_rocks_unstyled.svg")
      
    # Is that symbol really available in one of our libraries?
    if not (id in self.extSymbols): return False

    # Append it to our own <defs>
    self.defs.append(self.extSymbols[id])
    
    # Mark that we have it, in case we are asked again.
    self.ownSymbols[id] = self.extSymbols[id]
    
    # All is well
    return True

  def processTree(self, node):
    '''
    Recursively walk the SVG tree and randomize all rock/pebble symbols on the way
    '''
    
    # Is this a symbol reference?
    if node.tag == inkex.addNS('use', 'svg'):
      # Is this one of our rock/pebble symbols?
      m = re.match('#(gr|un|)?([ra])b([0-9]+)[a-z]', str(node.get(inkex.addNS("href", "xlink"))))
      if m:
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
    self.extSymbols = None
    self.ownSymbols = {}
    
    # Load our own symbols
    self.defs = self.scanDefs(self.document, self.ownSymbols)
    
    # Recursively process everything selected
    for id, node in self.selected.iteritems():
      self.processTree(node);
      
if __name__ == '__main__':
  e = SpeleoRandstones()
  e.affect()
