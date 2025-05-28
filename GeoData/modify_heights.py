###### modify_heights.py #####

#Use this code if heights are missing in geospatial data
#This code makes adds height values in a semi-manual way 
#Generates new geosjon files  with exisitng buildings and heights

####### follow the steps described from line 57 to add height data ########

import geopandas as gpd
import pandas as pd

def estimate_heights(input_path, output_path, manual_heights=None, manual_deletes=None):

    gdf = gpd.read_file(input_path)

    #optional: deletion of features
    if manual_deletes:
        gdf = gdf[~gdf["@id"].isin(manual_deletes)]

    #add height column
    heights = []
    for idx, row in gdf.iterrows():
        h = None

        if manual_heights and row.get("@id") in manual_heights:
            h = manual_heights[row["@id"]]

        #use existing height if available
        elif "height" in row and pd.notna(row["height"]):
            try:
                h = float(row["height"])
            except:
                pass 

        elif "building:levels" in row and pd.notna(row["building:levels"]):
            try:
                h = float(row["building:levels"]) * 3
            except:
                pass


        elif row.get("building") == "house":
            h = 6


        heights.append(h)

    gdf["height"] = heights
    gdf = gdf[gdf["height"].notna()] 

    gdf.to_file(output_path, driver="GeoJSON")
    print(f"Saved updated GeoJSON with heights to: {output_path}")



estimate_heights(
    #(path.....\Buildings.geojson)
    input_path="GeoData/NYGA/Buildings.geojson", #example input_path 

    #(path.....\BuildingsModified.geojson)
    output_path="GeoData/NYGA/BuildingsModified.geojson", #example output_path 

    #add hights manually
    manual_heights={
        #  "@id"    : height,  #how to add building height modification 

        "way/270902491":64    #example for height modification 

    }, 

        #optional: delete buildings 
        manual_deletes=[
    ]
)
