## UPGAmain.py###

#This Urban planning genetic algorithm takes a local data and building spesifications 
# and optimizes for the best building configuration which is then plotted and described in the output report
#to generate building shapes and ifc files as well - go to "GAIAmain.py"

############# UPGA use #####################
######## Follow the steps to optimize ######

import time
from UPGA.UPGA import UPGA
from GAIAClasses.LoadGeoData import LoadGeoData 

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
    "sites": loader.load_geojson("GeoData/ProjectName/Sites.json"), 
    "buildings": loader.load_geojson("GeoData/ProjectName/Buildings.geojson"),
    "barriers": loader.load_geojson("GeoData/ProjectName/Barriers.geojson"),
    "cycle": loader.load_geojson("GeoData/ProjectName/Cycle.geojson"),
    "nature": loader.load_geojson("GeoData/ProjectName/Nature.geojson"),
    "services": loader.load_geojson("GeoData/ProjectName/Services.geojson"),
    "existing": loader.load_geojson("GeoData/ProjectName/BuildingsModified.geojson")
}

# 6) Insert building specifications - building name (id), building type (school, office, apartment) and target gross floor area 
building_specs = {
    "BuildingName1":   {"type": "apartment", "target_gfa": 1500},
    "BuildingName1":   {"type": "office",    "target_gfa": 3000},  
    "BuildingName1":   {"type": "school",    "target_gfa": 3000} 
}

#Optional: If another building type than "school is preeffered, please define:
accessability_building_type="school"

#Optional: If Another building type than "apartment" and "office" is preffered for serviceavailability, please define:
serviceavailability_building_type=["apartment", "office"]


#UPGA
urban_ga = UPGA(report_path, IFC_file_path,  crs, geo_data, building_specs, 
                        azimuth, altitude, accessability_building_type, serviceavailability_building_type, 
                        popsize=population_size, generations=number_of_generations, mutProb=0.1, plot=True, PlotRun=False)
urban_ga.run()
