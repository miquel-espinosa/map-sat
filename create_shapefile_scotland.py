import geopandas as gpd
import os
from shapefile_utils import get_largest_geometry

ROOT = os.getcwd()
COUNTRIES = f'{ROOT}/country_data/country_region.shp'
SCOTLAND_FULL = f'{ROOT}/country_data/scotland_full.shp'
SCOTLAND = f'{ROOT}/country_data/scotland.shp'
EPSG = "EPSG:4326"

# Countries UK
gdf_country = gpd.read_file(COUNTRIES)
# Filter only for SCT
coastline_sct = gdf_country[gdf_country.NAME=='Scotland']
# Save Scotland boundaries as shapefile
coastline_sct.to_file(SCOTLAND_FULL, driver='ESRI Shapefile')
print("Scotland shapefile (full, with islands) saved")

# Read the shapefile for Scotland (full, mainland + islands)
scotland_shapefile = gpd.read_file(SCOTLAND_FULL)
# Get the largest geometry from the scotland shapefile (thus, the mainland)
# And convert it to CRS common format
sct_inland = get_largest_geometry(scotland_shapefile).to_crs(EPSG)
sct_inland.to_file(SCOTLAND, driver='ESRI Shapefile')
print("Scotland shapefile (mainland only) saved")