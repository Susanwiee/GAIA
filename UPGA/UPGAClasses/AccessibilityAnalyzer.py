##### AccessibilityAnalyzer ###
#this class is used in the fitness functions for walkability and cycleability in the UPGA

from shapely.geometry import LineString
from shapely.ops import unary_union
import geopandas as gpd

class AccessibilityAnalyzer:
    def __init__(self, sites_gdf, buildings_gdf, nature_gdf, barriers_gdf, cycle_gdf, accessability_building_type="school", D_max=500):
        self.sites_gdf = sites_gdf
        self.buildings_gdf = buildings_gdf
        self.nature_gdf = nature_gdf
        self.barriers_gdf = barriers_gdf
        self.cycle_gdf = cycle_gdf
        self.accessability_building_type = accessability_building_type
        self.D_max = D_max

        #ensure 'highway' column exists before filtering
        if "highway" in self.barriers_gdf.columns:
            self.highways = self.barriers_gdf[self.barriers_gdf["highway"].notna()]
        else:
            self.highways = gpd.GeoDataFrame(columns=self.barriers_gdf.columns, geometry=self.barriers_gdf.geometry)

        #ensure 'railway' column exists before filtering
        if "railway" in self.barriers_gdf.columns:
            self.railways = self.barriers_gdf[self.barriers_gdf["railway"] == "rail"]
        else:
            self.railways = gpd.GeoDataFrame(columns=self.barriers_gdf.columns, geometry=self.barriers_gdf.geometry)


        #precompute spatial indexes 
        self.nature_index = self.nature_gdf.sindex
        self.highway_index = self.highways.sindex
        self.railway_index = self.railways.sindex

    def compute_walkability_score(self, individual):
        return self._compute_access_score(individual, mode="walk")

    def compute_cycleability_score(self, individual):
        return self._compute_access_score(individual, mode="cycle")

    def _compute_access_score(self, individual, mode="walk"):
        total_score = 0
        count = 0

        #destination centroids 
        dest_centroids = {
            name: self.sites_gdf[self.sites_gdf["name"] == b["site"]].geometry.iloc[0].centroid
            for name, b in individual.items()
            if b["type"] == self.accessability_building_type
        }

        #residential origins
        res_types = ["house", "apartments", "residential", "dormitory", "semidetached_house", "terrace"]
        home_buildings = self.buildings_gdf[self.buildings_gdf["building"].isin(res_types)]

        for _, home in home_buildings.iterrows():
            origin = home.geometry.centroid

            for _, dest in dest_centroids.items():
                line = LineString([origin, dest])
                if line.length == 0:
                    continue

                D_score = max(0, 1 - (line.length / self.D_max))

                if mode == "walk":
                    #fast bounding-box filtering with spatial index
                    nature_idx = list(self.nature_index.intersection(line.bounds))
                    nature_hits = self.nature_gdf.iloc[nature_idx]
                    nature_hits = nature_hits[nature_hits.geometry.intersects(line)]

                    highway_idx = list(self.highway_index.intersection(line.bounds))
                    highway_hits = self.highways.iloc[highway_idx]
                    highway_hits = highway_hits[highway_hits.geometry.intersects(line)]

                    railway_idx = list(self.railway_index.intersection(line.bounds))
                    railway_hits = self.railways.iloc[railway_idx]
                    railway_hits = railway_hits[railway_hits.geometry.intersects(line)]

                    barrier_hits = (len(highway_hits) + len(railway_hits)) / 2
                    nature_score = min(1, len(nature_hits) / 4)
                    barrier_score = min(1, barrier_hits / 4)

                    C_score = max(0, nature_score - barrier_score)

                elif mode == "cycle":
                    cycle_buffer = unary_union(self.cycle_gdf.geometry).buffer(10)
                    intersection = line.intersection(cycle_buffer)
                    length_inside = intersection.length
                    length_total = line.length
                    C_score = length_inside / length_total if length_total > 0 else 0.0

                else:
                    raise ValueError(f"Unsupported access mode: {mode}")
                
                W_d = 0.5
                W_c = 0.5

                raw_score = W_d * D_score + W_c * C_score
                score = min(1.0, max(0.0, raw_score))

                total_score += score
                count += 1

        return round(total_score / count, 3) if count > 0 else 0.0
