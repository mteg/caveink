#!/bin/bash

if ! python $1 $2 $3.svg > $3.out.svg; then
	exit 1
fi
	

if ! inkscape --without-gui --export-area-drawing --export-png=$3.out.png $3.out.svg; then
	exit 1
fi


