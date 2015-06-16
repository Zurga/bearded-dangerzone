#!/bin/bash

for geojson in *.json; do
  topojson -o topo_$geojson -p -- $geojson
done
