#Making gejson files with exisitng buildings and heights when heighs are not stored in OSM

import geopandas as gpd
import json
import pandas as pd

def estimate_heights(input_path, output_path, manual_heights=None, manual_deletes=None):

    gdf = gpd.read_file(input_path)

    # Optional deletion of features
    if manual_deletes:
        gdf = gdf[~gdf["@id"].isin(manual_deletes)]

    # Add height column
    heights = []
    for idx, row in gdf.iterrows():
        h = None

        # Manual override by @id
        # Manual override by @id
        if manual_heights and row.get("@id") in manual_heights:
            h = manual_heights[row["@id"]]

        # Use existing height if available
        elif "height" in row and pd.notna(row["height"]):
            try:
                h = float(row["height"])
            except:
                pass  # skip if malformed

        # Estimate from building:levels
        elif "building:levels" in row and pd.notna(row["building:levels"]):
            try:
                h = float(row["building:levels"]) * 3
            except:
                pass

        # Default for houses
        elif row.get("building") == "house":
            h = 6


        heights.append(h)

    gdf["height"] = heights
    gdf = gdf[gdf["height"].notna()] #remove buildings without a height value

    # Save modified file
    gdf.to_file(output_path, driver="GeoJSON")
    print(f"Saved updated GeoJSON with heights to: {output_path}")


estimate_heights(
    input_path="GeoData/Rome/BuildingsR.geojson",
    output_path="GeoData/Rome/BuildingsModified.geojson",
    manual_heights={
        

    }, 
        manual_deletes=[
            "way/130807574", # apartment 
            "way/131235585", 
            "way/130807549", 
            "way/130807690", 
            "way/128740485", #office
            "way/128740275" #school
    ]
)
