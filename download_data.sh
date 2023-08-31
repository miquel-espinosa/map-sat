#!/bin/bash

wget 'https://api.os.uk/downloads/v1/products/BoundaryLine/downloads?area=GB&format=ESRI%C2%AE+Shapefile&redirect' -O boundaries.zip
unzip boundaries.zip
rm boundaries.zip
mv Doc/ Data/
mv Readme.txt Data/
mkdir country_data
mkdir results
mv Data/Supplementary_Country/* country_data/
rm -rf Data/
echo "Boundaries data downloaded, stored in country_data."