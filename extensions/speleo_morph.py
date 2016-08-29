# -*- coding: utf-8 -*-
'''
Copyright (C) 2008 Thomas Holder, http://sf.net/users/speleo3/
Distributed under the terms of the GNU General Public License v2
'''

import math
import inkex
import simpletransform
import speleo_grid
import simplestyle
import logging
import simplepath
import sys
import copy
from kdtree import KDTree

log = logging.debug

class StationStore:
        def getText(self, node):
                out = ""
                if node.text != None: out += node.text
                for span in node:
                        if span.tag == inkex.addNS('tspan','svg'):
                                if span.text != None: out += span.text
                return out

        def gotStation(self, marker, caption):
                name = self.getText(caption)
                a = simpletransform.composeParents(marker, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
                x = float(marker.get("x"))
                y = float(marker.get("y"))
                nx = a[0][0] * x + a[0][1] * y + a[0][2]
                ny = a[1][0] * x + a[1][1] * y + a[1][2]
                
                if name[:3] == "***": 
                        # We have a prefix!
                        self.prefix = name[3:]
                        return 1
                
                log("Station %s has coordinates %.2f, %.2f" % (name, nx, ny))
                self.dict[name] = (nx, ny)
                
                return 1

                                
        def findStations(self, node, recursion = -1):
                children = node.getchildren()
                
                # See if this can be a station?
                if len(children) == 2:
                        if children[0].tag == inkex.addNS('text','svg') and children[1].tag == inkex.addNS('use','svg'):
                                return self.gotStation(children[1], children[0])
                        elif children[1].tag == inkex.addNS('text','svg') and children[0].tag == inkex.addNS('use','svg'):
                                return self.gotStation(children[0], children[1])

                if recursion > 0 or recursion < 0:
                        # If not, go and recurse
                        for obj in children:
                                if self.findStations(obj, recursion - 1) == 1:
                                        # We get the topmost layer with stations this way
                                        self.stationLayer = node
                        
                return 0

        def findClosestA(self, x0, y0):
                closestCandidate = None
                closestDistance = 0
                for id, (x, y) in self.dict.iteritems():
                        dist = math.sqrt((x0 - x) ** 2 + (y0 - y) ** 2)
                        if closestCandidate == None or dist < closestDistance:
                                closestCandidate = id
                                closestDistance = dist
                
                return closestCandidate
       
        def findClosest(self, x0, y0, n = 1):
                dist, index = self.kd.query((x0, y0), n);
                if n == 1:
                        return [(self.stationList[index], dist)]
                else:
                        return [(self.stationList[idx], dist[n]) for n, idx in enumerate(index)]
                        
        def buildKD(self):
                self.kd = KDTree(list(self.dict.values()))
                self.stationList = self.dict.keys()

        def __init__(self, layer, recursive = True):
                self.dict = {}
                self.stationLayer = None
                self.prefix = None
                self.findStations(layer, -1 if recursive else 1)
                
                if self.prefix <> None:
                        # Need to rename everything, sorry
                        old_dict = self.dict
                        self.dict = {}
                        for k, v in old_dict.iteritems():
                                self.dict[self.prefix + k] = v

class SpeleoMorph(speleo_grid.SpeleoEffect):
	def __init__(self):
		inkex.Effect.__init__(self)
		self.OptionParser.add_option("--debug",
				action="store", type="string", 
				dest="debug", default="")
		self.OptionParser.add_option("--replace",
				action="store", type="inkbool", 
				dest="replace", default=False)
		self.OptionParser.add_option("--parent",
				action="store", type="string", 
				dest="parent", default="root")
		self.OptionParser.add_option("--mode",
				action="store", type="string", 
				dest="mode", default="followNearestTwo")
	

	def styleIfPresent(self, node, key, default = ''):
	        style = node.get('style')
	        if style:
	        	style = simplestyle.parseStyle(style)
                        if style.has_key(key):
                                return style[key]
                
                return ""

	
	def hasDisplayNone(self, node):
	        display = self.styleIfPresent(node, 'display')
                if self.styleIfPresent(node, 'display') == 'none':
                        log("Node " + node.get("id") + " has display = none, really!")
                        return True
                
                log("Returning False for " + node.get("id"))
	        return False

        def getOpacity(self, node):
                opacity = self.styleIfPresent(node, 'opacity')
                if opacity == "":
                        return "1"
                return opacity

        def changeStyleKey(self, node, key, value):
	        style = node.get('style')
	        if style:
	        	style = simplestyle.parseStyle(style)
                else:
                        style = {}
                style[key] = value
                node.set('style', simplestyle.formatStyle(style))

	# Returns False if no layers found within the hierarchy
	#         True if any child object or the object itself is a layer
	def addVisibleLeafLayers(self, node, keepAdding):
	        log("Entering addVisibleLeafLayers for " + node.get("id"))
		if node.tag != inkex.addNS('g','svg') and node.tag != inkex.addNS('svg','svg'):
		        log("Node " + node.get("id") + " is not a group, skipping")
			return False

		# If it's not displayed, then just go through the hierarchy
		if self.hasDisplayNone(node):
		        log("Node " + node.get("id") + " is not actually displayed, stopping any adds")
			keepAdding = False
		
		# Process all child groups
		layersInChildren = False
		for child in node.getchildren():
		        hierarchyResult = self.addVisibleLeafLayers(child, keepAdding)
			layersInChildren = layersInChildren or hierarchyResult
		
		if keepAdding and node.tag == inkex.addNS('g', 'svg'):
			# See if this one perhaps is to be added
			if layersInChildren == False and node.get(inkex.addNS('groupmode', 'inkscape')) == 'layer':
				# So, we have here: a visible layer, under lots of visible layers, that has no child layers
				# Clone it!
				
				clone = inkex.etree.SubElement(self.win_object, 'use')
				clone.set(inkex.addNS('href', 'xlink'), '#' + str(node.get("id")))
				# Set opacity 
				if self.options.opacity == "copy" or self.options.opacity == "copy-reset":
				        clone.set("style", "opacity: " + self.getOpacity(node))
                                if self.options.opacity == "copy-reset":
                                        self.changeStyleKey(node, "opacity", 1)
                                        
                                        
				
				
                                log("Node " + node.get("id") + " IS CLONED")
                        else:
                                log("Node " + node.get("id") + " does not like to be cloned")

		
		return layersInChildren or node.get(inkex.addNS('groupmode', 'inkscape')) == 'layer'

        def getTotalTransform(self, node):
                if node == None:
                        # Unitary transform
                        return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
                return simpletransform.composeTransform(self.getTotalTransform(node.getparent()), self.get_transform(node))
        
        def getTransformed(self, x, y, src, dst, t):
                # Compute global coordinates
                gx = x * t[0][0] + y * t[0][1] + t[0][2]
                gy = x * t[1][0] + y * t[1][1] + t[1][2]
                
                (nx, ny) = self.transformCoordinates(gx, gy, src, dst)
                
                if nx == gx and ny == gy: return (x, y)

                # Invert our transform
                it = self.invert_transform(t)

                rx = nx * it[0][0] + ny * it[0][1] + it[0][2]
                ry = nx * it[1][0] + ny * it[1][1] + it[1][2]
                return (rx, ry)

        def transformCoordinates_PlainShift(self, gx, gy, src, dst):
                if self.goffs <> None:
                        return (gx + self.goffs[0], gy + self.goffs[1])
                
                (nx, ny) = self.transformCoordinates_KeepToClosest(gx, gy, src, dst)
                if nx != gx or ny != gy:
                        self.goffs = [nx - gx, ny - gy]
                
                return (nx, ny)

        def transformCoordinates_KeepToClosest(self, gx, gy, src, dst):
                ox = oy = n = 0
                neigh = src.findClosest(gx, gy, 1)
                if len(neigh) <> 1: return (gx, gy)
                
                (st, dist) = neigh[0]
                if not st in dst.dict: return (gx, gy)
                
                (sx, sy) = src.dict[st]
                (dx, dy) = dst.dict[st]
                ox = dx - sx
                oy = dy - sy
#                       print "%.2f, %.2f is-close to %s, dist = %.2f" % (gx, gy, st, dist)
                
                if abs(ox) < 1e-5 and abs(oy) < 1e-5: return (gx, gy)
                
                # Apply offset
                return (gx + ox, gy + oy)

        def transformCoordinates_NearestTwo(self, gx, gy, src, dst):
                neigh = src.findClosest(gx, gy, 2)
                
                # Need two neighbors for this trick
                if len(neigh) <> 2: return (gx, gy)
                
                # Get close and far neighbor
                (cn, cdist) = neigh[0]
                (fn, fdist) = neigh[1]
                
                # If any of them is not present in dst, do not move
                if (cn not in dst.dict) or (fn not in dst.dict): return (gx, gy)
                
                # Get neighbor coordinates
                (scnx, scny) = src.dict[cn]
                (sfnx, sfny) = src.dict[fn]
                (dcnx, dcny) = dst.dict[cn]
                (dfnx, dfny) = dst.dict[fn]
                
                # Compute neighbor distances in source and destination
                snd = math.sqrt((scnx - sfnx) ** 2 + (scny - sfny) ** 2)
                dnd = math.sqrt((dcnx - dfnx) ** 2 + (dfny - dcny) ** 2)
                
                # If neighbors are in the same place, do not move
                if snd < 1e-5 or dnd < 1e-5: return (gx, gy)
                
                # Get bearing difference between the survey leg on both drawings
                rot_by = math.atan2(dfny - dcny, dfnx - dcnx) - math.atan2(sfny - scny, sfnx - scnx)
                
                # Get vector to point from closer neighbor @ source
                ox = gx - scnx
                oy = gy - scny
                
                # Scale this vector
                ratio = dnd / snd
                ox *= ratio
                oy *= ratio
                
                # Rotate this vector by the bearing difference
                (ox, oy) = (ox * math.cos(rot_by) - oy * math.sin(rot_by), ox * math.sin(rot_by) + oy * math.cos(rot_by))
                
                # Compute new point position
                return (ox + dcnx, oy + dcny)
                
        def rePath(self, path, src, dst, tr):
                for m, args in path:
                        if len(args) >= 2:
                                n = 0
                                while (n+1) < len(args):
                                        (args[n], args[n+1]) = self.getTransformed(args[n], args[n+1], src, dst, tr)
                                        n = n + 2

        def removeAttribIfExists(self, node, attrib):
                if attrib in node.attrib:
                        node.attrib.pop(attrib)

        def rectify(self, src, dst, node, centerline):
                if self.styleIfPresent(node, "display") == "none": return
                if node == centerline: return
                if node == self.dst: return
                if node.tag == inkex.addNS('defs', 'svg'): return
                
                if node.tag == inkex.addNS('path','svg'):
                        path = simplepath.parsePath(node.get("d"))
                        tr = simpletransform.composeParents(node, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
                        
#                        print str(path)
                        self.rePath(path, src, dst, tr)
#                        print " now becomes \n" + str(path) + "\n"
                        node.set("d", simplepath.formatPath(path))
                        self.removeAttribIfExists(node, inkex.addNS("path-effect", "inkscape"))
                        self.removeAttribIfExists(node, inkex.addNS("original-d", "inkscape"))
                        self.removeAttribIfExists(node, inkex.addNS("type", "sodipodi"))
                        
                        return
                elif node.get("x") <> None:
                        tr = simpletransform.composeParents(node, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
                        (x, y) = self.getTransformed(float(node.get("x")), float(node.get("y")), src, dst, tr)
                        node.set("x", str(x))
                        node.set("y", str(y))
                elif node.get("cx") <> None:
                        tr = simpletransform.composeParents(node, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
                        (x, y) = self.getTransformed(float(node.get("cx")), float(node.get("cy")), src, dst, tr)
                        node.set("cx", str(x))
                        node.set("cy", str(y))
                                
                for child in node.getchildren():
                        self.rectify(src, dst, child, centerline)
	
	def findCenterlineLayers(self, parent, list):
	        childLayerCount = 0
	        for node in parent.getchildren():
	                # See if this is a layer?
                        if node.get(inkex.addNS('groupmode', 'inkscape')) <> 'layer': continue
                        if self.styleIfPresent(node, "display") == "none": continue

                        if node == self.dst: continue
                        childLayerCount += 1
                        
                        # See if it has any sub-layers?
                        if self.findCenterlineLayers(node, list) == 0:
                                # It's a leaf layer! See if it has any stations ...
                                ss = StationStore(node)
                                if len(ss.dict) > 0:
                                        list.append((node, ss))
                
                return childLayerCount
                
	
	def effect(self):
	        # Configure logging
	        if len(self.options.debug):
	                logging.basicConfig(level = logging.DEBUG)
	        
	        if self.options.mode == "followNearestTwo":
        	        self.transformCoordinates = self.transformCoordinates_NearestTwo
                elif self.options.mode == "keepToClosest":
        	        self.transformCoordinates = self.transformCoordinates_KeepToClosest
                else:
                        self.goffs = None
        	        self.transformCoordinates = self.transformCoordinates_PlainShift
                        
                dst = self.get_current_layer()
                if dst == None: return
                self.dst = dst

                dstStations = StationStore(dst)
                # Now, go through all layers that have stations in them
                centerLines = []
                self.findCenterlineLayers(self.document.getroot(), centerLines)
                
                for (src, srcStations) in centerLines:
                        srcStations.buildKD()
                        # todo Huge trouble possible if two centerlines share a parent
                        self.rectify(srcStations, dstStations, src.getparent(), src)
                        
                        if self.options.replace:
                                # Duplicate new centerline into old layer
                                for ch in src:
                                        src.remove(ch)
                                for ch in dst:
                                        src.append(copy.deepcopy(ch))

                
#        	selected = self.selected.iteritems()
#        	if len(self.selected) > 0:
        	        # Move this object(s) into a clipPath
#        	        for id, obj in selected:
#        	                tr = simpletransform.composeParents(obj, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
#        	                obj.set("transform", simpletransform.formatTransform(tr))
#        	                root.append(obj)
        	
if __name__ == '__main__':
	e = SpeleoMorph()
	e.affect()

