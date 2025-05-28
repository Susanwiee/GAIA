# UPGA.py ##

#Urban Planning Genetic Algorithm (UPGA), takes input parameters such as  
# output_path (.txt), Cordinate reference system (crs), geo_data (dictionary), building_specs (dictionary) and azimuth & altitude sun angles
#Returns the best urban configurations of buildings based on a weighted sum of mutliple fitness functions 

#for usage go to "UPGAmain.py"

#importing python libraries 
import random
import copy
import geopandas as gpd
from shapely.ops import unary_union
import os

#import matplotlib for plotting
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

#importing classes
from UPGA.UPGAClasses.ShadowAnalyzer import ShadowAnalyzer, plot_shadow_from_gdf
from UPGA.UPGAClasses.AccessibilityAnalyzer import AccessibilityAnalyzer

class UPGA:
    def __init__(self, output_path, crs, geo_data, building_specs, azimuth, altitude, 
                 accessability_building_type="school", 
                 serviceavailability_building_type=["apartment", "office"], 
                 k_n=None, k_b=None, popsize=100, generations=200, mutProb=0.1,  
                 plot=False, PlotRun=False):
        
        self.output_path = output_path
        self.crs = crs
        self.sites_gdf = geo_data["sites"]
        self.buildings_gdf = geo_data["buildings"]
        self.barriers_gdf = geo_data["barriers"]
        self.cycle_gdf = geo_data["cycle"]
        self.nature_gdf = geo_data["nature"]
        self.services_gdf = geo_data["services"]
        self.existing_gdf = geo_data["existing"]

        self.building_specs = building_specs
        self.population = []
        self.popsize = popsize
        self.generations = generations
        self.mutProb = mutProb
        self.site_areas = self.CalculateSiteArea(self.sites_gdf)
        self.footprint_ratio = 0.7
        self.floor_height = 2.26
        self.plot = plot
        self.PlotRun = PlotRun
        self.accessability_building_type = accessability_building_type
        self.serviceavailability_building_type = serviceavailability_building_type
        self.azimuth = azimuth
        self.altitude = altitude

        # Determine max distance in area (for walkability/cycleability scaling)
        minx, miny, maxx, maxy = self.buildings_gdf.total_bounds
        width_m = maxx - minx
        height_m = maxy - miny
        self.D_max = max(width_m, height_m)

        # Set k_n and k_b defaults if not provided
        self.k_n = k_n if k_n is not None else len(self.nature_gdf)
        self.k_b = k_b if k_b is not None else len(self.barriers_gdf)        

        #initializing accessibility analyzer for walkability/cycleability
        self.access_analyzer = AccessibilityAnalyzer(
            self.sites_gdf, 
            self.buildings_gdf, 
            self.nature_gdf, 
            self.barriers_gdf, 
            self.cycle_gdf, 
            self.accessability_building_type, 
            self.D_max
        )
        
        #scaling factors for shadow-on-building penalty
        self.S_a = 50.0  # weight for area penalty
        self.S_h = 1.0  # weight for area penalty

        #scaling factor for shadow-on-nature penelty
        self.S_n = 5

    def CalculateSiteArea(self, sites_gdf):
        #calculating area for each site and returns a dict {site_name: area_m2}
        sites_gdf['area_m2'] = sites_gdf.geometry.area.round(2)
        return dict(zip(sites_gdf['name'], sites_gdf['area_m2']))

    def initialize_population(self):
        #initiliazes a population with a population size 
        site_ids = self.sites_gdf["name"].tolist()
        if len(site_ids) < len(self.building_specs):
            raise ValueError("Not enough unique sites to assign each building.")

        for _ in range(self.popsize):
            individual = {}
            available_sites = site_ids.copy()
            for name, spec in self.building_specs.items():
                site = random.choice(available_sites)
                available_sites.remove(site)
                floors = random.randint(1, 15)
                site_area = round(self.site_areas[site], 0)

                target_gfa = spec["target_gfa"]
                if target_gfa < self.site_areas[site] * self.footprint_ratio:
                    #if target GFA is small enough to fit on one floor 
                    gfa = target_gfa
                    floors = 1
                else:
                    #otherwise, assign floors and compute GFA based on footprint_ratio
                    gfa = site_area * self.footprint_ratio * floors

                individual[name] = {
                    "site": site,
                    "type": spec["type"],
                    "height": floors * self.floor_height,
                    "gfa": round(gfa)
                }
            self.population.append(individual)

    # Fitness functions
    def compute_fitness_gfa(self, individual):
        #computing fitness based on how close actual GFA (via floors) is to target GFA

        total_score = 0.0
        for name, values in individual.items():
            target_gfa = self.building_specs[name]["target_gfa"]
            actual_height = values["height"]
            actual_floors = actual_height / self.floor_height
            site_name = values["site"]
            site_area = self.site_areas.get(site_name, 0)

            if site_area <= 0 or self.footprint_ratio <= 0:
                score = 0.0
            else:
                ideal_floors = target_gfa // (site_area * self.footprint_ratio) if site_area * self.footprint_ratio > 0 else 0
                floor_deviation = abs(actual_floors - ideal_floors)
                score = 1 - (floor_deviation / ideal_floors) if ideal_floors > 0 else 0.0
                score = max(0.0, min(score, 1.0))
            total_score += score

        avg_score = total_score / len(individual) if len(individual) > 0 else 0.0
        return round(avg_score, 2)

    def compute_shadow_nature_fitness(self, individual):
        #Fitness score for shadows of new buildings falling on nature zones.
        # Prepare height mapping from the GA individual
        height_dict = {values["site"]: values["height"] for values in individual.values()}

        # Calculate shadow polygons for new buildings
        analyzer = ShadowAnalyzer(self.sites_gdf, height_dict, crs=self.crs)
        analyzer.calculate_shadows(self.azimuth, self.altitude)
        shadow_gdf = analyzer.get_shadow_data()

        # Filter nature zones to polygonal areas
        nature_gdf = self.nature_gdf[self.nature_gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])].copy()

        # Overlay shadows on nature areas to find intersections
        shadow_hits = gpd.overlay(shadow_gdf, nature_gdf, how='intersection')

        # Calculate shadow penalty as fraction of nature area covered (weighted by 5x factor)
        total_nature_area = nature_gdf.geometry.area.sum()
        penalty_area = shadow_hits.geometry.area.sum()
        shadow_fitness = 1 - ((penalty_area * self.S_n) / total_nature_area)
        if shadow_fitness > 1:
            shadow_fitness = 1.0
        return max(shadow_fitness, 0.0), penalty_area

    def compute_walkability_fitness(self, individual):
        """Delegated to AccessibilityAnalyzer: average walkability score for this configuration."""
        walk_score = self.access_analyzer.compute_walkability_score(individual)
        # print("Walkability fitness= ", round(walk_score, 2))
        return walk_score

    def compute_cycleability_fitness(self, individual):
        """Delegated to AccessibilityAnalyzer: average cycleability score for this configuration."""
        cycle_score = self.access_analyzer.compute_cycleability_score(individual)
        return cycle_score

    def compute_serviceavailability_apartments_fitness(self, individual):
        """Fitness for service availability (e.g., shops) near apartment-type buildings."""
        apartment_centroids = {
            name: self.sites_gdf[self.sites_gdf["name"] == b["site"]].geometry.iloc[0].centroid
            for name, b in individual.items()
            if b["type"] == self.serviceavailability_building_type[0]
        }
        if not apartment_centroids:
            return 0.0

        # Consider nearby shops or supermarkets as services
        service_spots = self.services_gdf.copy()
        relevant_services = service_spots[
            service_spots["shop"].notna() |
            (service_spots["amenity"].isin(["cafe", "supermarket"]))
        ].copy()
        if relevant_services.empty:
            return 0.0

        relevant_services["centroid"] = relevant_services.geometry.centroid
        total_distance = 0.0
        count = 0
        for _, service_row in relevant_services.iterrows():
            s_pt = service_row["centroid"]
            for _, a_pt in apartment_centroids.items():
                total_distance += s_pt.distance(a_pt)
                count += 1

        if count == 0:
            return 0.0
        avg_dist = total_distance / count
        service_score = min(1.0, 1 - avg_dist / self.D_max)
        return round(max(0.0, service_score), 3)

    def compute_serviceavailability_offices_fitness(self, individual):
        """Fitness for service availability (e.g., cafes/restaurants) near office-type buildings."""
        office_centroids = {
            name: self.sites_gdf[self.sites_gdf["name"] == b["site"]].geometry.iloc[0].centroid
            for name, b in individual.items()
            if b["type"] == self.serviceavailability_building_type[1]
        }
        if not office_centroids:
            return 0.0

        service_spots = self.services_gdf.copy()
        relevant_services = service_spots[service_spots["amenity"].isin(["cafe", "restaurant"])].copy()
        if relevant_services.empty:
            return 0.0

        relevant_services["centroid"] = relevant_services.geometry.centroid
        total_distance = 0.0
        count = 0
        for _, service_row in relevant_services.iterrows():
            s_pt = service_row["centroid"]
            for _, o_pt in office_centroids.items():
                total_distance += s_pt.distance(o_pt)
                count += 1

        if count == 0:
            return 0.0
        avg_dist = total_distance / count
        service_score = min(1.0, 1 - avg_dist / self.D_max)
        return round(max(0.0, service_score), 3)

    def compute_shadow_building_fitness(self, individual):
        """
        Computes fitness penalty for shadows between new and existing buildings:
        - Penalizes new buildings casting shadows on existing ones (especially if taller).
        - Penalizes existing buildings casting shadows on new ones.
        Returns a fitness score (1.0 is best), plus details of which buildings are shadowed or not.
        """
        # Prepare existing buildings GeoDataFrame with heights
        existing_gdf = self.existing_gdf.copy()
        existing_gdf['height_m'] = existing_gdf['height'].astype(float)
        existing_gdf = existing_gdf[existing_gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])].copy()

        # Prepare new buildings GeoDataFrame with geometry and height
        new_buildings = []
        for b_name, b_values in individual.items():
            site_name = b_values["site"]
            site_geom = self.sites_gdf[self.sites_gdf["name"] == site_name].geometry.iloc[0]
            height_m = b_values["height"]
            new_buildings.append((b_name, site_geom, height_m))
        new_gdf = gpd.GeoDataFrame(
            [{'name': name, 'geometry': geom, 'height_m': h} for name, geom, h in new_buildings],
            crs=self.crs
        )

        # Spatial indexes for faster intersection queries
        existing_sindex = existing_gdf.sindex
        new_sindex = new_gdf.sindex

        total_roof_area = existing_gdf.geometry.area.sum() + new_gdf.geometry.area.sum()

        shadowed_by_individual = {b_name: [] for b_name in individual.keys()}
        not_shadowed_by_individual = {b_name: [] for b_name in individual.keys()}
        affected_ids = set()
        shadow_on_new_buildings = {}
        shadow_on_new_buildings_full = {}

        def compute_shadow_geometry(name, geom, height):
            """Helper: compute the shadow geometry polygon(s) for a single building."""
            temp_gdf = gpd.GeoDataFrame([{'name': name, 'geometry': geom}], crs=self.crs)
            analyzer = ShadowAnalyzer(temp_gdf, {name: height}, crs=self.crs)
            analyzer.calculate_shadows(self.azimuth, self.altitude)
            return unary_union(analyzer.shadow_gdf.geometry)

        # 1. Shadows from each new building onto existing buildings
        shadow_conflicts_area_existing = 0.0
        for b_name, geom, height in new_buildings:
            shadow_geom_new = compute_shadow_geometry(b_name, geom, height)
            # Check existing buildings that lie within the bounds of this shadow geometry
            possible_idxs = list(existing_sindex.intersection(shadow_geom_new.bounds))
            for _, exist_row in existing_gdf.iloc[possible_idxs].iterrows():
                exist_geom = exist_row.geometry
                exist_height = exist_row['height_m']
                exist_id = exist_row.get("@id", exist_row.name)  # use '@id' if present, otherwise index
                if shadow_geom_new.intersects(exist_geom):
                    overlap_area = shadow_geom_new.intersection(exist_geom).area
                    if overlap_area > 0:
                        if height > exist_height:
                            # New building overshadows this existing building
                            shadow_conflicts_area_existing += overlap_area
                            shadowed_by_individual[b_name].append({
                                "geometry": exist_geom,
                                "existing_height": exist_height,
                                "overlap_area": overlap_area,
                                "id": exist_id
                            })
                            affected_ids.add(exist_id)
                        elif height < exist_height:
                            # Existing building is taller (new building not causing shadow issue here)
                            not_shadowed_by_individual[b_name].append({
                                "geometry": exist_geom,
                                "existing_height": exist_height,
                                "overlap_area": overlap_area,
                                "id": exist_id
                            })

        # 2. Shadows from each existing building onto new buildings
        shadow_conflicts_area_new = 0.0
        for _, exist_row in existing_gdf.iterrows():
            exist_geom = exist_row.geometry
            exist_height = exist_row['height_m']
            e_name = str(exist_row.name)
            shadow_geom_exist = compute_shadow_geometry(e_name, exist_geom, exist_height)

            possible_idxs = list(new_sindex.intersection(shadow_geom_exist.bounds))
            for _, new_row in new_gdf.iloc[possible_idxs].iterrows():
                new_geom = new_row.geometry
                new_height = new_row['height_m']
                new_name = new_row['name']
                if shadow_geom_exist.intersects(new_geom):
                    overlap_area = shadow_geom_exist.intersection(new_geom).area
                    if overlap_area > 0 and exist_height > new_height:
                        # Existing building (taller) casts shadow on new building
                        shadow_conflicts_area_new += overlap_area
                        #for plotting
                        if new_name in shadow_on_new_buildings:
                            # combine multiple shadows on the same new building
                            shadow_on_new_buildings[new_name] = unary_union([
                                shadow_on_new_buildings[new_name],
                                shadow_geom_exist
                            ])
                        else:
                            shadow_on_new_buildings[new_name] = shadow_geom_exist
                        #for reporting
                                            # For reporting
                        if new_name not in shadow_on_new_buildings_full:
                            shadow_on_new_buildings_full[new_name] = []

                        shadow_on_new_buildings_full[new_name].append({
                            "id": exist_id,
                            "existing_height": exist_height,
                            "overlap_area": overlap_area
                        })


        #computing penalties for shadow on building
        total_conflict_area = shadow_conflicts_area_existing + shadow_conflicts_area_new
        penalty_ratio = total_conflict_area / total_roof_area if total_roof_area > 0 else 1.0

        area_penalty = min(penalty_ratio * self.S_a, 1.0)
        total_existing = len(existing_gdf)
        hit_ratio = (len(affected_ids)*self.S_h) / total_existing if total_existing > 0 else 1.0
        hit_penalty = min(hit_ratio, 1.0)

        # Weighted combination of area coverage penalty and number-of-buildings-hit penalty
        weight_area = 0.4
        weight_hits = 0.7
        combined_penalty = weight_area * area_penalty + weight_hits * hit_penalty

        #normalizing and defining fitness score
        fitness_score = 1.0 - combined_penalty
        fitness_score = max(0.0, min(1.0, fitness_score))

        return round(fitness_score, 3), shadowed_by_individual, not_shadowed_by_individual, shadow_on_new_buildings, shadow_conflicts_area_new, shadow_conflicts_area_existing, shadow_on_new_buildings_full  

    def fitness(self, individual):
        #MOGA: calculating overall fitness as weighted sum of sub-fitnesses
        
        #equal weighting for all objectives, insert preferred weighting
        weight_gfa = 0.1667
        weight_shadow_nature = 0.1667
        weight_walk = 0.1667
        weight_cycle = 0.1667
        weight_service = 0.1667
        weight_shadow_building = 0.1667

        gfa_fitness = self.compute_fitness_gfa(individual)
        shadow_fitness_nature, _ = self.compute_shadow_nature_fitness(individual)
        walk_fitness = self.compute_walkability_fitness(individual)
        cycle_fitness = self.compute_cycleability_fitness(individual)
        service_fitness = (self.compute_serviceavailability_apartments_fitness(individual) + 
                           self.compute_serviceavailability_offices_fitness(individual)) / 2.0
        building_shadow_fitness, _, _, _ , _, _, _= self.compute_shadow_building_fitness(individual)

        total_fitness = (
            weight_gfa * gfa_fitness +
            weight_shadow_nature * shadow_fitness_nature +
            weight_walk * walk_fitness +
            weight_cycle * cycle_fitness +
            weight_service * service_fitness +
            weight_shadow_building * building_shadow_fitness
        )
        return total_fitness

    # Genetic operators
    def crossover(self, parent1, parent2):
        #combining two parent individuals to produce a child
        child = {}

        #random choise for which parent contributes heights and which contributes site assignments
        height_parent = random.choice([1, 2])
        site_parent = 2 if height_parent == 1 else 1

        for name in self.building_specs:
            height = parent1[name]["height"] if height_parent == 1 else parent2[name]["height"]
            site = parent1[name]["site"] if site_parent == 1 else parent2[name]["site"]

            type_ = self.building_specs[name]["type"]
            floors = height / self.floor_height

            #update GFA
            gfa = self.site_areas[site] * self.footprint_ratio * floors

            child[name] = {
                "site": site,
                "type": type_,
                "height": height,
                "gfa": round(gfa)
            }
        return child

    def mutate(self, individual):
        #randomly adjust height or swap sites between two buildings
        mutated = copy.deepcopy(individual)
        building_names = list(mutated.keys())
        if random.choice([True, False]):
            # Mutate height of one random building
            name = random.choice(building_names)
            current_height = mutated[name].get("height", 0)
            current_floors = int(round(current_height / self.floor_height)) if current_height else 0
            delta = random.choice([-3, -2, -1, 1, 2])
            new_floors = max(1, current_floors + delta)
            new_height = new_floors * self.floor_height
            mutated[name]["height"] = new_height
            site = mutated[name]["site"]

            #update GFA
            mutated[name]["gfa"] = round(self.site_areas[site] * self.footprint_ratio * new_floors)
        else:
            # Mutate by swapping the site assignments of two buildings (if more than one building)
            if len(building_names) < 2:
                return mutated  # no swap possible
            b1, b2 = random.sample(building_names, 2)
            site1 = mutated[b1]["site"]
            site2 = mutated[b2]["site"]
            # Swap sites
            mutated[b1]["site"], mutated[b2]["site"] = site2, site1
            # Recalculate GFA for both affected buildings
            h1 = mutated[b1]["height"]
            h2 = mutated[b2]["height"]
            mutated[b1]["gfa"] = round(self.site_areas[site2] * self.footprint_ratio * (h1 / self.floor_height))
            mutated[b2]["gfa"] = round(self.site_areas[site1] * self.footprint_ratio * (h2 / self.floor_height))
        
        return mutated

    def select(self, population, fitnesses, k):
        """Selection: pick the top-k individuals based on fitness (elitism selection)."""
        top_indices = sorted(range(len(fitnesses)), key=lambda i: fitnesses[i], reverse=True)[:k]
        return [population[i] for i in top_indices]

    def plot_individual(self, individual):
        """Plot the configuration of an individual (buildings and their shadows)."""
        # Create the height dictionary for the candidate
        height_dict = {values["site"]: values["height"] for values in individual.values()}

        # Generate distinct colors for each building in this individual
        names = list(individual.keys())
        cmap = cm.get_cmap("tab20", len(names))
        color_map = {name: mcolors.to_hex(cmap(i)) for i, name in enumerate(names)}

        # Prepare plot
        fig, ax = plt.subplots(figsize=(10, 10))

        # Compute and plot shadows from new buildings
        shadow_gdf = plot_shadow_from_gdf(self.sites_gdf, height_dict=height_dict, 
                                          azimuth_deg=self.azimuth, altitude_deg=self.altitude, crs=self.crs)

        # Plot background layers
        self.nature_gdf.plot(ax=ax, color="green", alpha=0.2, label="Nature")
        self.existing_gdf.plot(ax=ax, color="tan", alpha=1.0, label="Buildings")

        # Plot each site polygon with its assigned building color
        for name, values in individual.items():
            site_name = values["site"]
            site_color = color_map[name]
            site_geom = self.sites_gdf[self.sites_gdf["name"] == site_name]
            site_geom.plot(ax=ax, color=site_color, edgecolor="black", label=name)

        # Get shadow details for new vs existing buildings
        _, shadowed_info, not_shadowed_info, shadow_on_new_buildings, _, _,_ = self.compute_shadow_building_fitness(individual)

        # Plot shadows from new buildings
        shadow_gdf.plot(ax=ax, color="gray", alpha=0.3, label="Shadows (new buildings)")

        # Plot shadows cast by existing buildings onto new buildings (if any)
        for new_building, shadow_geom in shadow_on_new_buildings.items():
            gdf_shadow = gpd.GeoDataFrame([{'name': new_building, 'geometry': shadow_geom}], crs=self.crs)
            gdf_shadow.plot(ax=ax, color="darkgoldenrod", alpha=0.5, label="Shadows (existing on new)")

        # (Optional) Highlight existing buildings affected by shadows (if desired in future)
        # affected_ids = [data['id'] for affected in shadowed_info.values() for data in affected]
        # if affected_ids:
        #     affected_gdf = self.existing_gdf[self.existing_gdf["@id"].isin(affected_ids)]
        #     affected_gdf.plot(ax=ax, color="red", label="Affected Existing Buildings")

        # Build legend handles (shadows and each building)
        legend_handles = [
            # mpatches.Patch(color="green", alpha=0.2, label="Nature"),
            # mpatches.Patch(color="tan", label="Buildings"),
            mpatches.Patch(color="gray", alpha=0.3, label="Shadows from new buildings"),
            mpatches.Patch(color="darkgoldenrod", label="Shadows from existing buildings")
        ] + [
            mpatches.Patch(color=color_map[name], label=name) for name in individual.keys()
        ]

        ax.legend(handles=legend_handles)
        ax.set_title("Best Individual Configuration")
        minx, miny, maxx, maxy = self.buildings_gdf.total_bounds
        ax.set_xlim(minx - 200, maxx + 200)
        ax.set_ylim(miny - 0, maxy + 190)
        plt.show()
    
    def write_evaluation_report(self, output_path, individual):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("Urban Planning Layout - Evaluation Report")
        report_lines.append("_Delivered by GAIA_")  
        report_lines.append("=" * 60)

        # Best individual summary
        report_lines.append("\n Best Individual Configuration:")
        report_lines.append("-" * 60)
        for name, values in individual.items():
            height = values['height']
            gfa = values['gfa']
            footprint = gfa / (height / self.floor_height)
            report_lines.append(
                f"- {name:<10} | Site:   {values['site']}   | Type: {values['type']:<10} | "
                f"Max Height: {height:>5.1f} m | GFA: {gfa:>6.1f} m² | Footprint: {footprint:>6.1f} m²"
            )

        # Fitness scores
        report_lines.append("\nFitness Evaluation:")
        report_lines.append("-" * 60)
        gfa_fitness = self.compute_fitness_gfa(individual)
        shadow_nature_fitness, area_nature_conflict = self.compute_shadow_nature_fitness(individual)
        walkability = self.compute_walkability_fitness(individual)
        cycleability = self.compute_cycleability_fitness(individual)
        service_apartments = self.compute_serviceavailability_apartments_fitness(individual)
        service_offices = self.compute_serviceavailability_offices_fitness(individual)
        service_avg = (service_apartments + service_offices) / 2.0
        (
            shadow_new_fitness,
            shadowed_info,
            non_shadowed_info,
            shadow_on_new_buildings,
            conflict_area_new,
            conflict_area_existing,
            shadow_on_new_buildings_full
        ) = self.compute_shadow_building_fitness(individual)

        report_lines += [
            f"- GFA Fitness:                  {gfa_fitness:.3f}",
            f"- Shadow on Nature Fitness:     {shadow_nature_fitness:.3f}",
            f"- Shadow on Buildings Fitness:  {shadow_new_fitness:.3f}",
            f"- Walkability Fitness:          {walkability:.3f}",
            f"- Cycleability Fitness:         {cycleability:.3f}",
            f"- Serviceability Fitness:       {service_avg:.3f}",
            f"  └ For apartments:             {service_apartments:.3f}",
            f"  └ For offices:                {service_offices:.3f}",
            
        ]

        total_score = self.fitness(individual)
        report_lines.append(f"\nTotal Fitness Score: {total_score:.3f}")


        report_lines.append("\nFitness Explanation:")
        report_lines.append("-" * 60)

        if gfa_fitness > 0.5:
            report_lines.append(f"- GFA fitness is {gfa_fitness:.2f}, which indicates that the generated heights match the intended gross floor area well.")
        else:
            report_lines.append(f"- GFA fitness is {gfa_fitness:.2f}, which indicates that there's a mismatch between building heights and target floor areas, try another run with a increased number of generations and population size.")

        if shadow_nature_fitness > 0.5:
            report_lines.append(f"- Shadow on nature fitness is {shadow_nature_fitness:.2f}. This means that the design preserves sunlight access to green areas.")
        else:
            report_lines.append(f"- Shadow on nature fitness is {shadow_nature_fitness:.2f}. This means that many green zones are negatively affected by shadow, check if they are sensitive to lack of sunlight.")

        if walkability > 0.5:
            report_lines.append(f"- Walkability score is {walkability:.2f}. The {self.accessability_building_type}(s) are located where walking is convenient, safe and enjoyable.")
        else:
            report_lines.append(f"- Walkability score is {walkability:.2f}. Long distances or barriers make walking less attractive to the {self.accessability_building_type}(s) location.")

        # Cycleability
        if cycleability > 0.5:
            report_lines.append(f"- Cycleability score is {cycleability:.2f}. This indicates that there is good proximity to bike paths from the {self.accessability_building_type}(s) to residentials")
        else:
            report_lines.append(f"- Cycleability score is {cycleability:.2f}. This indicates limited cycling infrastructure from the {self.accessability_building_type}(s) ro residential, this could hinder active and sustainable transport.")

        # Services - Apartments
        if service_apartments > 0.5:
            report_lines.append(f"- The {self.serviceavailability_building_type[0]}(s) location has a good service availability which means that the building(s) are close to shops, cafes, or supermarkets.")
        else:
            report_lines.append(f"- The {self.serviceavailability_building_type[0]}(s) location has a poor service availability which means that services are far from the chosen building placement.")

        # Services - Offices
        if service_offices > 0.5:
            report_lines.append(f"- The {self.serviceavailability_building_type[1]}(s) has a good service availability which means that the building type is located near lunch spots, resturants or amenities.")
        else:
            report_lines.append(f"- The {self.serviceavailability_building_type[1]}(s) has a poor service availability which means that the building type may lack nearby services.")

        # Solar Analysis
        report_lines.append("\nSolar Potential Analysis")
        report_lines.append("-" * 60)
        if shadow_new_fitness > 0.5:
            report_lines.append(f"- Shadow on buildings fitness is {shadow_new_fitness:.2f}: Minimal overshadowing on buildings.")
        else:
            report_lines.append(f"- Shadow on buildings fitness is {shadow_new_fitness:.2f}: Overshadowing may affect daylight, comfort or sustainable goals.")


        new_roof_area = self.sites_gdf.geometry.area.sum()
        solar_area = new_roof_area - conflict_area_new
        solar_area = max(solar_area, 0.0)  # Prevent negative values
        total_nature_area = self.nature_gdf.geometry.area.sum()
        pros_shadow_new = (conflict_area_new / new_roof_area) * 100 if new_roof_area > 0 else 0
        pros_shadow_nature = (area_nature_conflict / (total_nature_area + 1e-6)) * 100
        report_lines.append(" " * 60)
        report_lines += [
            f"- Total New Roof Area:                        {new_roof_area:.1f} m²",
            f"- Shadowed Area on New Buildings:             {conflict_area_new:.1f} m² ({pros_shadow_new:.1f}%)",
            f"- Shadowed Area on Existing Buildings:        {conflict_area_existing:.1f} m²",
            f"- Area Available for PV:                      {solar_area:.1f} m²",
            f"- Nature Areas in Shadow:                     {area_nature_conflict:.1f} m² ({pros_shadow_nature:.1f}%)",
        ]

        # Shadow reasoning
        report_lines.append("\n Shadow Impact Summary")
        report_lines.append("-" * 60)

        report_lines.append("\nNew buildings casting shadows on existing buildings:")
        for b_name, affected in shadowed_info.items():
            report_lines.append(f"• {b_name} casts shadow on {len(affected)} building(s):")
            for entry in affected:
                report_lines.append(
                    f"   ↳ ID: {entry['id']} | Height: {entry['existing_height']:.1f} m | Overlap: {entry['overlap_area']:.1f} m²"
                )

        report_lines.append("\nExisting buildings casting shadows on new buildings:")
        for new_b_name, source_list in shadow_on_new_buildings_full.items():
            report_lines.append(f"• {new_b_name} receives shadow from {len(source_list)} building(s):")
            for data in source_list:
                report_lines.append(
                    f"   ↳ ID: {data['id']} | Height: {data['existing_height']:.1f} m | Overlap: {data['overlap_area']:.1f} m²"
                )

        # Write to file
        with open(output_path, "w") as file:
            file.write("\n".join(report_lines))

        print(f" Evaluation report saved to: {output_path}")

    def write_fitness_evaluation_report(self, fitness_data, output_file="fitness_per_generationtid.txt"):
        with open(output_file, "w") as file:
            file.write("GAIA Fitness per Generation Report\n")
            file.write("=" * 50 + "\n\n")
            for entry in fitness_data:
                file.write(f"Generation {entry['generation']}:\n")
                file.write(f"  Total Fitness: {entry['total_fitness']:.4f}\n")
                for key in ["GFA", "Shadow Nature", "Walkability", "Cycleability", "Serviceability", "Shadow Buildings"]:
                    file.write(f"  - {key}: {entry[key]:.4f}\n")
                file.write("\n")
        print(f"Fitness report written to {output_file}")


    def run(self):
        self.initialize_population()
        generations_list = []
        fitness_log = []


        #Print site areas (debug information)
        for site_name, area in self.site_areas.items():
            print(f"Site {site_name}: {area} m²")

        for gen in range(self.generations):
            fitnesses = [self.fitness(ind) for ind in self.population]
            elite_idx = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
            elites = [self.population[elite_idx]]

            #elitism locig: carry forward the best individual unchanged
            new_pop = elites.copy()

            #continue until population size is restored
            while len(new_pop) < self.popsize:
                parents = self.select(self.population, fitnesses, 2)
                child = self.crossover(parents[0], parents[1])
                if random.random() < self.mutProb:
                    child = self.mutate(child)
                new_pop.append(child)
            self.population = new_pop

            best_fit = fitnesses[elite_idx]
            print(f" Generation {gen+1} best fitness: {best_fit:.4f}")
            generations_list.append(round(best_fit, 4))

            #for analysing fitness scores for each fitness function
            best_individual = self.population[elite_idx]
            fitness_gfa = self.compute_fitness_gfa(best_individual)
            fitness_shadow_nature, _ = self.compute_shadow_nature_fitness(best_individual)
            fitness_walk = self.compute_walkability_fitness(best_individual)
            fitness_cycle = self.compute_cycleability_fitness(best_individual)
            fitness_services = (
                self.compute_serviceavailability_apartments_fitness(best_individual) + 
                self.compute_serviceavailability_offices_fitness(best_individual)
            ) / 2.0
            fitness_shadow_building, *_ = self.compute_shadow_building_fitness(best_individual)

            #log all fitness data for this generation
            fitness_log.append({
                "generation": gen + 1,
                "total_fitness": best_fit,
                "GFA": fitness_gfa,
                "Shadow Nature": fitness_shadow_nature,
                "Walkability": fitness_walk,
                "Cycleability": fitness_cycle,
                "Serviceability": fitness_services,
                "Shadow Buildings": fitness_shadow_building
            })

        self.write_fitness_evaluation_report(fitness_log)

        #identifying the best individual
        best = self.population[max(range(len(self.population)), key=lambda i: self.fitness(self.population[i]))]
        self.best_individual = best

        #preparing returned values
        urban_result = {}       # maps building name to values 
        site_to_building = {}   # maps site name to building name
        for name, values in best.items():
            urban_result[name] = {
                "max_height": values["height"],
                "site": values["site"]
            }
            site_to_building[values["site"]] = name

        # Compute detailed fitness breakdown for the best individual
        fitness_gfa = self.compute_fitness_gfa(best)
        fitness_shadow_nature,_ = self.compute_shadow_nature_fitness(best)
        fitness_walk = self.compute_walkability_fitness(best)
        fitness_cycle = self.compute_cycleability_fitness(best)
        fitness_services = (self.compute_serviceavailability_apartments_fitness(best) + 
                             self.compute_serviceavailability_offices_fitness(best)) / 2.0
        fitness_shadow_building, shadowed_info, non_shadowed_info, _ , _, _, _= self.compute_shadow_building_fitness(best)

        #Print best individual's configuration and fitness breakdown
        print("\nBest Individual:")
        for name, values in best.items():
            gfa_final = values['gfa'] 
            footprint_area = gfa_final / (values['height'] / self.floor_height) if values['height'] > 0 else 0
            print(f" - {name}: {{'site': '{values['site']}', 'type': '{values['type']}', 'height': {values['height']:.2f}, 'gfa': {values['gfa']}}}, maximal footprint: {footprint_area:.2f} m²")

        print("\nFitness Breakdown:")
        print(f"  • GFA fitness:                   {fitness_gfa:.3f}")
        print(f"  • Shadow Nature Fitness:         {fitness_shadow_nature:.3f}")
        print(f"  • Shadow Buiilding Fitness:      {fitness_shadow_building:.3f}")
        print(f"  • Walkability Fitness:           {fitness_walk:.3f}")
        print(f"  • Cycleability Fitness:          {fitness_cycle:.3f}")
        print(f"  • Serviceability Fitness:        {fitness_services:.3f}")
        
        #Optional: printing shadow-effected buildings in the terminal
        #Note: the shadow-effected buildings are written in the report 
        #for building_name, affected_list in shadowed_info.items():
            #print(f"{building_name} casts shadow on {len(affected_list)} building(s):")
            #for data in affected_list:
                #print(f"   • ID: {data['id']}, height: {data['existing_height']}")

        #for building_name, affected_list in non_shadowed_info.items():
            #print(f"{building_name} will not cast shadow on {len(affected_list)} building(s):")
            #for data in affected_list:
                #print(f"   • ID: {data['id']}, height: {data['existing_height']}")

        # Optional: print fitness trend
        if self.PlotRun:
            print("fitness_setX =", generations_list)  

        total_score = self.fitness(best)
        print(f"\nTotal fitness: {total_score:.3f}")
        if self.output_path != None:
            self.write_evaluation_report(self.output_path, best)

        #plotting the best individual - recomended
        if self.plot:
            self.plot_individual(best)
        return urban_result, site_to_building

