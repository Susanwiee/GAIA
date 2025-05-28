#####GAIA.py#####
#for use - go to "GAIAmain.py"
#this is the GAIA class which uses subclasses such as RectangleAnalyzer, UPGA, Daedalus GA and Buildingcomposer 
#to optimize a urban plan and generate a ifc.file representing the solution
#the code is divided into 4 main steps 



from GAIAClasses.RectangleAnalyzer import RectangleAnalyzer
from BuildingComposer.BuildingComposer import BuildingComposer  
from UPGA.UPGA import UPGA    
from Daedalus import DaedalusGA  
import time 

class GAIA:
    def __init__(self, output_path_report, output_path_IFC, geo_data, building_specs, azimuth, altitude, crs, accessability_building_type, serviceavailability_building_type, pop_size, n_gen):
        self.output_path_report = output_path_report
        self.output_path_IFC = output_path_IFC
        self.geo_data = geo_data 
        self.building_specs=building_specs
        self.azimuth = azimuth
        self.altitude = altitude
        self.crs = crs
        self.accessability_building_type = accessability_building_type
        self.serviceavailability_building_type = serviceavailability_building_type
        self.pop_size = pop_size
        self.n_gen = n_gen

    def runGAIA(self):    

        # 1) - calling rectangleanalyzer to make site parameters 
        analyzer = RectangleAnalyzer(self.geo_data) 
        analyzer.plot_site_rectangles()              
        params = analyzer.get_parameters()   

        ##Store parameters from RectangleAnalyzer##
        #choose the anchor site to use as reference for relative positioning
        anchor = next((p for p in params if p["site"].lower() == "site1"), None)
        if anchor is None:
            raise ValueError("Site1 not found in parameters!")
        anchor_x = anchor["position_x"]
        anchor_y = anchor["position_y"]
        sites = []
        for p in params:
            name = p["site"]
            rel_x = p["position_x"] - anchor_x
            rel_y = p["position_y"] - anchor_y
            site_entry = {
                "name": name,
                "length": min(p["site_length"], p["site_width"]),
                "width":  max(p["site_width"], p["site_length"]),
                "angle":  p["orientation"],   
                "position_x": round(rel_x, 2),      
                "position_y": round(rel_y, 2)       
            }
            sites.append(site_entry)

        start = time.time()

        # 2) - UPGA will assign each building (from building_specs) to a unique site.
        urban_ga = UPGA(self.output_path_report, self.crs, self.geo_data, self.building_specs, 
                        self.azimuth, self.altitude, self.accessability_building_type, self.serviceavailability_building_type, 
                        popsize=self.pop_size, generations=self.n_gen, mutProb=0.1, plot=True, PlotRun=False)
        urban_result, site_to_building = urban_ga.run()
        end = time.time()
        print("UPGA execution time:", round(end - start, 3), "seconds")


        all_buildings = []
        for site in sites:
            site_name   = site["name"]
            site_length = site["length"]
            site_width  = site["width"]

            if site_name not in site_to_building:
                print(f"No building assigned to {site_name}, skipping...")
                continue

            building_id = site_to_building[site_name]
            target_gfa = self.building_specs[building_id]["target_gfa"]
            max_height = round(urban_result[building_id]["max_height"],2)

            print(f"Running DaedalusGA for {building_id} at {site_name} (GFA {target_gfa}, Max height {max_height})")

            # 3) - Daedalus GA runs and optimized building parameters
            ga = DaedalusGA(
                popsize=500,
                generations=5000,
                mutProb=0.1,
                target_GFA=target_gfa,
                site_width=site_width,
                site_length=site_length,
                max_height=max_height
            )
            start = time.time()
            best_result = ga.run()
            end = time.time()
            print("Daedalus GA execution time:", round(end - start, 3), "seconds")

            if "buildings" not in best_result:
                raise ValueError(f"DaedalusGA result does not contain 'buildings' key! Got keys: {list(best_result.keys())}")


            for building_params in best_result["buildings"]:
                all_buildings.append({
                    "site": site_name,
                    "shape": building_params["shape"],
                    "roof_type": building_params["roof_type"],
                    "window_type": "standard",
                    "length": float(building_params["length"]),
                    "width": float(building_params["width"]),
                    "height": 2.26,                      
                    "top_height": float(building_params["top_height"]),
                    "thickness": 0.3,                   
                    "arm1_thickness": float(building_params["arm1_thickness"]),
                    "arm2_thickness": float(building_params["arm2_thickness"]),
                    "overhang": float(building_params["overhang"]),
                    "num_levels": int(building_params["num_levels"]),
                    "window_sill_height": float(building_params["window_sill_height"]),
                    "window_width": float(building_params["window_width"]),
                    "window_height": float(building_params["window_height"]),
                    "distance_between_windows": 2.0,   
                })

        # 4) - running BuildingComposer to generate IFC files 
        output_file = self.output_path_IFC
        builder = BuildingComposer(sites, all_buildings, output_file)
        builder.build()

