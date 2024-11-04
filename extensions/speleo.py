# -*- coding: utf-8 -*-
'''
Generic utility functions for the inkscape cave map drawing extensions.

Copyright (C) 2013, 2016 Mateusz Golicz, http://jaskinie.jaszczur.org
Distributed under the terms of the GNU General Public License v2
'''

import inkex
import simpletransform
import simplestyle
import logging
import copy

class SpeleoTransform:
  '''
  Some SVG Transform utilities not covered by simpletransform
  '''

  Identity = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
  
  @staticmethod
  def invertTransform(transform):
    '''
    Compute inverse of transform
    '''
    (a, b, c) = transform[0]
    (d, e, f) = transform[1]
    
    # Formulas for inverting a 3x3 matrix; see SVG specification for more details
    det = a*e - b*d
    inverse = [[e/det, -b/det, (b*f - c*e)/det], [-d/det, a/det, (c*d - a*f)/det]]
    
    return inverse	

  @staticmethod
  def getTransform(node):
    tr = node.get("transform")
    if tr:
      return simpletransform.parseTransform(tr)
    else:
      return SpeleoTransform.Identity

  @staticmethod
  def getTotalTransform(node):
    '''
    Shorthand method that is lacking in simpletransform
    '''
    if node.tag == inkex.addNS("svg", "svg"): return SpeleoTransform.Identity
#    return simpletransform.composeParents(node, SpeleoTransform.Identity)
    return node.composed_transform().matrix
    
  @staticmethod
  def transformCoords(pt, a):
    '''
    Shorthand method that is almost there in simpletransform
    '''
    nx = a[0][0] * pt[0] + a[0][1] * pt[1] + a[0][2]
    ny = a[1][0] * pt[0] + a[1][1] * pt[1] + a[1][2]
    return (nx, ny)
  

class SpeleoEffect(inkex.Effect):
  '''
  Generic effect class, shared by other "speleo" effects
  '''

  try:
    inkex.Effect.unittouu
  except AttributeError:
    unittouu = inkex.unittouu
  
  def __init__(self):
    inkex.Effect.__init__(self)
    self.arg_parser.add_argument("--debug",
          action="store", type=str, 
          dest="debug", default="")
    self.initOptions()
  
  def initOptions(self):
    '''
    Configure option parser for this particular effect
    '''
    # This is abstract
    pass
  
  def currentLayer(self):
    '''
    Get the 'nearest' true layer (ie. not a group or something)
    '''
    layer = self.svg.get_current_layer()
    if layer == None: return self.getRoot()
    while True:
      groupmode = layer.get(inkex.addNS('groupmode', 'inkscape'))
      if groupmode == 'layer':
              break
      parent = layer.getparent()
      if parent == None:
              break
      layer = parent
    return layer

  def getStyleProp(self, node, key, default = ''):
    '''
    Get contents of a style key of a node, if it is set. Otherwise, 
    return some default string.
    '''
    style = node.get('style')
    if style:
      style = dict(inkex.Style.parse_str(style))
      if key in style:
        return style[key]
    return default
  
  def setStyleProp(self, node, key, value):
    '''
    Set contents of a style key of a node
    '''
    style = node.get('style')
    if style:
            style = dict(inkex.Style.parse_str(style))
    else:
            style = {}
    style[key] = value
    node.set('style', simplestyle.formatStyle(style))

  
  def hasDisplayNone(self, node):
    '''
    Shorthand method for testing layer visiblity
    '''
    return (self.getStyleProp(node, 'display') == 'none')
  
  def log(self, text):
    '''
    Shorthand method for logging
    '''
    logging.debug(text)
    
  def getRoot(self):
    '''
    Shorthand method for getting root
    '''
    return self.document.getroot()
 
  def getDocScale(self):
    '''
    Get scale factors to take into account
    
    viewbox / docsize = 35.4 = 90 / 25.4
    '''
    docScale = 1 / self.uutounit(1, 'mm')
    
    node = self.getRoot()
    viewBox = node.get('viewBox')
    viewBox = [float(i) for i in viewBox.split()]
    doc_width = self.unittouu(node.get('width', viewBox[2]))
    doc_height = self.unittouu(node.get('height', viewBox[3]))
    
    docScale /= (doc_width / viewBox[2] + doc_height / viewBox[3]) / 2
    return docScale
    
  
  def getDefs(self):
    '''
    Shorthand method for getting the document defs
    '''
    try:
      defs = self.xpathSingle('/svg:svg//svg:defs')
    except Exception:
      # Works, but raises a stupid warning - how to fix?
      defs = None
    
    if defs == None:
      defs = inkex.etree.SubElement(self.getRoot(), "defs")
    
    return defs

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

  
  def isLayer(self, node):
    '''
    Shorthand method for identifying a layer
    '''
    return node.get(inkex.addNS('groupmode', 'inkscape')) == 'layer' 

  def removeAttrib(self, node, attrib):
    '''
    Remove an attribute from XML node
    '''
    if attrib in node.attrib:
      node.attrib.pop(attrib)
  
  def safelyMoveTo(self, node, parent, doCopy = False):
    '''
    Move a node, preserving its position in absolute coordinates
    '''
    oldParentTr = SpeleoTransform.getTotalTransform(node.getparent())
    newParentTr = SpeleoTransform.getTotalTransform(parent)
    if doCopy: node = copy.deepcopy(node)
    simpletransform.applyTransformToNode(oldParentTr, node)
    simpletransform.applyTransformToNode(SpeleoTransform.invertTransform(newParentTr), node)
    parent.append(node)
    return node

  def safelyCopyTo(self, node, parent):
    '''
    Copy a node, preserving its position in absolute coordinates
    '''
    return self.safelyMoveTo(node, parent, True)
  
  def getElementById(self, id):
    try:
      return self.xpathSingle("//*[@id='%s']" % id)
    except:
      return None
