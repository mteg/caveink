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
                
                log("Station %s has coordinates %.2f, %.2f" % (name, nx, ny))
                self.dict[name] = (nx, ny)

                                
        def findStations(self, children):
                # See if this can be a station
                if len(children) == 2:
                        if children[0].tag == inkex.addNS('text','svg') and children[1].tag == inkex.addNS('use','svg'):
                                return self.gotStation(children[1], children[0])
                        elif children[1].tag == inkex.addNS('text','svg') and children[0].tag == inkex.addNS('use','svg'):
                                return self.gotStation(children[0], children[1])

                for obj in children:
                        self.findStations(obj.getchildren())

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

        def __init__(self, layer):
                self.dict = {}
                self.findStations(layer.getchildren())
                
        


class SpeleoMorph(speleo_grid.SpeleoEffect):
	def __init__(self):
		inkex.Effect.__init__(self)
		self.OptionParser.add_option("--debug",
				action="store", type="string", 
				dest="debug", default="")
		self.OptionParser.add_option("--opacity",
				action="store", type="string", 
				dest="opacity", default="clone")
		self.OptionParser.add_option("--parent",
				action="store", type="string", 
				dest="parent", default="root")
		self.OptionParser.add_option("--neighbors",
				action="store", type="int", 
				dest="neighbors", default=1)
	

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
                
                ox = oy = n = 0
                for st, dist in src.findClosest(gx, gy, self.options.neighbors):
                        if st not in dst.dict: pass
                        (sx, sy) = src.dict[st]
                        (dx, dy) = dst.dict[st]
                        ox += dx - sx
                        oy += dy - sy
                        n = n + 1
                
                if abs(ox) < 1e-5 and abs(oy) < 1e-5: return (x, y)
                
                # Apply offset
                gx += ox / n
                gy += oy / n
                
                # Invert our transform
                it = self.invert_transform(t)
                
                # Compute new coordinates
                nx = gx * it[0][0] + gy * it[0][1] + it[0][2]
                ny = gx * it[1][0] + gy * it[1][1] + it[1][2]
                
                return (nx, ny)
                
        def rePath(self, path, src, dst, tr):
                for m, args in path:
                        if len(args) >= 2:
                                n = 0
                                while (n+1) < len(args):
                                        (args[n], args[n+1]) = self.getTransformed(args[n], args[n+1], src, dst, tr)
                                        n = n + 2


        def rectify(self, src, dst, node):
                if node.tag == inkex.addNS('path','svg'):
                        path = simplepath.parsePath(node.get("d"))
                        tr = simpletransform.composeParents(node, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
                        
#                        print str(path)
                        self.rePath(path, src, dst, tr)
#                        print " now becomes \n" + str(new_path) + "\n"
                        node.set("d", simplepath.formatPath(path))
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
                        self.rectify(src, dst, child)
	
	def effect(self):
	        # Configure logging
	        if len(self.options.debug):
	                logging.basicConfig(level = logging.DEBUG)
	        
	        
		# Get root node
                if self.options.parent == "root":
                        root = self.document.getroot()
                else:
                        root = self.get_current_layer()


                src = self.xpathSingle('//svg:g[@id="%s"]' % "src")
                srcStations = StationStore(src)
                srcStations.buildKD()

                dst = self.xpathSingle('//svg:g[@id="%s"]' % "dst")
                dstStations = StationStore(dst)
                
#                print srcStations.dict
#                print dstStations.dict

                drawing = self.xpathSingle('//svg:g[@id="%s"]' % "content")
                
                self.rectify(srcStations, dstStations, drawing)
                
                
                
                
                
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

