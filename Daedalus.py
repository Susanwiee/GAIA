#####Deadalus.py######
#this script is the code behind the Daedlus Genetic Algorithm (GA)
#this GA optimizes the building shape based on aesthetic and enviromental objectives
#returns building parameters


import random
import copy

class DaedalusGA:
    def __init__(self, popsize, generations, mutProb, target_GFA, site_width, site_length, max_height):
        self.floor_height = 2.26
        self.popsize = popsize
        self.generations = generations
        self.mutProb = mutProb
        self.target_GFA = target_GFA
        self.site_width = site_width
        self.site_length = site_length
        self.max_height = max_height
        self.currGeneration = self.initialize_population()
        self.bestIndividual = None
        self.site_area = site_length*site_width


    def initialize_population(self):
        population = []
        for _ in range(self.popsize):  
            #num_buildings = random.randint(5, 20)  
            num_buildings = 1 #modified for the GAIA framework

            individual = {  
                    "number_of_buildings": 0,
                    "buildings": []
                }
            
            x_offset = 0
            y_offset = 0

            for building_idx in range(num_buildings):
                if building_idx == 0:
                    building = self.generate_building(x_offset, y_offset)
                else:
                    building = self.generate_different_building(
                    x_offset, y_offset,  individual["buildings"][-1]
                )

                individual["buildings"].append(building)

                #updating the offsets for the next building
                x_offset = x_offset +  building["length"] + building["distance_x_to_building"]+building["overhang"]
                y_offset = y_offset +  building["width"] + building["distance_y_to_building"]+building["overhang"]

                if x_offset >= (self.site_length) or y_offset >= (self.site_width):
                    break

            individual["number_of_buildings"] = len(individual["buildings"])
            population.append(individual)
        return population
        
    def generate_building(self, x_offset=0, y_offset=0):
        shape = random.choice(["Rectangle", "L-shape"]) 
        max_length = (self.site_length - x_offset )   
        max_width = (self.site_width - y_offset )    
        max_levels = int(self.max_height // self.floor_height)  

        length = random.uniform(self.site_length/1.63**3,  max_length)  
        width = random.uniform(self.site_length/1.63**3,  max_width)   

        arm1_thickness = 0
        arm2_thickness = 0

        if shape == "L-shape":
            #ensure arms have valid, non-zero lengths "L-shape"
            arm1_thickness = random.choice([width/1.618, width/1.618**2, width/1.618**3, width/1.618**4]) #golden ratio: aesthetic variables
            arm2_thickness = random.choice([length/1.618, length/1.618**2, length/1.618**3, length/1.618**4]) #golden ratio: aesthetic variables

        #ensure zero arm-thickness for rectangle shape
        elif shape == "Rectangle":
            arm1_thickness = arm2_thickness = 0        

        number_of_levels = random.randint(1, max_levels)
        height = number_of_levels*self.floor_height
        top_height = random.uniform(1, height/1.618**3) #golden ratio as a constraint for the maximum top height 
        overhang = random.uniform(1, height/1.618**6) #golden ratio as a constraint for the largest overhang

        #for aesthetic symsetry it will always let one of the distances to be zero, but choosen randomly
        if random.choice([False, True]):
            dis_x_building = 0
            dis_y_building = random.uniform(1.5, max(0, self.site_width - y_offset - width - overhang))
            
        else:
            dis_y_building = 0
            dis_x_building = random.uniform(1.5, max(0, self.site_length - x_offset - length - overhang))
        
        if random.random() < 0.4: 
            dis_y_building = random.uniform(1.5, max(0, self.site_width - y_offset - width - overhang))
            dis_x_building = random.uniform(1.5, max(0, self.site_length - x_offset - length - overhang))

    
        ###########OPTIMAL TILT ANGLE ROOF#############
        """
        Constraints for optimal tilt angle for solar panels 
        phi = 44                           #Insert the lattitude for the specific site
        beta = 3.7 + 0.69*phi                  #Find optimal angle for solar panels
        beta_rad = np.radians(beta)
        top_height = width*np.tan(beta_rad)    #Find roof height for optimal angle
        """
        #################################################


        #Using the overhang as a shading technique: 
        ############SHADING WITH OVERHANG################
        """
        theta_sun = 35  
        number_of_levels = random.randint(1, max_levels)
        height = number_of_levels/2.260
        L_overhang = height * math.tan(math.radians(theta_sun))
        overhang = L_overhang
        """
        #################################################

        return {
            "shape": shape,
            "roof_type": random.choice(["Pyramid", "Prism", "Pitched"]),
            "length": length,
            "width": width,
            "top_height": top_height,
            "arm1_thickness": arm1_thickness,
            "arm2_thickness": arm2_thickness,
            "overhang": overhang,
            "num_levels": number_of_levels,
            "window_sill_height": random.uniform(0.1, 1),
            "window_width": random.uniform(0.5, 1.260),
            "window_height": random.uniform(0.5, 1.26),
            "distance_x_to_building": dis_x_building,
            "distance_y_to_building": dis_y_building, 
            "factor_south": random.uniform(0.8, 1),
            "factor_east": random.uniform(0.4, 0.7),
            "factor_west": random.uniform(0.4, 0.7),
            "factor_north": random.uniform(0.0, 0.3)

        }

    def generate_different_building(self, x_offset, y_offset, prev_building):
        new_building = self.generate_building(x_offset, y_offset)
        while new_building["shape"] == prev_building["shape"]:
            new_building["shape"] = random.choice(["Rectangle", "L-shape"]) 
        possible_roof_types = ["Pyramid", "Prism", "Pitched"]
        new_building["roof_type"] = random.choice(possible_roof_types)
        new_building["length"] = max(prev_building["length"]/1.63**2, min(new_building["length"] + random.uniform(-1, 1), self.site_length - x_offset))
        new_building["width"] = max(prev_building["width"]/1.63**2, min(new_building["width"] + random.uniform(-1, 1), self.site_width - y_offset))
        return new_building
    
    
    def calculate_building_ground_area(self, individual):
        total_area = 0
        for building in individual["buildings"]:
            if building["shape"]=="Rectangle":
                area = building["width"]*building["length"]
                total_area = total_area + area 
            else: 
                area = (building["width"]*building["arm2_thickness"] + (building["length"]-building["arm2_thickness"])*(building["arm1_thickness"]))
                total_area = total_area + area
        return total_area


    def calculate_individual_area(self, individual):
        total_area = 0
        for building in individual["buildings"]:
            if building["shape"]=="Rectangle":
                area = building["width"]*building["length"]*building["num_levels"]
                total_area = total_area + area 
            else: 
                area = (building["width"]*building["arm2_thickness"] + (building["length"]-building["arm2_thickness"])*(building["arm1_thickness"]))*building["num_levels"]
                total_area = total_area + area
        return total_area
    
    def calculate_single_building_area(self, building):
        total_area = 0
        if building["shape"]=="Rectangle":
            area = building["width"]*building["length"]*building["num_levels"]
            total_area = total_area + area 
        else: 
            area = (building["width"]*building["arm2_thickness"] + (building["length"]-building["arm2_thickness"])*(building["arm1_thickness"]))*building["num_levels"]
            total_area = total_area + area
        return total_area
            

    def calculate_fitness_green_space(self, individual):
        target_building_area = 0
        total_building_area = 0
        target_building_area = 0.7 * self.site_area  
        total_building_area = self.calculate_building_ground_area(individual)
        distance_from_target = abs(total_building_area - target_building_area)
        max_distance = 0.3 * self.site_area  
        fitness_green_space = max(0, 1 - (distance_from_target / max_distance))
        return fitness_green_space


    def calculate_fitness_similarity(self, individual):
        building_areas = []  
        building_heights = []  

        #collect area and height for each building
        for building in individual["buildings"]:
            #calculate area
            if building["shape"] == "Rectangle":
                area = building["length"] * building["width"]
            elif building["shape"] == "L-shape":
                arm1_area = (building["arm1_thickness"] or 0) * building["width"]
                arm2_area = (building["arm2_thickness"] or 0) * (building["length"] - (building["arm1_thickness"] or 0))
                area = arm1_area + arm2_area
            else:
                area = 0  

            #calculate height
            levels = building["num_levels"] 

            building_areas.append(area)
            building_heights.append(levels)

        #similarity score for area
        area_similarity = self.calculate_similarity(building_areas)

        #milarity score for heights
        height_similarity = self.calculate_similarity(building_heights)


        #combined similarity score
        combined_similarity = (area_similarity + height_similarity) / 2

        #ensure score is between 0 and 1
        return max(0, min(1, combined_similarity))


    def calculate_fitness_WW_ratio(self, individual):
        total_ratio = 0  # accumulate the ratios for all buildings

        for building in individual["buildings"]:
            #calculate total wall surface area
            total_wall_surface = (
                2 * building["length"]  +  # south and north walls
                2 * building["width"]   # west and east walls
            )

            # Simplified window area calculation
            total_window_surface = 0
            window_width = building["window_width"]
            window_height = building["window_height"]
            distance_between_windows = 1.0  # Default or configurable value

            # Calculate windows for each wall orientation
            for orientation, factor in [
                ("south", building["factor_south"]),
                ("north", building["factor_north"]),
                ("east", building["factor_east"]),
                ("west", building["factor_west"]),
            ]:
                # Adjust window dimensions based on orientation factor
                adjusted_width = window_width * factor
                adjusted_height = window_height * factor
                wall_length = building["length"] if orientation in ["south", "north"] else building["width"]

                # Calculate number of windows along the wall
                n_windows = int(wall_length // (adjusted_width + distance_between_windows))
                total_window_surface += n_windows * adjusted_width * adjusted_height

            # Add ratio of windows to walls for the building
            if total_wall_surface > 0:  # Avoid division by zero
                total_ratio += total_window_surface / total_wall_surface

        # Calculate average ratio across all buildings
        final_ratio = total_ratio / len(individual["buildings"]) if individual["buildings"] else 0
        return final_ratio

        
    def calculate_fitness_PV_ratio(self, individual): 
        total_ratio_PV = 0  
        for building in individual["buildings"]:
            
            if building["roof_type"] == "Prism" or  building["roof_type"] == "Pyramid":
                total_ratio_PV=0

            elif building["roof_type"] == "Pitched":
                PV_length = 1.0
                PV_width = 2.0
                PV_width_space = 0.1
                overhang = building.get("overhang", 0)  
                width = building["width"]
                length = building["length"]
                top_height = building["top_height"]

                if building["shape"] == "Rectangle":
                    # Calculate roof dimensions
                    length_roof = length
                    width_roof = (top_height**2 + width**2)**0.5 + overhang
                    area_roof = length_roof * width_roof
                    # Calculate PV panel placement
                    number_of_PV_width = int(width_roof // (PV_width+PV_width_space)) 
                    number_of_PV_length = int(length_roof// PV_length) 
                    number_of_PV = number_of_PV_width * number_of_PV_length
                    area_PV = number_of_PV * PV_width * PV_length
                    total_ratio_PV += area_PV / area_roof

                if building["shape"] == "L-shape":
                    #seperates in two rectangles 
                    arm1 = building["arm1_thickness"]
                    arm2 = building["arm2_thickness"]

                    #first rectangle langthxarm1
                    length_roof_1 = length - arm2
                    width_roof_1 = (top_height**2 + arm1**2)**0.5 + overhang
                    area_roof_1 = length_roof_1 * width_roof_1
                    number_of_PV_length_1 = int(length_roof_1//PV_length)
                    number_of_PV_width_1 = int(width_roof_1 // (PV_width+PV_width_space))
                    number_of_PV_1 = number_of_PV_length_1*number_of_PV_width_1
                    area_PV_1 = number_of_PV_1 * PV_width * PV_length
                    
                    #seccond rectangle
                    length_roof_2 = arm2
                    width_roof_2 = (top_height**2 + width**2)**0.5 + overhang
                    area_roof_2 = length_roof_2 * width_roof_2
                    number_of_PV_length_2 = int(length_roof_2//PV_length)
                    number_of_PV_width_2 = int(width_roof_2 // (PV_width+PV_width_space))
                    number_of_PV_2 = number_of_PV_length_2*number_of_PV_width_2
                    area_PV_2 = number_of_PV_2 * PV_width * PV_length

                    total_area_roof_L = area_roof_1 + area_roof_2
                    total_area_PV_L = area_PV_1 + area_PV_2
                    total_ratio_PV += total_area_PV_L / total_area_roof_L

            else:
                total_ratio_PV = 0  
        valid_building_count = sum(1 for building in individual["buildings"] if building["roof_type"] == "Pitched")
        return total_ratio_PV / valid_building_count if valid_building_count > 0 else 0



    def calculate_similarity(self, values):
        std_dev_value = 0
        if len(values) <= 1:
            return 0.5  #some score if there is only one building

        mean_value = sum(values) / len(values)
        for v in values: 
            if (v-mean_value) > 0: 
                std_dev_value = std_dev_value + 1/(abs(v-mean_value))
            elif (v-mean_value) == 0: 
                std_dev_value = std_dev_value

        return max(0, min(1, std_dev_value))



    def calculate_fitness_number_buildings(self, site_area, individual):
        # Define thresholds for ideal numbers (adjust as needed)
        ideal_based_on_area = 0

        if site_area < 100: 
            ideal_based_on_area = 1
        elif 200 > site_area >= 100: 
            ideal_based_on_area = 2
        elif 300 > site_area >= 200: 
            ideal_based_on_area = 3
        elif 500 > site_area >= 300: 
            ideal_based_on_area = 4
        elif site_area >= 500: 
            ideal_based_on_area = 5

        # Calculate fitness
        fitness_number_buildings = len(individual["buildings"]) / ideal_based_on_area

        #If number of buildings > ideal number
        fitness_number_buildings = min(fitness_number_buildings, 1)

        return fitness_number_buildings
    

    def calculate_fitness_compactness(self, individual): 
        # Rectangle
        compactness = 0
        for building in individual["buildings"]:
            width = building["width"]
            length = building["length"]
            arm1 = building["arm1_thickness"]
            arm2 = building["arm2_thickness"]
            height = building["num_levels"]*self.floor_height

            if building["shape"] == "Rectangle":
                volume = width * length * height
                rect_surface_area = 2 * (width * height + length * height + width * length)
                a = volume ** (1 / 3)
                cube_surface_area = 6 * (a ** 2)
                compactness += cube_surface_area / rect_surface_area
            
            # L-shape
            else:
                volume = (length * arm1 + (width - arm1) * arm2) * height
                L_surface_area = (
                    2 * (length * height + width * height) + ((arm1 * length) + (arm2 * (width - arm1)) * 2)
                )
                a = volume ** (1 / 3)
                cube_surface_area = 6 * (a ** 2)
                compactness += cube_surface_area / L_surface_area
            
            total_compactness = compactness/len(individual["buildings"]) if len(individual["buildings"]) > 0 else 0

        return min(total_compactness, 1.0) 

    
    def calculate_fitness_GFA(self, target_GFA, individual):
        total_area_individual = self.calculate_individual_area(individual)
        
        if total_area_individual > target_GFA:
            fitness = target_GFA / total_area_individual  
        else:
            fitness = total_area_individual / target_GFA  
        return fitness

        
    def fitness(self, individual):
        fintess = 0
        fitness_green_space = 0
        fitness_number_buildings = 0
        fitness_compactness = 0
        ratio_PV = 0
        site_area = self.site_length*self.site_width

        #in use in the GAIA framework
        ########Fitness TARGET GFA#########
        fitness_target_GFA = self.calculate_fitness_GFA(self.target_GFA, individual)

        ########Fitness PV-ROOF RATIO###### 
        ratio_PV = self.calculate_fitness_PV_ratio(individual)
        
        #######Fitness WINDOW WALL RATIO#### 
        ratio_WW = self.calculate_fitness_WW_ratio(individual)/0.36

        ######Fitness COMPACTNESS#######
        fitness_compactness = self.calculate_fitness_compactness(individual)


        #Not in use in the GAIA framework 
        ########Fitness NUMBER OG BUILDINGS###
        #gir fitness basert på et gyldig antall bygg
        fitness_number_buildings = self.calculate_fitness_number_buildings(site_area, individual)
        ##########Fitness GREEN SPACE#######
        fitness_green_space = self.calculate_fitness_green_space(individual)
        #########Fitness SIMILARITY#############
        fitness_similarity = self.calculate_fitness_similarity(individual)


        #####TOTAL FITNESS################
        fintess = fitness_compactness*(0.2) +  ratio_PV*(0.2) + ratio_WW*(0.2) + fitness_target_GFA*(0.4)  


        for building in individual["buildings"]:
            if building["shape"]=="L-shape" and (building["arm1_thickness"] + building["arm1_thickness"]<3):
                fintess = 0
 
        buildings_lengths=[]
        buildings_widths = []
        for building in individual["buildings"]:
            length = building["length"]
            width = building["width"]
            distance_x = building["distance_x_to_building"]
            distance_y = building["distance_y_to_building"]
            buildings_lengths.append(length)
            buildings_lengths.append(distance_x)

            buildings_widths.append(width)
            buildings_widths.append(distance_y)

        if sum(buildings_lengths) > self.site_length or sum(buildings_widths)>self.site_width: 
            fintess = 0
             
        return fintess,  fitness_green_space, fitness_number_buildings, fitness_compactness, fitness_similarity, ratio_PV, ratio_WW, fitness_target_GFA

    #not in use in the GAIA framework 
    #def add_buildings(self, individual):
        total_area = self.calculate_individual_area(individual)
        x_offset = sum(building["length"] + building["distance_x_to_building"] + building["overhang"]
                    for building in individual["buildings"])
        y_offset = sum(building["width"] + building["distance_y_to_building"] + building["overhang"]
                    for building in individual["buildings"])
        
        max_attempts = 10  
        attempts = 0

        while total_area < 0.6 * self.site_area and attempts < max_attempts:
            building = self.generate_building(x_offset, y_offset)
            
            if not self.is_within_bounds(building, x_offset, y_offset):
                attempts += 1
                continue
            
            if self.is_overlapping(building, individual["buildings"]):
                attempts += 1
                continue

            individual["buildings"].append(building)
            individual["number_of_buildings"] += 1
            total_area += building["length"] * building["width"]

            x_offset += building["length"] + building["distance_x_to_building"] + building["overhang"]
            y_offset += building["width"] + building["distance_y_to_building"] + building["overhang"]

        return individual


        
    def mutation(self, individual):
        """
        Apply mutation to an individual with a given probability, modifying only specific attributes.
        """
        for building in individual["buildings"]:
            # Calculate dynamic bounds based on building's position

            # Mutate specific properties only
            #the number of levels, wil wither: 1) decrease by 1, 2) stay unchanges, 3) increase by 1
            if random.random() < self.mutProb:
                building["num_levels"] += random.randint(-1, 1)
                building["num_levels"] = max(1, min(building["num_levels"], int(self.max_height / 2.3)))

            if random.random() < self.mutProb:
            #decrease by -0.1, stay unchanged or increase by 0.1 
                building["window_sill_height"] += random.uniform(-0.1, 0.1)
                building["window_sill_height"] = max(0.1, min(building["window_sill_height"],0.3))

            if random.random() < self.mutProb:
            #decrease by -0.1, stay unchanged or increase by 0.1 
                building["window_height"] += random.uniform(-0.1, 0.1)
                building["window_height"] = max(0.1, min(building["window_sill_height"],2))

            if random.random() < self.mutProb:
                building["window_width"] += random.uniform(-0.1, 0.1)
                building["window_width"] = max(0.5, min(building["window_width"], 2))


            if random.random() < self.mutProb:
                building["top_height"] += random.uniform(-1, 1)
                building["top_height"] = max(1, min(building["top_height"], 2))



        return individual
    

    def is_within_bounds(self, building, x_offset, y_offset):
        return (
            x_offset + building["length"] + building["overhang"] <= self.site_length and
            y_offset + building["width"] + building["overhang"] <= self.site_width
        )


    def crossover(self, parent1, parent2):
        
        #Performs 2-point crossover on two parents to generate two offspring, modifying only specific attributes.
        
        #get the building lists of the parents
        buildings1 = parent1["buildings"]
        buildings2 = parent2["buildings"]

        #determine crossover points
        if len(buildings1) > 1 and len(buildings2) > 1:  
            point1 = random.randint(0, len(buildings1) - 1)
            point2 = random.randint(point1, len(buildings1) - 1)
        else:
            return copy.deepcopy(parent1), copy.deepcopy(parent2)

        offspring1_buildings = buildings1[:point1] + buildings2[point1:point2] + buildings1[point2:]
        offspring2_buildings = buildings2[:point1] + buildings1[point1:point2] + buildings2[point2:]

        offspring1 = {
            "number_of_buildings": len(offspring1_buildings),
            "buildings": offspring1_buildings
        }
        offspring2 = {
            "number_of_buildings": len(offspring2_buildings),
            "buildings": offspring2_buildings
        }

        return offspring1, offspring2

    def selection(self, currGeneration, fitnessResults):
        #Selects the two parents with the highest fitness scores.

        #currGeneration: List of individuals in the current population.
        #fitnessResults: List of fitness values corresponding to each individual.
        #Returns: a tuple of two selected individuals (parents).
    
        paired_population = list(zip(currGeneration, fitnessResults))
        
        paired_population.sort(key=lambda x: (x[1]), reverse=True)

        #selecting the top two individuals
        parent1 = paired_population[0][0]
        parent2 = paired_population[1][0]

        return parent1, parent2



    def print_building_parameters(self, building, building_number):

        print(f"\n--- Building {building_number} Parameters ---")
        GFA = self.calculate_single_building_area(building)
        print("GFA: ", GFA)
        print(f"Shape: {building['shape']}")
        print(f"Roof Type: {building['roof_type']}")
        print(f"Length: {building['length']} meters")
        print(f"Width: {building['width']} meters")
        print(f"Arm1 Thickness: {building['arm1_thickness']}")
        print(f"Arm2 Thickness: {building['arm2_thickness']}")
        print(f"Overhang: {building['overhang']}")
        print(f"top height: {building["top_height"]}")
        print(f"Number of Levels: {building['num_levels']}")
        #print(f"number of windows length: {num_windows_wall_length:.2f}")
        print(f"Window Sill Height: {building['window_sill_height']}")
        print(f"Window Width: {building['window_width']}")
        print(f"Window Height: {building['window_height']}")
        print(f"Distance X to Building: {building['distance_x_to_building']}")
        print(f"Distance Y to Building: {building['distance_y_to_building']}")
        print(f"Scaling Factors:")

        #print(f"  - South: {building['factor_south']}")
        #print(f"  - North: {building['factor_north']}")
        #print(f"  - West: {building['factor_west']}")
        #print(f"  - East: {building['factor_east']}")

    def run(self):
        overall_best_individual = None
        overall_best_fitness = float('-inf')  

        for generation in range(self.generations):
            
            #optinal: 
            #print(f"Generation {generation + 1}/{self.generations}")
            
            #calculate fitness for each individual
            fitness_results = [self.fitness(individual) for individual in self.currGeneration]

            #select parents based on fitness
            new_population = []
            while len(new_population) < self.popsize:
                parent1, parent2 = self.selection(self.currGeneration, fitness_results)
                offspring1, offspring2 = self.crossover(parent1, parent2)
                new_population.append(self.mutation(offspring1))
                new_population.append(self.mutation(offspring2))

            #update the current generation
            self.currGeneration = new_population[:self.popsize]

            #identify the best individual in this generation
            generation_best = max(self.currGeneration, key=lambda ind: self.fitness(ind)[0]) 
            generation_best_fitness = self.fitness(generation_best)

            #update overall best individual if necessary
            if generation_best_fitness[0] > overall_best_fitness:
                overall_best_individual = generation_best
                overall_best_fitness = generation_best_fitness[0]  
                #best_fitness_green_space = generation_best_fitness[1]   #1 not in use in the GAIA framework 
                #fitness_number_buildings = generation_best_fitness[2]   #2 not in use in the GAIA framework 
                best_fitness_compactness = generation_best_fitness[3]   #3
                #best_fitness_similarity = generation_best_fitness[4]    #4 not in use in the GAIA framework
                best_fitness_ratio_PV = generation_best_fitness[5]      #5
                best_fitness_ratio_WW = generation_best_fitness[6]       #6
                best_fitness_target_GFA = generation_best_fitness[7]     #7

        #set the best overall individual
        self.bestIndividual = overall_best_individual

        for idx, building in enumerate(overall_best_individual["buildings"]):
            building_number = idx + 1  
            self.print_building_parameters(building, building_number)
        
        
        #print results
        #print(f"Fitness Green Space: {best_fitness_green_space:.3f}") #1  not in use in the GAIA framework
        #print(f"Fitness Number of buildings: {fitness_number_buildings:.3f}") #2  not in use in the GAIA framework
        print(f"Fitness compactness: {best_fitness_compactness:.3f}") #3
        #print(f"Fitness Similarity: {best_fitness_similarity:.3f}") #4 not in use in the GAIA framework
        print(f"Fitness ratio PV: {best_fitness_ratio_PV:.3f}") #5
        print(f"Fitness ratio WW: {best_fitness_ratio_WW:.3f}") #6
        print(f"Fitness GFA: {best_fitness_target_GFA:.3f}") #7
        print(f"Final Fitness Score of Best Individual: {overall_best_fitness:.4f}")
        return self.bestIndividual

