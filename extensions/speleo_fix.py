# -*- coding: utf-8 -*-
'''
Inserts missing cave map symbols into a SVG file.

Copyright (C) 2016 Mateusz Golicz, http://jaskinie.jaszczur.org
Distributed under the terms of the GNU General Public License v2
'''

import inkex
import os
import sys
from lxml import etree

from speleo import SpeleoEffect, SpeleoTransform
from speleo_line import SpeleoLine

class SpeleoFix(SpeleoLine):
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
      print "Error"
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
      self.loadSymbols("cave_symbols.svg")
      self.loadSymbols("cave_symbols_unstyled.svg")
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

  def initSymbols(self):
    self.extSymbols = None
    self.ownSymbols = {}
    
    # Load our own symbols
    self.defs = self.scanDefs(self.document, self.ownSymbols)

  def processTree(self, node):
    # Is this a SpeleoLine we can fix?
    if self.testFix(node): return
    
    # Then, perhaps an orphaned immutable text!
    if inkex.addNS("text", "svg") == node.tag:
      ins = inkex.addNS("insensitive", "sodipodi")
      if ins in node.attrib:
        if node.get(ins) == "true":
          node.getparent().remove(node)    
          return

    # Recurse first
    for child in node:
      self.processTree(child)
      
    # Is this a symbol reference?
    if node.tag == inkex.addNS("use", "svg"):
      # Get the symbol ID
      href = node.get(inkex.addNS('href', 'xlink'))
      if href[0] == "#":
        # Make sure it's there!
        self.ensureSymbol(href[1:])
    
  def processDefs(self, defs):
    '''
    Fixes references to stock patterns
    '''
    
    # First pass - collect stock patterns definitions and duplicate stock patterns
    stockPatterns = {}
    toReplace = {}
    for i in defs:
      # If not a pattern, it's not interesting
      if i.tag <> inkex.addNS("pattern", "svg"): continue
      
      # If not a stock pattern, it's not interesting
      if not (inkex.addNS("stockid", "inkscape")) in i.attrib: continue
      
      # Get stock pattern ID
      stockid = i.get(inkex.addNS("stockid", "inkscape"))
      
      # Already encountered?
      if stockid in stockPatterns:
        # Yes - let's get rid of it!
        toReplace[i.get("id")] = stockPatterns[stockid]
      else:
        # No - insert into stock pattern dictionary
        stockPatterns[stockid] = i.get("id")
    
    # Second pass - remove all garbage and replace references
    for i in defs:
      # If not a pattern, it's not interesting
      if i.tag <> inkex.addNS("pattern", "svg"): continue
      
      # Does it reference other pattern?
      if inkex.addNS("href", "xlink") in i.attrib:
        # See if the reference needs replacing
        ref = i.get(inkex.addNS("href", "xlink"))
        if ref[1:] in toReplace:
          i.set(inkex.addNS("href", "xlink"), "#" + toReplace[ref[1:]])
        # Do not process further
        continue
      
      # Is it on our replacement list?
      if i.get("id") in toReplace:
        # We do not need it any more, sorry
        defs.remove(i)
    
  def effect(self):
    # Initialize symbol knowledge
    self.initSymbols()
    
    # Process the tree
    self.processTree(self.getRoot());
    
    # Process defs
    self.processDefs(self.getDefs());
      
if __name__ == '__main__':
  e = SpeleoFix()
  e.affect()
