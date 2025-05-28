#this code is used to add heights only to the original buildings to evaluate the exisitng layout in 
# the case study of Nydalen


import geopandas as gpd

allowed_ids = [
    "way/71198331", #school
    "way/1023062984", #apartment
    "way/66354020" #office
]

manual_heights = {
    "way/71198331": 17,  
    "way/1023062984": 15,
    "way/66354020": 10
}


input_geojson = "GeoData/Buildings.geojson"
output_geojson = "GeoData/OriginalBuildingsModified.geojson"

gdf = gpd.read_file(input_geojson)


filtered_gdf = gdf[gdf["@id"].isin(allowed_ids)]

filtered_gdf["manual_height"] = filtered_gdf["@id"].map(manual_heights)


filtered_gdf.to_file(output_geojson, driver="GeoJSON")
print(f"Filtered GeoJSON with manual heights saved to '{output_geojson}'.")
