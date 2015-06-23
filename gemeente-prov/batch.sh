#!/bin/bash

for geojson in latlon_*.json; do
  topojson -o topo_$geojson -p -- $geojson
done
