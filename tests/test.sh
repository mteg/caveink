#!/bin/bash

python $1 $2 $3.svg > $3.out.svg
inkscape --without-gui --export-area-drawing --export-png=$3.out.png $3.out.svg

