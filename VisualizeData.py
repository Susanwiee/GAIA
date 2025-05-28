### VisualizeData #####
#Class for visualizing geospatial features in the GAIA tool using Matplotlib and GeoPandas

#for use - go to "GAIAmain.py" or "VisualizeData_main.py"


import matplotlib.pyplot as plt  
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import geopandas as gpd

class VisualizeData:
    def __init__(self, crs, geo_data, feature):
        self.crs = crs
        self.geo_data = geo_data
        self.feature = feature
        self.plot()

    def plot_if_not_empty(self, gdf, ax, color, label, alpha=1.0, is_line=False, linewidth=1):
        if gdf is not None and not gdf.empty:
            if is_line:
                gdf.plot(ax=ax, color=color, linewidth=linewidth, label=label)
                if label:
                    return mlines.Line2D([], [], color=color, linewidth=linewidth, label=label)
            else:
                gdf.plot(ax=ax, color=color, alpha=alpha, label=label)
                if label:
                    return mpatches.Patch(color=color, alpha=alpha, label=label)
        return None

    #helper functions for flexibility 
    def safe_filter(self, gdf, column, value):
        return gdf[gdf[column] == value] if column in gdf.columns else gpd.GeoDataFrame()

    def safe_notna(self, gdf, column):
        return gdf[gdf[column].notna()] if column in gdf.columns else gpd.GeoDataFrame()

    def plot(self):
        buildings_gdf     = self.geo_data.get("buildings", gpd.GeoDataFrame())
        services_gdf      = self.geo_data.get("services", gpd.GeoDataFrame())
        nature_gdf        = self.geo_data.get("nature", gpd.GeoDataFrame())
        barriers_gdf      = self.geo_data.get("barriers", gpd.GeoDataFrame())
        cycle_gdf         = self.geo_data.get("cycle", gpd.GeoDataFrame())
        sites_gdf         = self.geo_data.get("sites", gpd.GeoDataFrame())
        buildings_mod_gdf = self.geo_data.get("existing", gpd.GeoDataFrame())


        if self.feature == "BuildingsModified":
            buildings_with_height = buildings_mod_gdf[buildings_mod_gdf["height"].notna()]

            #optinal:  check for a specific building
            #filtered = buildings_mod_gdf[buildings_mod_gdf["@id"] == "way/66354020"]

            #plot
            fig, ax = plt.subplots(figsize=(10, 10))
            buildings_with_height.plot(ax=ax, color="lightblue", edgecolor="black")
            plt.title("Buildings with Height Attribute")
            plt.show()

        elif self.feature == "Buildings":
            houses = [
                self.safe_filter(buildings_gdf, "building", btype)
                for btype in ["house", "semidetached_house", "terrace"]
            ]
            apartments = [
                self.safe_filter(buildings_gdf, "building", btype)
                for btype in ["apartments", "dormitory", "residential"]
            ]
            schools = self.safe_filter(buildings_gdf, "building", "school")
            kindergarten = self.safe_filter(buildings_gdf, "building", "kindergarten")
            office = self.safe_filter(buildings_gdf, "building", "office")
            university = self.safe_filter(buildings_gdf, "building", "university")
            divbuildings = self.safe_filter(buildings_gdf, "building", "yes")
            public = self.safe_filter(buildings_gdf, "building", "public")
            parking = self.safe_filter(buildings_gdf, "amenity", "parking")

            industrial = [
                self.safe_filter(buildings_gdf, "building", btype)
                for btype in ["industrial", "warehouse", "civic"]
            ]
            retail = self.safe_filter(buildings_gdf, "building", "retail")
            commercial = self.safe_filter(buildings_gdf, "building", "commercial")

            fig, ax = plt.subplots(figsize=(10, 10))
            legend_handles = []

            #Apartments
            for gdf in apartments:
                self.plot_if_not_empty(gdf, ax, "purple", None)
            if any(not gdf.empty for gdf in apartments):
                legend_handles.append(mpatches.Patch(color="purple", label="Apartments"))

            #Houses
            for gdf in houses:
                self.plot_if_not_empty(gdf, ax, "orange", None)
            self.plot_if_not_empty(parking, ax, "orange", None)
            if any(not gdf.empty for gdf in houses + [parking]):
                legend_handles.append(mpatches.Patch(color="orange", label="Houses"))

            #Schools
            legend_handles.append(self.plot_if_not_empty(schools, ax, "red", "Schools"))

            #Kindergarten
            legend_handles.append(self.plot_if_not_empty(kindergarten, ax, "pink", "Kindergartens"))

            #Office
            legend_handles.append(self.plot_if_not_empty(office, ax, "blue", "Office"))

            #University
            legend_handles.append(self.plot_if_not_empty(university, ax, "rosybrown", "University"))

            #Public
            legend_handles.append(self.plot_if_not_empty(public, ax, "skyblue", "Public"))

            #Unlabeled
            legend_handles.append(self.plot_if_not_empty(divbuildings, ax, "black", "Unlabeled"))

            #Industrial 
            for gdf in industrial:
                self.plot_if_not_empty(gdf, ax, "grey", None)
            if any(not gdf.empty for gdf in industrial):
                legend_handles.append(mpatches.Patch(color="grey", label="Industrial"))

            #Retail 
            for gdf in [retail, commercial]:
                self.plot_if_not_empty(gdf, ax, "mediumpurple", None)
            if any(not gdf.empty for gdf in [retail, commercial]):
                legend_handles.append(mpatches.Patch(color="mediumpurple", label="Retail"))

            legend_handles = [h for h in legend_handles if h is not None]
            plt.legend(handles=legend_handles, fontsize=14)

            #plot adjustments
            minx, miny, maxx, maxy = buildings_gdf.total_bounds
            ax.set_xlim(minx - 50, maxx + 200)
            ax.set_ylim(miny - 10, maxy + 100)
            plt.title("Buildings", fontsize=18)
            plt.show()


        elif self.feature == "Services":
            #categorize services
            cafes = services_gdf[services_gdf["amenity"] == "cafe"]
            restaurants = services_gdf[services_gdf["amenity"] == "restaurant"]
            fast_food = services_gdf[services_gdf["amenity"] == "fast_food"]
            bars = services_gdf[services_gdf["amenity"] == "bar"]
            pharmacies = services_gdf[services_gdf["amenity"] == "pharmacy"]
            cinemas = services_gdf[services_gdf["amenity"] == "cinema"]
            shops = services_gdf[services_gdf["shop"].notna()]

            #plot
            fig, ax = plt.subplots(figsize=(12, 12))
            shops.plot(ax=ax, color="blue", label="Shops", markersize=20)
            buildings_gdf.plot(ax=ax, color="grey", label="Cafés",markersize=20, alpha=0.6)
            cafes.plot(ax=ax, color="saddlebrown", label="Cafés", markersize=20)
            restaurants.plot(ax=ax, color="orange", label="Restaurants", markersize=20)
            fast_food.plot(ax=ax, color="red", label="Fast Food", markersize=20)
            bars.plot(ax=ax, color="purple", label="Bars", markersize=20)
            pharmacies.plot(ax=ax, color="green", label="Pharmacies", markersize=20)
            
            
            cinemas.plot(ax=ax, color="black", label="Cinemas", markersize=20)

            legend_handles = [
                mpatches.Patch(color="saddlebrown", label="Cafés"),
                mpatches.Patch(color="orange", label="Restaurants"),
                mpatches.Patch(color="red", label="Fast Food"),
                mpatches.Patch(color="purple", label="Bars"),
                mpatches.Patch(color="green", label="Pharmacies"),
                mpatches.Patch(color="black", label="Cinemas"),
                mpatches.Patch(color="blue", label="Shops"),
            ]

            plt.title("Mapped Service Features", fontsize = 14)
            plt.legend(handles=legend_handles, fontsize = 14)
            minx, miny, maxx, maxy = buildings_gdf.total_bounds
            ax.set_xlim(minx +500, maxx -500 )
            ax.set_ylim(miny + 500, maxy -500)
            plt.axis("equal")
            plt.show()

        elif self.feature == "Nature":
            parks     = self.safe_filter(nature_gdf, "leisure", "park")
            forests   = self.safe_filter(nature_gdf, "landuse", "forest")
            water     = self.safe_filter(nature_gdf, "natural", "water")
            wood      = self.safe_filter(nature_gdf, "natural", "wood")
            grass     = self.safe_filter(nature_gdf, "landuse", "grass")
            cemetery  = self.safe_filter(nature_gdf, "landuse", "cemetery")
            garden    = self.safe_filter(nature_gdf, "leisure", "garden")

            fig, ax = plt.subplots(figsize=(10, 10))
            legend_handles = []

            #plot all green areas
            self.plot_if_not_empty(parks, ax, "green", None, alpha=0.5)
            self.plot_if_not_empty(forests, ax, "green", None, alpha=0.3)
            self.plot_if_not_empty(wood, ax, "green", None, alpha=0.3)
            self.plot_if_not_empty(grass, ax, "green", None, alpha=0.5)
            self.plot_if_not_empty(cemetery, ax, "green", None, alpha=0.3)
            self.plot_if_not_empty(garden, ax, "green", None, alpha=0.3)

            if any([not gdf.empty for gdf in [parks, forests, wood, grass, cemetery, garden]]):
                legend_handles.append(mpatches.Patch(color="green", alpha=0.5, label="Nature"))

            #plot water separately in blue
            self.plot_if_not_empty(water, ax, "blue", None, alpha=0.3)
            if not water.empty:
                legend_handles.append(mpatches.Patch(color="blue", alpha=0.3, label="Water"))

            plt.title("Nature Elements", fontsize=18)
            legend_handles = [h for h in legend_handles if h is not None]
            plt.legend(handles=legend_handles, fontsize=14)

            minx, miny, maxx, maxy = buildings_gdf.total_bounds
            ax.set_xlim(minx - 10, maxx + 90)
            ax.set_ylim(miny - 10, maxy + 250)
            ax.set_aspect("equal")
            plt.show()


        elif self.feature == "Barriers":
            highways = self.safe_notna(barriers_gdf, "highway")
            barrier = self.safe_notna(barriers_gdf, "barrier")
            railways = self.safe_filter(barriers_gdf, "railway", "rail")

            fig, ax = plt.subplots(figsize=(10, 10))
            legend_handles = []

            legend_handles.append(self.plot_if_not_empty(highways, ax, "gray", "Highways", is_line=True))
            legend_handles.append(self.plot_if_not_empty(railways, ax, "red", "Railways", is_line=True, linewidth=0.7))
            legend_handles.append(self.plot_if_not_empty(barrier, ax, "Black", "Barrier", is_line=True))

            legend_handles = [h for h in legend_handles if h is not None]
            plt.legend(handles=legend_handles, fontsize=14)

            plt.title("Barriers", fontsize=18)
            minx, miny, maxx, maxy = barriers_gdf.total_bounds
            ax.set_xlim(minx - 100, maxx + 0)
            ax.set_ylim(miny - 300, maxy + 250)
            ax.set_aspect("equal")
            plt.show()

        elif self.feature == "Cycle":
            residential_cycle = self.safe_filter(cycle_gdf, "highway", "residential")
            bicycle           = self.safe_filter(cycle_gdf, "bicycle", "yes")
            cycleway          = self.safe_filter(cycle_gdf, "highway", "cycleway")


            fig, ax = plt.subplots(figsize=(10, 10))
            legend_handles = []

            # Plot buffers 
            if not residential_cycle.empty:
                residential_cycle.plot(ax=ax, color="saddlebrown", alpha=0.2)
                legend_handles.append(mpatches.Patch(color="saddlebrown", alpha=0.8, label="Residential"))

            if not bicycle.empty:
                bicycle.plot(ax=ax, color="teal", alpha=0.2)
                legend_handles.append(mpatches.Patch(color="teal", alpha=0.8, label="Bicycle = yes"))

            if not cycleway.empty:
                cycleway.plot(ax=ax, color="royalblue", alpha=0.2)
                legend_handles.append(mpatches.Patch(color="royalblue", alpha=0.8, label="Cycleway"))

            self.plot_if_not_empty(residential_cycle, ax, "saddlebrown", None)
            self.plot_if_not_empty(bicycle, ax, "teal", None)
            self.plot_if_not_empty(cycleway, ax, "royalblue", None)

            plt.title("Cycleable Network", fontsize=20)
            legend_handles = [h for h in legend_handles if h is not None]
            plt.legend(handles=legend_handles, fontsize=14)
            ax.set_aspect("equal")
            plt.show()


        elif self.feature == "CycleWithBuffer":
            residential_cycle = self.safe_filter(cycle_gdf, "highway", "residential")
            bicycle           = self.safe_filter(cycle_gdf, "bicycle", "yes")
            cycleway          = self.safe_filter(cycle_gdf, "highway", "cycleway")

            resi_buffer   = residential_cycle.buffer(10) if not residential_cycle.empty else gpd.GeoDataFrame()
            bike_buffer   = bicycle.buffer(10) if not bicycle.empty else gpd.GeoDataFrame()
            cycle_buffer  = cycleway.buffer(10) if not cycleway.empty else gpd.GeoDataFrame()

            fig, ax = plt.subplots(figsize=(10, 10))
            legend_handles = []

            # plot buffers
            if not resi_buffer.empty:
                resi_buffer.plot(ax=ax, color="saddlebrown", alpha=0.2)
                legend_handles.append(mpatches.Patch(color="saddlebrown", alpha=0.8, label="Residential"))

            if not bike_buffer.empty:
                bike_buffer.plot(ax=ax, color="teal", alpha=0.2)
                legend_handles.append(mpatches.Patch(color="teal", alpha=0.8, label="Bicycle = yes"))

            if not cycle_buffer.empty:
                cycle_buffer.plot(ax=ax, color="royalblue", alpha=0.2)
                legend_handles.append(mpatches.Patch(color="royalblue", alpha=0.8, label="Cycleway"))


            self.plot_if_not_empty(residential_cycle, ax, "saddlebrown", None)
            self.plot_if_not_empty(bicycle, ax, "teal", None)
            self.plot_if_not_empty(cycleway, ax, "royalblue", None)

            plt.title("Cycleable Network Zones", fontsize=20)
            legend_handles = [h for h in legend_handles if h is not None]
            plt.legend(handles=legend_handles, fontsize=14)
            ax.set_aspect("equal")
            plt.show()


        elif self.feature == "Sites":

            fig, ax = plt.subplots(figsize=(10, 10))            
            if not buildings_gdf.empty:
                buildings_gdf.plot(ax=ax, color="gray", alpha = 0.3, edgecolor="none")
            
            if not sites_gdf.empty:
                sites_gdf.plot(ax=ax, color="teal", edgecolor="black", linewidth=0.5)

            plt.title("Sites", fontsize=18)
            minx, miny, maxx, maxy = buildings_gdf.total_bounds
            ax.set_xlim(minx - 0, maxx + 0)
            ax.set_ylim(miny - 0, maxy + 0)
            ax.set_aspect("equal")
            plt.show()

        elif self.feature == "SpecificBuildings":
            
            # define the specific IDs you want to highlight
            highlight_ids = ["way/71198331", "way/1023062984", "way/66354020"]  # Add as many as needed

            
            fig, ax = plt.subplots(figsize=(10, 10))

            #plot all buildings in gray
            if not buildings_gdf.empty:
                buildings_gdf.plot(ax=ax, color="gray", alpha=0.3, edgecolor="none")

            #filter and plot the highlighted buildings in red
            if "@id" in buildings_gdf.columns:
                highlighted = buildings_gdf[buildings_gdf["@id"].isin(highlight_ids)]
                if not highlighted.empty:
                    highlighted.plot(ax=ax, color="rosybrown", edgecolor="black", linewidth=0.5, alpha=0.9)

            plt.title("Removed Buildings", fontsize=18)
            minx, miny, maxx, maxy = buildings_gdf.total_bounds
            ax.set_xlim(minx, maxx)
            ax.set_ylim(miny, maxy)
            ax.set_aspect("equal")
            plt.show()


        elif self.feature == "SitesAndShadows":
            # Optional: height assumptions for shadow casting
            height_dict = {
                "Site1": 60,
                "Site2": 60,
                "Site3": 60
            }

            from UPGA.UPGAClasses.ShadowAnalyzer import plot_shadow_from_gdf
            shadows = plot_shadow_from_gdf(sites_gdf, height_dict=height_dict, azimuth_deg=180, altitude_deg=53)

            fig, ax = plt.subplots(figsize=(10, 10))

            #all buildings in gray
            if not buildings_gdf.empty:
                buildings_gdf.plot(ax=ax, color="gray", alpha =0.3, edgecolor="none")

            #shadow overlay in black
            if not shadows.empty:
                shadows.plot(ax=ax, color="black", alpha=0.2)

            #sites on top in red
            if not sites_gdf.empty:
                sites_gdf.plot(ax=ax, color="gray", edgecolor="black", linewidth=0.7)

            plt.title("Sites, Buildings, and Shadows", fontsize=16)
            ax.set_aspect("equal")
            plt.legend(["Buildings", "Shadows", "Sites"], fontsize=12)
            plt.show()

        elif self.feature == "All":
            #barriers
            highways = self.safe_notna(barriers_gdf, "highway")
            railways = self.safe_filter(barriers_gdf, "railway", "rail")

            #nature
            parks     = self.safe_filter(nature_gdf, "leisure", "park")
            forests   = self.safe_filter(nature_gdf, "landuse", "forest")
            wood      = self.safe_filter(nature_gdf, "natural", "wood")
            grass     = self.safe_filter(nature_gdf, "landuse", "grass")
            cemetery  = self.safe_filter(nature_gdf, "landuse", "cemetery")
            garden    = self.safe_filter(nature_gdf, "leisure", "garden")
            water     = self.safe_filter(nature_gdf, "natural", "water")

            #buildings
            def building_type(value): return self.safe_filter(buildings_mod_gdf, "building", value)
            houses     = building_type("house")
            apartments = building_type("apartments")
            residential = building_type("residential")
            dormitory  = building_type("dormitory")
            semidetached_house = building_type("semidetached_house")
            terrace    = building_type("terrace")
            schools    = building_type("school")
            kindergarten = building_type("kindergarten")
            office     = building_type("office")
            university = building_type("university")
            retail     = building_type("retail")
            commercial = building_type("commercial")
            civic      = building_type("civic")
            industrial = building_type("industrial")
            warehouse  = building_type("warehouse")
            divbuildings = building_type("yes")
            public     = building_type("public")
            church     = building_type("church")
            temple     = building_type("temple")
            presbytery = building_type("presbytery")
            parking = self.safe_filter(buildings_gdf, "amenity", "parking")
            museum = building_type("museum")

            #cycle
            residential_cycle = self.safe_filter(cycle_gdf, "highway", "residential")
            bicycle           = self.safe_filter(cycle_gdf, "bicycle", "yes")
            cycleway          = self.safe_filter(cycle_gdf, "highway", "cycleway")

            fig, ax = plt.subplots(figsize=(10, 10))
            legend_handles = []

            #barriers
            legend_handles.append(self.plot_if_not_empty(highways, ax, "gray", "Highways", is_line=True))
            legend_handles.append(self.plot_if_not_empty(railways, ax, "red", "Railways", is_line=True, linewidth=0.1))

            #nature: Green
            self.plot_if_not_empty(parks, ax, "green", None, alpha=0.5)
            self.plot_if_not_empty(forests, ax, "green", None, alpha=0.3)
            self.plot_if_not_empty(wood, ax, "green", None, alpha=0.3)
            self.plot_if_not_empty(grass, ax, "green", None, alpha=0.5)
            self.plot_if_not_empty(cemetery, ax, "green", None, alpha=0.3)
            self.plot_if_not_empty(garden, ax, "green", None, alpha=0.3)
            if any([not gdf.empty for gdf in [parks, forests, wood, grass, cemetery, garden]]):
                legend_handles.append(mpatches.Patch(color="green", alpha=0.5, label="Nature"))

            #nature: Water
            self.plot_if_not_empty(water, ax, "blue", None, alpha=0.3)
            if any([not gdf.empty for gdf in [water]]):
                legend_handles.append(mpatches.Patch(color="blue", alpha=0.5, label="Water"))

            #nuildings
            legend_handles.append(self.plot_if_not_empty(houses, ax, "orange", "Houses"))
            legend_handles.append(self.plot_if_not_empty(apartments, ax, "purple", "Apartments"))
            legend_handles.append(self.plot_if_not_empty(residential, ax, "purple", None))
            legend_handles.append(self.plot_if_not_empty(dormitory, ax, "purple", None))
            legend_handles.append(self.plot_if_not_empty(semidetached_house, ax, "orange", None))
            legend_handles.append(self.plot_if_not_empty(terrace, ax, "orange", None))
            legend_handles.append(self.plot_if_not_empty(parking, ax, "orange", None))

            legend_handles.append(self.plot_if_not_empty(schools, ax, "red", "Schools"))
            legend_handles.append(self.plot_if_not_empty(kindergarten, ax, "pink", "Kindergartens"))
            legend_handles.append(self.plot_if_not_empty(office, ax, "blue", "Office"))
            legend_handles.append(self.plot_if_not_empty(university, ax, "rosybrown", "University"))
            legend_handles.append(self.plot_if_not_empty(divbuildings, ax, "black", "Unlabeled"))
            legend_handles.append(self.plot_if_not_empty(public, ax, "skyblue", "Public"))
            legend_handles.append(self.plot_if_not_empty(museum, ax, "skyblue", None))

            #industrial 
            self.plot_if_not_empty(industrial, ax, "grey", None)
            self.plot_if_not_empty(warehouse, ax, "grey", None)
            self.plot_if_not_empty(civic, ax, "grey", None)
            if any([not gdf.empty for gdf in [industrial, warehouse, civic]]):
                legend_handles.append(mpatches.Patch(color="grey", label="Industrial"))

            #retail  
            self.plot_if_not_empty(retail, ax, "mediumpurple", None)
            self.plot_if_not_empty(commercial, ax, "mediumpurple", None)
            if any([not gdf.empty for gdf in [retail, commercial]]):
                legend_handles.append(mpatches.Patch(color="mediumpurple", label="Retail"))

            #religious
            self.plot_if_not_empty(church, ax, "brown", None)
            self.plot_if_not_empty(temple, ax, "brown", None)
            self.plot_if_not_empty(presbytery, ax, "brown", None)
            if any([not gdf.empty for gdf in [church, temple, presbytery]]):
                legend_handles.append(mpatches.Patch(color="brown", label="Religious"))

            #cycle
            self.plot_if_not_empty(residential_cycle, ax, "teal", None)
            self.plot_if_not_empty(bicycle, ax, "teal", None)
            self.plot_if_not_empty(cycleway, ax, "teal", None)
            if any([not gdf.empty for gdf in [residential_cycle, bicycle, cycleway]]):
                legend_handles.append(mpatches.Patch(color="teal", label="Cycleways"))

            #clean and plot
            legend_handles = [h for h in legend_handles if h is not None]
            plt.legend(handles=legend_handles, fontsize=14)
            minx, miny, maxx, maxy = nature_gdf.total_bounds
            ax.set_xlim(minx + 400, maxx - 300)
            ax.set_ylim(miny + 800, maxy - 800)
            plt.show()
            plt.show()


