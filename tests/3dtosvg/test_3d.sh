#!/bin/bash

if ! python2 $1 $2 $3.3d > $3.out.svg; then
	exit 1
fi
	

if ! inkscape --without-gui --export-area-drawing --export-png=$3.out.png $3.out.svg; then
	exit 1
fi


