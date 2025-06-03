#####evaluate_existing_layout.py####
#this script is used to compare the UPGA-generated output with the exisitng urban plan 

#import python libraries
import geopandas as gpd
import matplotlib.pyplot as plt  
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import geopandas as gpd

#import classes
from GAIAClasses.LoadGeoData import LoadGeoData
from UPGA.UPGA import UPGA


#Example input: mapping of existing buildings to type and height
building_input = {
    "school1": {"id": "way/71198331", "type": "school", "height": 20.0}, 
    "apartment1": {"id": "way/1023062984", "type": "apartments", "height": 17}, 
    "office1": {"id": "way/66354020", "type": "office", "height": 12.0} 
}


#Insert correct CRS for the specific location 
crs = "EPSG:32618"
loader = LoadGeoData(crs)

#insert Geodata layers from overpass turbo Queries, see "OverpassTruboQuery.txt"
geo_data = {
    "sites": loader.load_geojson("GeoData/NY/Sites.json"), 
    "buildings": loader.load_geojson("GeoData/NY/Buildings.geojson"),
    "barriers": loader.load_geojson("GeoData/NY/Barriers.geojson"),
    "cycle": loader.load_geojson("GeoData/NY/cycle.geojson"),
    "nature": loader.load_geojson("GeoData/NY/Nature.geojson"),
    "services": loader.load_geojson("GeoData/NY/Services.geojson"),
    "existing": loader.load_geojson("GeoData/NY/BuildingsModified.geojson")
}


site_geoms = []
for b_name, b_info in building_input.items():
    b_id = b_info["id"]
    match = geo_data["buildings"][geo_data["buildings"]["@id"] == b_id]
    if not match.empty:
        row = match.iloc[0]
        geom = row.geometry
        site_geoms.append({"name": b_name, "geometry": geom})  
    else:
        print(f"warning: Building ID {b_id} not found in buildings.geojson")


sites_gdf = gpd.GeoDataFrame(site_geoms, crs=crs)
geo_data["sites"] = sites_gdf


target_floor_height = 3 #assuming exisitng floors heihgts are 3 meters 
footprint_ratio = 0.7
site_areas = sites_gdf.set_index("name").geometry.area.to_dict()

individual = {}
building_specs = {}
for b_name, b_info in building_input.items():
    area = site_areas.get(b_name, 1.0)
    floors = b_info["height"] // target_floor_height
    gfa = area * footprint_ratio * floors
    individual[b_name] = {
        "site": b_name,
        "type": b_info["type"],
        "height": b_info["height"],
        "gfa": gfa
    }
    building_specs[b_name] = {"type": b_info["type"], "target_gfa": gfa}


upga = UPGA(
    output_path=None,
    crs=crs,
    geo_data=geo_data,
    building_specs=building_specs,
    azimuth=180,
    altitude=30,
    plot=True,
    PlotRun=False
)

shadow_nature_fitness, _ = upga.compute_shadow_nature_fitness(individual)
walkability_fitness = upga.compute_walkability_fitness(individual)
cycleability_fitness = upga.compute_cycleability_fitness(individual)
service_fitness = (upga.compute_serviceavailability_apartments_fitness(individual)+upga.compute_serviceavailability_offices_fitness(individual))/2
shadow_building_fitness, shadowed_info, non_shadowed_info, _, _, _, _ = upga.compute_shadow_building_fitness(individual)


weight_shadow_nature = 0.1667
weight_walk =0.1667
weight_cycle = 0.1667
weight_service = 0.1667
weight_building_shadow = 0.1667
weight_building_GFA = 0.1667

total_fitness = (
    weight_shadow_nature * shadow_nature_fitness +
    weight_walk * walkability_fitness +
    weight_cycle * cycleability_fitness +
    weight_service * service_fitness +
    weight_building_shadow * shadow_building_fitness + 
    weight_building_GFA*1
)

print(site_areas)

upga.plot_individual(individual)

#insert output path 
upga.write_evaluation_report("(output path.......)/ReportOriginal.txt", individual)

print(f"\nTotal fitness for original layout: {total_fitness:.3f}")
print("---------------------------------------")
print("\nFitness Breakdown:")
print(f"  • GFA fitness:             {1.00:.3f}")
print(f"  • Shadow Nature fitness:   {shadow_nature_fitness:.3f}")
print(f"  • Shadow Building fitness: {shadow_building_fitness:.3f}")
print(f"  • Walkability:             {walkability_fitness:.3f}")
print(f"  • Cycleability:            {cycleability_fitness:.3f}")
print(f"  • Serviceability:          {service_fitness:.3f}")

