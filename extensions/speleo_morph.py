# -*- coding: utf-8 -*-
'''
Inkscape plugin for morphing maps to surveying stations a'la Therion

Useful if you need to update your map after closing a survey loop
or detecting a blunder.

Copyright (C) 2016 Mateusz Golicz, http://jaskinie.jaszczur.org
Distributed under the terms of the GNU General Public License v2
'''

import math
import sys
import inkex
import simpletransform
import logging
import simplepath
import copy
from speleo_kdtree import KDTree
from speleo import SpeleoEffect, SpeleoTransform

class StationStore:
  '''
  Class for storing planar station coordinates and for looking up stations
  closest to a particular position on the drawing.
  '''

  def log(self, text):
    '''
    Shorthand method for logging
    '''
    logging.debug(text)

  def getText(self, node):
    '''
    Get a flattened text out of a <text> SVG node
    '''
    out = ""
    # Does the node itself have an inner textual content?
    if node.text != None: out += node.text
    
    # We might have even more content in <tspan>s 
    for span in node:
      if span.tag == inkex.addNS('tspan','svg'):
        if span.text != None: out += span.text

    return out

  def saveStation(self, marker, caption):
    '''
    Retrieve station data from SVG elements and store it
    '''
    
    # Get station name from the caption object
    name = self.getText(caption)
    
    # Perhaps it's not a station, but rather a prefix indication
    if name[:3] == "***": 
      self.prefix = name[3:]
      return 1

    # Get absolute marker coordinates
    coords = SpeleoTransform.transformCoords((float(marker.get("x")), float(marker.get("y"))), SpeleoTransform.getTotalTransform(marker))
    self.log("Station %s has coordinates %.2f, %.2f" % (name, coords[0], coords[1]))
    
    # Save the station
    self.dict[name] = coords
    return True

                                
  def findStations(self, node, recursion = -1):
    '''
    (Possibly recursively) find stations within a SVG layer.
    
    For this extension, all groups that consist of exactly one
    marker and one text element are a surveying station.
    '''
    
    # Get children of this node
    children = node.getchildren()
    
    # See if this can be a station?
    if len(children) == 2:    
      if children[0].tag == inkex.addNS('text','svg') and children[1].tag == inkex.addNS('use','svg'):
        return self.saveStation(children[1], children[0])
      elif children[1].tag == inkex.addNS('text','svg') and children[0].tag == inkex.addNS('use','svg'):
        return self.saveStation(children[0], children[1])
    
    # Not a station, let's dig deeper (if ordered)
    if recursion > 0 or recursion < 0:
      for obj in children:
        if self.findStations(obj, recursion - 1):
          # Since findStations returns true if a station is detected, by this assignment 
          # we get the topmost group that contains stations
          self.stationLayer = node
            
    return False

  def findClosest(self, x0, y0, n = 1):
    '''
    Use a k,d-tree to find station(s) closest to specific coordinates on the map
    '''
    # Query the k,d-tree
    dist, index = self.kd.query((x0, y0), n);
    
    # Find the station ID in a way dependant on the query size
    if n == 1:
      return [(self.stationList[index], dist)]
    else:
      return [(self.stationList[idx], dist[n]) for n, idx in enumerate(index)]
  
  def findDistinctClosest(self, x0, y0, n = 1):
    '''
    Find closest n DISTINCT stations
    '''
    m = n
    while m <= (len(self.stationList) * 2) or m == n:
      # Query the k,d-tree
      kd = self.findClosest(x0, y0, m)
      
      # See how many different stations are there
      stationsPresent = {}
      result = []
      for name, dist in kd:
        if not name in stationsPresent:
          stationsPresent[name] = True
          result.append((name, dist))
      
      # Do we have enough?
      if len(result) >= n:
        return result[:n]
      
      # No? Sorry ...
      m *= 2
    
    # Cannot satisfy
    return kd
      
                        
  def buildKD(self):
    '''
    Build a k,d-tree for all loaded stations
    '''
    self.kd = KDTree(list(self.dict.values()))
    
    # Make an index for resolving queries
    self.stationList = self.dict.keys()

    # Resolve references
    for idx, name in enumerate(self.stationList):
      self.log(name)
      if name[:3] == "-->":
        self.log("Resolving reference " + name)
        # Get referenced station
        ref = name[3:].strip()
        
        # Add only if we can resolve it
        if ref in self.dict:
          self.stationList[idx] = ref
        else:
          sys.stderr.write("Cannot resolve station " + name)


  def __init__(self, layer, recursive = True):
    '''
    Initialize a station storage object, loading stations from an XML node
    '''
    # Reset stuff
    self.dict = {}
    self.stationLayer = None
    self.prefix = None
    
    # Look for stations
    self.findStations(layer, -1 if recursive else 1)
    
    
    # Did we find a prefix on the way?
    if self.prefix <> None:
      # Need to rename everything, sorry
      old_dict = self.dict
      self.dict = {}
      for k, v in old_dict.iteritems():
        if k[:3] == "-->":
          self.dict["-->" + self.prefix + k[3:].strip()] = v
        else:
          self.dict[self.prefix + k] = v

class SpeleoMorph(SpeleoEffect):
  def initOptions(self):
    self.OptionParser.add_option("--replace",
        action="store", type="inkbool", 
        dest="replace", default=False)
    self.OptionParser.add_option("--parent",
        action="store", type="string", 
        dest="parent", default="root")
    self.OptionParser.add_option("--mode",
        action="store", type="string", 
        dest="mode", default="followNearestTwo")  
    self.OptionParser.add_option("--scale",
        action="store", type="inkbool", 
        dest="scale", default=True)  
    self.OptionParser.add_option("--rotate-symbols",
        action="store", type="inkbool", 
        dest="rotate", default=True)  
        
  def getTransformed(self, x, y, src, dst, t, node = None):
    '''
    Transform local coordinates into new local coordinates
    '''
    # Compute absolute coordinates
    (gx, gy) = SpeleoTransform.transformCoords((x, y), t)
    
    # Compute new coordinates using transformation method of choice
    (nx, ny, angle) = self.transformCoordinates(gx, gy, src, dst)
          
    # If nothing changed, return old local coordinates
    if nx == gx and ny == gy and angle == 0: return (x, y)

    # ... so that we do not waste time on inverting transforms
    
    # Invert transform
    it = SpeleoTransform.invertTransform(t)
    
    # See if we need to rotate a symbol...
    if angle <> 0 and node <> None:
      # Maybe it needs rotation!
      if node.tag == inkex.addNS("use", "svg") and self.options.rotate:
        name = node.get(inkex.addNS("href", "xlink"))[1:]
        if name in [
          "gradient", "mini-gradient", "source", "sink", "water", "draft", "paleoflow", "scallops",
          "grgradient", "grmini-gradient", "grsource", "grsink", "grwater", "grdraft", "grpaleoflow", "grscallops"]:
          
          # Invert original node transform
          simpletransform.applyTransformToNode(it, node)

          # Apply rotation
          simpletransform.applyTransformToNode(simpletransform.parseTransform("rotate(" + str(angle) + ")"), node)
          
          # Go back
          simpletransform.applyTransformToNode(t, node)
     
    
    # Go back to local coordinate system
    return SpeleoTransform.transformCoords((nx, ny), it)

  def transformCoordinates_PlainShift(self, gx, gy, src, dst):
    '''
    Shift everything uniformly
    '''
    
    # Do we already know the offset?
    if self.goffs <> None:
      # Yes! Just apply it.
      return (gx + self.goffs[0], gy + self.goffs[1], 0)
    
    # Find out the offset by a slightly "better" method
    (nx, ny) = self.transformCoordinates_KeepToClosest(gx, gy, src, dst)
    
    # If there is any offset...?
    if nx != gx or ny != gy:
      # Remember it!
      self.goffs = [nx - gx, ny - gy]
    
    # ... and apply!
    return (nx, ny, 0)

  def transformCoordinates_KeepToClosest(self, gx, gy, src, dst):
    '''
    Keep constant bearing and distance from closest station
    '''
    # Find the closest station
    neigh = src.findDistinctClosest(gx, gy, 1)
    
    # There has to be one? Just one!
    if len(neigh) <> 1: return (gx, gy, 0)
    
    # Get name and distance...
    (st, dist) = neigh[0]
    
    # Does not exist in target centerline? Keep in place then!
    if not st in dst.dict: return (gx, gy, 0)
    
    # See how this station moved between the centerlines...
    (sx, sy) = src.dict[st]
    (dx, dy) = dst.dict[st]
    ox = dx - sx
    oy = dy - sy
    
    # Let's not bother with details
    if abs(ox) < 1e-5 and abs(oy) < 1e-5: return (gx, gy, 0)
    
    # Apply the offset to supplied coordinates
    return (gx + ox, gy + oy, 0)

  def transformCoordinates_NearestTwo(self, gx, gy, src, dst):
    # Need two neighbors for this trick
    neigh = src.findDistinctClosest(gx, gy, 2)
    if len(neigh) <> 2: return (gx, gy, 0)
    
    # Get close and far neighbor
    (cn, cdist) = neigh[0]
    (fn, fdist) = neigh[1]
    
    # If any of them is not present in dst, do not move
    if (cn not in dst.dict) or (fn not in dst.dict): return (gx, gy, 0)
    
    # Get neighbor coordinates
    (scnx, scny) = src.dict[cn]
    (sfnx, sfny) = src.dict[fn]
    (dcnx, dcny) = dst.dict[cn]
    (dfnx, dfny) = dst.dict[fn]
    
    # Compute neighbor distances in source and destination
    snd = math.sqrt((scnx - sfnx) ** 2 + (scny - sfny) ** 2)
    dnd = math.sqrt((dcnx - dfnx) ** 2 + (dfny - dcny) ** 2)
    
    # If neighbors are in the same place, do not move
    if snd < 1e-5 or dnd < 1e-5: return (gx, gy, 0)
    
    # Get bearing difference between the survey leg on both drawings
    rot_by = math.atan2(dfny - dcny, dfnx - dcnx) - math.atan2(sfny - scny, sfnx - scnx)
    
    # Get vector to point from closer neighbor @ source
    ox = gx - scnx
    oy = gy - scny
    
    # Scale this vector
    if self.options.scale:
      ratio = dnd / snd
      ox *= ratio
      oy *= ratio
    
    # Rotate this vector by the bearing difference
    (ox, oy) = (ox * math.cos(rot_by) - oy * math.sin(rot_by), ox * math.sin(rot_by) + oy * math.cos(rot_by))
    
    # Compute new point position
    return (ox + dcnx, oy + dcny, rot_by / math.pi * 180)
                
  def rectifyPath(self, path, src, dst, tr):
    '''
    Transform all path nodes
    '''
    # Go through all 'd=' commands...
    for m, args in path:
      # If we have at least two args ...
      if len(args) >= 2:
        n = 0
        # For every pair of args...
        while (n+1) < len(args):
          # Transform the pair!
          (args[n], args[n+1]) = self.getTransformed(args[n], args[n+1], src, dst, tr)
          n = n + 2


  def rectify(self, src, dst, node, centerline):
    '''
    Recursively transform objects from old to new centerline
    '''
    # Skip invisible layers
    if self.hasDisplayNone(node): return

    # Skip layers with centerlines and the defs object
    if node == centerline: return
    if node == self.dst: return
    if node.tag == inkex.addNS('defs', 'svg'): return
          
    # If it's a path ...
    if node.tag == inkex.addNS('path','svg'):
      # Parse path data
      path = simplepath.parsePath(node.get("d"))
      
      # Get absolute transform
      tr = SpeleoTransform.getTotalTransform(node)
      
      # Rectify the path
      self.rectifyPath(path, src, dst, tr)
      
      # Re-set path data
      node.set("d", simplepath.formatPath(path))
      
      # Remove attributes that break our efforts
      self.removeAttrib(node, inkex.addNS("path-effect", "inkscape"))
      self.removeAttrib(node, inkex.addNS("original-d", "inkscape"))
      self.removeAttrib(node, inkex.addNS("type", "sodipodi"))
      
      return
    elif node.get("x") <> None and node.tag == inkex.addNS("use", "svg"):
      # Handle symbols
      tr = SpeleoTransform.getTotalTransform(node)
      
      # Convert and set new coordinates
      (x, y) = self.getTransformed(float(node.get("x")), float(node.get("y")), src, dst, tr, node)
      
      simpletransform.applyTransformToNode(simpletransform.parseTransform("translate(" + str(x) + "," +str(y) + ")"), node)
      node.set("x", "0")
      node.set("y", "0")
    elif node.get("x") <> None:
      # Generic handler for nodes having x & y coordinates
      tr = SpeleoTransform.getTotalTransform(node)
      
      # Convert and set new coordinates
      (x, y) = self.getTransformed(float(node.get("x")), float(node.get("y")), src, dst, tr, node)
      
      node.set("x", str(x))
      node.set("y", str(y))
    elif node.get("cx") <> None:
      # Generic handler for nodes having x & y coordinates as cx/cy
      tr = SpeleoTransform.getTotalTransform(node)
      
      # Convert and set new coordinates
      (x, y) = self.getTransformed(float(node.get("cx")), float(node.get("cy")), src, dst, tr)
      node.set("cx", str(x))
      node.set("cy", str(y))
                          
    # Go deeper                
    for child in node.getchildren():
      self.rectify(src, dst, child, centerline)

  def findCenterlineLayers(self, parent, list):
    '''
    Recursively find leaf layers containing centerlines in them
    '''
    childLayerCount = 0
    
    for node in parent.getchildren():
      # Not a layer? Bye!
      if not self.isLayer(node): continue
      
      # Invisible? Bye!
      if self.hasDisplayNone(node): continue
      
      # Target centerline? Bye!
      if node == self.dst: continue
      
      # Report that we have layers down here...
      childLayerCount += 1
      
      # Recurse, seeing if it has any sub-layers?
      if self.findCenterlineLayers(node, list) == 0:
        # No! It's a leaf layer! Great! See if it has any stations ...
        ss = StationStore(node)
        if len(ss.dict) > 0:
          # It has - add it to our list
          list.append((node, ss))
          
    return childLayerCount
                
  
  def effect(self):
    # Configure self.logging
    if len(self.options.debug): logging.basicConfig(level = logging.DEBUG)
          
    # Configure morphing method
    if self.options.mode == "followNearestTwo":
      self.transformCoordinates = self.transformCoordinates_NearestTwo
    elif self.options.mode == "keepToClosest":
      self.transformCoordinates = self.transformCoordinates_KeepToClosest
    else:
      self.goffs = None
      self.transformCoordinates = self.transformCoordinates_PlainShift

    # Get current layer - needs to hold the target centerline
    dst = self.currentLayer()
    if dst == None: return
    self.dst = dst

    # Process stations from the target
    dstStations = StationStore(dst)

    # Find all other layers that have stations in them
    centerLines = []
    self.findCenterlineLayers(self.document.getroot(), centerLines)
                
    # Go through all of the centerlines (other than target)
    for (src, srcStations) in centerLines:
      # Build nearest-neighbor lookup tree
      srcStations.buildKD()
      
      # TODO Huge trouble possible if two centerlines share a parent
      
      # Move objects referenced to this centerline
      self.rectify(srcStations, dstStations, src.getparent(), src)
      
      if self.options.replace:
        # Duplicate new centerline into old layer, if requested

        # Remove all that was there
        for ch in src:
          src.remove(ch)

        # Add copies of new cl
        for ch in dst:
          src.append(copy.deepcopy(ch))
        
        # TODO could copy only stations that are present in src!

          
if __name__ == '__main__':
  e = SpeleoMorph()
  e.affect()

