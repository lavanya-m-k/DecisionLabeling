#!/bin/sh

mkdir $2
ffmpeg -i $1 -vsync vfr -qscale:v 2 -start_number 0 $2/%05d.jpg
#ffmpeg -i $1 -qscale:v 1 -start_number 0 $2/%07d.jpg