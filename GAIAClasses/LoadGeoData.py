#### LoadGeoData.py ###
#This script processes geospatial data layers and converts them into GeoDataFrames with the appropriate coordinate reference system (CRS)

import geopandas as gpd
from shapely.geometry import shape
import json

class LoadGeoData:
    def __init__(self, crs):
        self.crs = crs


    def load_geojso(self, path):
        with open(path) as f:
            raw_data = json.load(f)

        attributes = []
        geometries = []

        for feature in raw_data["features"]:
            try:
                geom = shape(feature["geometry"])
                geometries.append(geom)
                attributes.append(feature["properties"])
            except Exception as e:
                print("Skipping feature:", e)

