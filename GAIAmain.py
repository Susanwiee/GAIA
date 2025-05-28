#####GAIAmain.py#########

#This script serves as the main user interface and entry point for the GAIA tool

################ GAIA USE #############################
######Follow the instructions below to run the tool#####
########################################################
#(there are in total 7 steps (+ 2 optional), make sure to complete all 7 steps###


from GAIAClasses.LoadGeoData import LoadGeoData
from GAIA import GAIA
from VisualizeData import VisualizeData


# 1) Enter sun angles for the loction you are evaluating
azimuth = 180
altitude =  30

# 2) Enter ESPG for the loction you are evaluating
crs = "EPSG:32632"
loader = LoadGeoData(crs)

# 3) Enter genetic hyperparameters for the UPGA
population_size = 4
number_of_generations = 10

# 4) Enter file paths for report and ifc file 
report_path =   "(insert path..........)/GeoData/Report(ProjectName).txt"          
IFC_file_path = "(insert path..............)/GeoData/FinalCityPlanTime(ProjectName).ifc"


# 5) Insert Geodata layers from overpass turbo Queries 
#See OverpassTruboQuery.txt for defined queries 
geo_data = {
    "sites": loader.load_geojso("GeoData/ProjectName/Sites.json"), 
    "buildings": loader.load_geojso("GeoData/ProjectName/Buildings.geojson"),
    "barriers": loader.load_geojso("GeoData/ProjectName/Barriers.geojson"),
    "cycle": loader.load_geojso("GeoData/ProjectName/Cycle.geojson"),
    "nature": loader.load_geojso("GeoData/ProjectName/Nature.geojson"),
    "services": loader.load_geojso("GeoData/ProjectName/Services.geojson"),
    "existing": loader.load_geojso("GeoData/ProjectName/BuildingsModified.geojson")
}

# 6) Insert building specifications - building name (id), building type (school, office, apartment) and target gross floor area 
building_specs = {
    "BuildingName1": {"type": "apartment", "target_gfa": 1500},
    "BuildingName1":   {"type": "office",    "target_gfa": 3000},  
    "BuildingName1":   {"type": "school",    "target_gfa": 3000} 
}

#Optional: If another building type than "school is preeffered, please define:
accessability_building_type="school"

#Optional: If Another building type than "apartment" and "office" is preffered for serviceavailability, please define:
serviceavailability_building_type=["apartment", "office"]

# 7) analyse the geospatial data you provided to check that all elements are included 
#( ! if there are missing hight values, go to "modify_heights.py" for further instructions !)

########## GIS #########
# For visualization: enter feature as one of the following
# "Buildings"           # Residential, public, office, industrial, etc.
#"BuildingsModified"   # Buildings that include a 'height' attribute           
#"Services"            # Cafés, restaurants, shops, pharmacies, etc.
#"Nature"              # Parks, water bodies, forests, grass, gardens, etc.
#"Barriers"            # Highways, railways, fences, etc.
#"Cycle"               # Cycleways and bike infrastructure
#"CycleWithBuffer"     # Same as above, but with buffer zones for visibility
#"Sites"               # Plots/sites of potential development
#"SpecificBuildings"   # Highlight specific buildings by ID
#"SitesAndShadows"     # Plots + shadows from hypothetical buildings
#"All"                 # Everything (buildings, barriers, nature, cycleways, etc.)

#VisualizeData(crs, geo_data, feature="Nature")
#######################

GAIA = GAIA(report_path, IFC_file_path, geo_data, building_specs, azimuth, altitude, crs, accessability_building_type, serviceavailability_building_type,  population_size, number_of_generations)
GAIA.runGAIA()
