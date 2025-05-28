###ShadowAnalyzer.py###
#class used to generate shadow geometires for shadow related fitness functions in the UPGA

import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
import numpy as np
from shapely.ops import unary_union

class ShadowAnalyzer:
    def __init__(self, gdf, height_dict, crs=None):
        self.crs = crs 
        self.sites_gdf = gdf.copy().to_crs(self.crs)
        self.sites_gdf['height'] = self.sites_gdf['name'].map(height_dict).fillna(15)
        self.shadow_gdf = None

    def calculate_shadows(self, azimuth_deg, altitude_deg):
        azimuth_rad = np.radians(azimuth_deg)
        altitude_rad = np.radians(altitude_deg)
        shadow_length_factor = 1 / np.tan(altitude_rad)  

        shadows = []
        for _, row in self.sites_gdf.iterrows():
            geom = row.geometry
            height = row.height

            #using Equation (3) in thesis
            #shadow projection offsets 
            dx = -height * shadow_length_factor * np.sin(azimuth_rad)
            dy = -height * shadow_length_factor * np.cos(azimuth_rad)

            coords = list(geom.exterior.coords)
            shadow_coords = [(x + dx, y + dy) for x, y in coords]

            #create polygons for each side of the building connecting to its shadow
            for i in range(len(coords) - 1):
                corner = Polygon([
                    coords[i],
                    coords[i + 1],
                    shadow_coords[i + 1],
                    shadow_coords[i]
                ])
                shadows.append(corner)
            #polygon representing the full shadow projection of the building footprint
            shadows.append(Polygon(shadow_coords))

        #store all shadow polygons in a GeoDataFrame (same CRS)
        self.shadow_gdf = gpd.GeoDataFrame(geometry=shadows, crs=self.crs)

    def plot(self, azimuth_deg, altitude_deg):
        if self.shadow_gdf is None:
            raise ValueError("Shadows not yet calculated. Call calculate_shadows first.")

        fig, ax = plt.subplots(figsize=(10, 10))
        #plot shadow polygons
        self.shadow_gdf.plot(ax=ax, color='darkgray', alpha=0.7, edgecolor='none', label='Shadows')
        #label each building by site name at its centroid
        for _, row in self.sites_gdf.iterrows():
            centroid = row.geometry.centroid
            ax.annotate(row['name'], (centroid.x, centroid.y), fontsize=9, ha='center')

        plt.title(f"Shadow Analysis (Azimuth: {azimuth_deg}°, Altitude: {altitude_deg}°)")
        plt.axis('equal')
        plt.xlabel('X coordinate (m)')
        plt.ylabel('Y coordinate (m)')
        plt.legend()
        plt.show()

    def get_shadow_data(self):
        #returns a GeoDataFrame with one entry per site,containing the union of all shadow polygons 
        site_shadow_data = []
        for site_name in self.sites_gdf["name"]:
            building = self.sites_gdf[self.sites_gdf["name"] == site_name].iloc[0]
            relevant_shadows = self.shadow_gdf[self.shadow_gdf.geometry.intersects(building.geometry.buffer(200))]
            merged_shadow = unary_union(relevant_shadows.geometry)
            total_area = merged_shadow.area

            site_shadow_data.append({
                "site": site_name,
                "shadow_area_m2": round(total_area, 2),
                "shadow_geometry": merged_shadow
            })
        return gpd.GeoDataFrame(site_shadow_data, geometry="shadow_geometry", crs=self.crs)


#Eksample for or plotting 
def plot_shadow_from_gdf(gdf, height_dict=None, azimuth_deg=180, altitude_deg=30, crs="EPSG:32632"):
    if height_dict is None:
        height_dict = {name: 10 for name in gdf['name'].unique()}
    analyzer = ShadowAnalyzer(gdf, height_dict, crs=crs)
    analyzer.calculate_shadows(azimuth_deg, altitude_deg)
    return analyzer.shadow_gdf
