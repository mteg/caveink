# -*- coding: utf-8 -*-
'''
Uses the 'text along path' feature to quickly style paths
into step symbols, dripline etc.

Needs the Speleo Sans font, version 2+!

Copyright (C) 2013 Mateusz Golicz, http://jaskinie.jaszczur.org
Distributed under the terms of the GNU General Public License v2
'''

# Now that inkscape uses symbols, probably we can get rid of the SpeleoUIS font.
# Just need to find suitable glyphs in Unicode :)

import inkex
from speleo import SpeleoEffect, SpeleoTransform

class SpeleoLine(SpeleoEffect):
  def initOptions(self):
    self.OptionParser.add_option("--fontsize",
        action="store", type="float", 
        dest="fontsize", default=6)
    self.OptionParser.add_option("--fontstroke",
        action="store", type="float", 
        dest="fontstroke", default=0.2)
    self.OptionParser.add_option("--linetype",
        action="store", type="int", 
        dest="linetype", default=1)
    self.OptionParser.add_option("--linewidth",
        action="store", type="float", 
        dest="linewidth", default=0.5)
    self.OptionParser.add_option("--char",
        action="store", type="string", 
        dest="char", default=1)
  
  def testFix(self, node, replaceLine = False):
    # Get children of this node
    children = node.getchildren()
      
    # See if this can be a station?
    if len(children) == 2:
      if children[0].tag == inkex.addNS('text','svg') and children[1].tag == inkex.addNS('path','svg') and children[0].get("class") == "speleoLine":
        return self.fixLine(node, children[0], children[1], replaceLine)
      elif children[1].tag == inkex.addNS('text','svg') and children[0].tag == inkex.addNS('path','svg') and children[1].get("class") == "speleoLine":
        return self.fixLine(node, children[1], children[0], replaceLine)
    
    return False

  
  def scanTree(self, node):
    if self.testFix(node): return      
    for child in node:
      self.scanTree(child)
  
  def fixLine(self, grp, text, path, replaceLine = False):
    if replaceLine:
      grp.remove(text)
      self.makeLine(path, grp)
    else:
      tch = text.getchildren()
      if len(tch) == 1:
        if tch[0].tag == inkex.addNS('textPath', 'svg'):
          tch[0].set(inkex.addNS('href', 'xlink'), '#' + path.get("id"))
          return True
    return False
  
  def makeLine(self, node, grp = None):
    if node.tag != inkex.addNS("path", "svg"):
      return False

    t = self.options.linetype
    

    tr = SpeleoTransform.getTotalTransform(node.getparent())
    parent_scale = (tr[0][0] + tr[1][1]) / 2.0

    tr = SpeleoTransform.getTotalTransform(node)
    this_scale = (tr[0][0] + tr[1][1]) / 2.0

    fontsize = self.options.fontsize / parent_scale
    linewidth = self.options.linewidth / this_scale
    fontstroke = self.options.fontstroke / parent_scale

    if t == 1:
      line_style = 'stroke:#000000;stroke-width:%.3fmm;fill:none' % linewidth
      text_style = 'font-size:%.3fpt' % fontsize
      text = self.char * 100 
    elif t == 2:
      line_style = 'stroke:#000000;fill:none;stroke-width:0.5mm;stroke-opacity:0.005'
      text_style = 'font-size:%.3fpt;stroke:#000000;stroke-width:%.3fmm' % (fontsize, fontstroke)
      text = self.char * 100 
    

    node.set('style', line_style)
    tx = inkex.etree.Element('text', {"class": "speleoLine"})
    tp = inkex.etree.Element('textPath')
    tspan = inkex.etree.Element('tspan')

    tp.set(inkex.addNS('href', 'xlink'), '#' + node.get("id"))
    tspan.set('style', 'font-family:Speleo3;-inkscape-font-specification:Speleo3;' + text_style)
    tspan.text = text

    tp.append(tspan)
    tx.append(tp)
    
    if grp == None: grp = inkex.etree.SubElement(node.getparent(), "g")
    tx.set(inkex.addNS('insensitive', 'sodipodi'), 'true')
    grp.append(node)
    grp.append(tx)
    return True
  
  def effect(self):
    self.char = ['', '!', '{', '}', '(', ')', '<', '^'][int(self.options.char)]
    for id, node in self.selected.iteritems():
      if self.testFix(node.getparent(), True): continue
      if self.testFix(node, True): continue
      if self.makeLine(node): continue
      self.scanTree(node)

if __name__ == '__main__':
  e = SpeleoLine()
  e.affect()

