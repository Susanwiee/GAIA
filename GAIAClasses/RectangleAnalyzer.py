### RectangleAnalyzer.py## 
#This class is used in the GAIA framework to convert geospatial site data into usable parameters

import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import box, Polygon
from shapely.affinity import rotate
from matplotlib.patches import Polygon as MplPolygon, FancyArrow
from typing import List, Tuple
from mpl_toolkits.axes_grid1.inset_locator import inset_axes


class RectangleAnalyzer:
    def __init__(self, geo_data):
        self.sites_gdf = geo_data["sites"]
        self.valid_sites: List[Tuple[str, Polygon, Polygon, float]] = []  # (name, polygon, rect, angle)
        self.ga_site_parameters: List[dict] = []
        self._process_sites()

    def largest_rectangle_fitting_inside(self, polygon: Polygon, angle_resolution: int = 1) -> Tuple[Polygon, float, float]:
        max_area = 0
        best_rectangle = None
        best_angle = 0

        for angle in np.arange(0, 180, angle_resolution):
            rotated = rotate(polygon, angle, origin='centroid', use_radians=False)
            minx, miny, maxx, maxy = rotated.bounds

            for scale in np.linspace(1.0, 0.5, 20):
                cx, cy = rotated.centroid.x, rotated.centroid.y
                w = (maxx - minx) * scale / 2
                h = (maxy - miny) * scale / 2
                rect = box(cx - w, cy - h, cx + w, cy + h)

                if rotated.contains(rect):
                    area = rect.area
                    if area > max_area:
                        max_area = area
                        best_rectangle = rotate(rect, -angle, origin='centroid', use_radians=False)
                        best_angle = angle
                    break

        return best_rectangle, max_area, best_angle
    
    def get_rectangle_orientation(self, rect: Polygon) -> float:
        coords = list(rect.exterior.coords)[:4]
        max_length = 0
        main_angle = 0

        for i in range(4):
            p1, p2 = coords[i], coords[(i + 1) % 4]
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            length = np.hypot(dx, dy)

            if length > max_length:
                max_length = length
                angle_from_east = np.degrees(np.arctan2(dy, dx))  # standard angle from +X axis (East)
                angle_from_north = (90 - angle_from_east) % 360  # convert to compass angle (0° = North)
                main_angle = angle_from_north

        return round(main_angle, 1)

    def _get_rectangle_orientation_and_dims(self, rect: Polygon) -> Tuple[float, float, float]:
        coords = list(rect.exterior.coords)[:4]
        edge_vectors = []
        for i in range(4):
            p1 = coords[i]
            p2 = coords[(i + 1) % 4]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            edge_vectors.append(((dx, dy), np.hypot(dx, dy)))

        main_vector, main_length = max(edge_vectors, key=lambda item: item[1])
        secondary_length = min(edge_vectors, key=lambda item: item[1])[1]
        angle = np.degrees(np.arctan2(main_vector[1], main_vector[0])) % 360
        return round(angle, 2), round(main_length, 2), round(secondary_length, 2)

    def _process_sites(self):
        for _, row in self.sites_gdf.iterrows():
            name = row.get("name", "Unnamed")
            geom = row.geometry
            if geom.is_valid and geom.area < 1e6:
                rect, _, _ = self.largest_rectangle_fitting_inside(geom)
                self.valid_sites.append((name, geom, rect, 0))  # angle not used anymore here

                if rect:
                    _, length, width = self._get_rectangle_orientation_and_dims(rect)
                    angle = self.get_rectangle_orientation(rect)
                    centroid = rect.centroid
                    self.ga_site_parameters.append({
                        "site": name,
                        "site_length": length,
                        "site_width": width,
                        "orientation": angle,
                        "position_x": round(centroid.x, 2),
                        "position_y": round(centroid.y, 2)
                    })

    def plot_site_rectangles(self):
        fig, ax = plt.subplots(figsize=(10, 10))
        for name, geom, rect, _ in self.valid_sites:
            ax.add_patch(MplPolygon(list(geom.exterior.coords), edgecolor='black', facecolor='lightgray', alpha=0.5))
            if rect:
                ax.add_patch(MplPolygon(list(rect.exterior.coords), edgecolor='blue', facecolor='none', linewidth=2))
                match = next(p for p in self.ga_site_parameters if p["site"] == name)
                label = f"L={round(match['site_length'],1)}\nW={round(match['site_width'],1)}\nA={match['orientation']}\u00b0"
                centroid = rect.centroid
                ax.text(centroid.x , centroid.y, label, fontsize=8, ha='center', va='center', color='blue')


        all_bounds = [geom.bounds for _, geom, _, _ in self.valid_sites]
        minx = min(b[0] for b in all_bounds)
        miny = min(b[1] for b in all_bounds)
        maxx = max(b[2] for b in all_bounds)
        maxy = max(b[3] for b in all_bounds)
        ax.set_xlim(minx - 100, maxx + 100)
        ax.set_ylim(miny - 100, maxy + 100)

        self._add_compass_rose(ax)
        ax.set_aspect('equal')
        ax.set_title("Sites and Largest Inscribed Rectangles", fontsize=14)

        ax.grid(True)
        plt.show()

    def _add_compass_rose(self, ax):
        inset_ax = inset_axes(ax, width="10%", height="10%", loc='lower right', borderpad=2)
        inset_ax.set_xlim(-2.5, 2.5)
        inset_ax.set_ylim(-2.5, 2.5)
        inset_ax.axis("off")

        def draw_arrow(dx, dy, label, ha, va):
            inset_ax.add_patch(FancyArrow(0, 0, dx, dy, width=0.1, head_width=0.3, head_length=0.3, length_includes_head=True, color='black'))
            inset_ax.text(dx * 1.2, dy * 1.2, label, fontsize=14, ha=ha, va=va)

        draw_arrow(0, 1.8, "N", 'center', 'bottom')
        draw_arrow(1.8, 0, "E", 'left', 'center')
        draw_arrow(0, -1.8, "S", 'center', 'top')
        draw_arrow(-1.8, 0, "W", 'right', 'center')

    def 