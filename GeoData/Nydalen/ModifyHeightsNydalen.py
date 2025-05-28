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
        if manual_heights and row.get("@id") in manual_heights:
            h = manual_heights[row["@id"]]

        # Use building:levels if available
        elif "building:levels" in row and pd.notna(row["building:levels"]):
            try:
                h = float(row["building:levels"]) * 3
            except:
                pass  # skip if not numeric

        # Default height for house
        elif row.get("building") == "house":
            h = 6

        heights.append(h)

    gdf["height"] = heights
    gdf = gdf[gdf["height"].notna()] #remove buildings without a height value

    # Save modified file
    gdf.to_file(output_path, driver="GeoJSON")
    print(f"✅ Saved updated GeoJSON with heights to: {output_path}")


estimate_heights(
    input_path="GeoData/Nydalen/Buildings.geojson",
    output_path="GeoData/Nydalen/BuildingsModified.geojson",
    manual_heights={
        "way/38316703": 25, #BI
        "way/31056341": 20, 
        "way/80915039": 10, #er egentlig 10, men er i skyggen for å teste 
        "way/116863073": 13, 
        "way/80915060": 14, 
        "way/1275434038": 54, 
        "way/80915079": 10, 
        "way/521313340": 15, 
        "way/80915041": 20,
        "way/585414364": 17, 
        "way/71197843": 18, 
        "way/1023061769": 18, 
        "way/1023061768": 18, 
        "way/80915062": 10, 
        "way/83376754": 29, 
        "relation/14697624": 18, 
        "way/80915076": 10, 
        "way/71336689": 20, 
        "way/71336664": 18, 
        "relation/13698999": 22,
        "way/1023061811": 5, 
        "way/71336668": 11,
        #Warehouse
        "way/1023064202": 1,
        "way/1023064203": 1,
        "way/1023064204":1,
        "way/80915055": 1,
        "way/80915057": 20, 
        "way/80915074": 15, 
        "way/83376757": 20, 
        "way/83376755": 5, 
        "way/80915040": 20, 
        "way/80915035": 20, #Må sjekke om denne stemmer 
        "way/1023061428": 1,

    }, 
        manual_deletes=[
        #site buildings
        "way/71198331", 
        "way/1023062984",
        "way/66354020",
    ]
)



