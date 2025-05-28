######VisualizeData_main.py#####
#This code is only for visualizing the urban area, not for optimization#
#go to GAIAmain.py or UPGAmain.py for optimization##


from VisualizeData import VisualizeData
from GAIAClasses.LoadGeoData import LoadGeoData

# 1 - insert correct CRS: 
crs = "EPSG:32632"
loader = LoadGeoData(crs)

# 2 - insert Geodata layers from overpass turbo Queries using OverpassTruboQuery.txt
geo_data = {
    "sites": loader.load_geojso("GeoData/Rome/Sites.json"),
    "buildings": loader.load_geojso("GeoData/Rome/Buildings.geojson"),
    "barriers": loader.load_geojso("GeoData/Rome/Barriers.geojson"),
    "nature": loader.load_geojso("GeoData/Rome/Nature.geojson"),
    "cycle": loader.load_geojso("GeoData/Rome/cycle.geojson"),
    "services": loader.load_geojso("GeoData/Rome/Services.geojson"),
    "existing": loader.load_geojso("GeoData/Rome/BuildingsModified.geojson")
}

# 3 -  For visualization: enter feature as one of the following
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

VisualizeData(crs, geo_data, feature="Sites")


