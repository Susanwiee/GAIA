#rectangular windows for oriented buildings generated in the BuildingComposer 

import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.geometry
import numpy as np
import math


import numpy as np
import ifcopenshell


class Rectangular:
    def __init__(self, shape, model, storey, wall, wall_length, wall_width, wall_length_windows, wall_orientation,
                 level_height, window_width, window_height, window_sill_height, context, thickness,
                 distance_between_windows, arm_1, arm_2, x_offset, y_offset, angle_deg,
                 factor_west, factor_east, factor_south, factor_north): 
        self.shape = shape
        self.model = model
        self.storey = storey
        self.wall = wall
        self.wall_length = wall_length
        self.wall_width = wall_width
        self.wall_length_windows = wall_length_windows
        self.wall_orientation = wall_orientation
        self.level_height = level_height
        self.window_width = window_width
        self.window_height = window_height
        self.window_sill_height = window_sill_height
        self.context = context
        self.thickness = thickness
        self.distance_between_windows = distance_between_windows
        self.arm_1 = arm_1
        self.arm_2 = arm_2
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.angle_deg = angle_deg
        angle_rad = math.radians(angle_deg)
        self.cos_a = math.cos(angle_rad)
        self.sin_a = math.sin(angle_rad)


    def rotate_point(self, x, y):
        rel_x = x - self.x_offset
        rel_y = y - self.y_offset
        x_rot = rel_x * self.cos_a - rel_y * self.sin_a
        y_rot = rel_x * self.sin_a + rel_y * self.cos_a
        return x_rot + self.x_offset, y_rot + self.y_offset

    def add_rectangular_windows(self):
        if self.shape == "Rectangle":
            #determine window size based on wall orientation and factors
            if self.wall_orientation == 0:  #south-facing wall
                current_window_width = self.window_width 
                current_window_height = self.window_height
            elif self.wall_orientation == 1:  #east-facing wall
                current_window_width = self.window_width 
                current_window_height = self.window_height
            elif self.wall_orientation == 2:  #north-facing wall
                current_window_width = self.window_width 
                current_window_height = self.window_height
            elif self.wall_orientation == 3:  #west-facing wall
                current_window_width = self.window_width 
                current_window_height = self.window_height
            else:
                current_window_width = self.window_width
                current_window_height = self.window_height  

            #calculate number of windows rectangle
            n_windows = int(self.wall_length_windows // (current_window_width + self.distance_between_windows))
            leftover_space = self.wall_length_windows - (n_windows * current_window_width + (n_windows - 1) * self.distance_between_windows)
            start_offset = leftover_space / 2  
            
            for i in range(n_windows):
                offset = start_offset + i * (current_window_width + self.distance_between_windows)
                if self.wall_orientation == 0:  # south wall
                    x_local = self.x_offset + offset
                    y_local = self.y_offset
                elif self.wall_orientation == 1:  # east wall
                    x_local = self.x_offset + self.wall_length
                    y_local = self.y_offset + offset
                elif self.wall_orientation == 2:  # north wall
                    x_local = self.x_offset + self.wall_length - offset
                    y_local = self.y_offset + self.wall_width
                elif self.wall_orientation == 3:  # west wall
                    x_local = self.x_offset
                    y_local = self.y_offset + self.wall_width - offset

                #rotating local position by the building's angle to get global coords
                x_global, y_global = self.rotate_point(x_local, y_local)

                #initializing placement matrix and set rotated translation
                window_matrix = np.identity(4)
                window_matrix[0:3, 3] = [x_global, y_global, self.level_height + self.window_sill_height]

                #computing the wall direction unit vector and rotate it for orientation:
                if self.wall_orientation == 0:   #wall along +X 
                    dir_x, dir_y = 1, 0
                elif self.wall_orientation == 1:  #wall along +Y 
                    dir_x, dir_y = 0, 1
                elif self.wall_orientation == 2:  #wall along -X 
                    dir_x, dir_y = -1, 0
                elif self.wall_orientation == 3: #wall along -Y
                    dir_x, dir_y = 0, -1

                #rotate the direction vector to align with building orientation
                global_dir_x = dir_x * self.cos_a - dir_y * self.sin_a
                global_dir_y = dir_x * self.sin_a + dir_y * self.cos_a

                #set local X-axis along the rotated wall direction, and Y-axis perpendicular to it
                window_matrix[0:3, 0] = [global_dir_x, global_dir_y, 0]      
                window_matrix[0:3, 1] = [-global_dir_y, global_dir_x, 0]     

                #create window and apply placement
                window = ifcopenshell.api.root.create_entity(self.model, ifc_class="IfcWindow", name=f"Window {self.wall_orientation+1}-{i+1}")
                ifcopenshell.api.geometry.edit_object_placement(self.model, product=window, matrix=window_matrix)

                #add geometry for the window
                window_representation = ifcopenshell.api.geometry.add_wall_representation(
                    self.model, context=self.context, length=current_window_width, height=current_window_height, thickness=self.thickness
                )
                ifcopenshell.api.geometry.assign_representation(self.model, product=window, representation=window_representation)
                ifcopenshell.api.spatial.assign_container(self.model, relating_structure=self.storey, products=[window])

        elif self.shape == "L-shape":
            current_window_width = self.window_width
            current_window_height = self.window_height

            n_windows = int(self.wall_length_windows // (current_window_width + self.distance_between_windows))
            total_windows_width = n_windows * current_window_width
            total_gaps_width = (n_windows - 1) * self.distance_between_windows
            total_occupied_width = total_windows_width + total_gaps_width
            leftover_space = self.wall_length_windows - total_occupied_width
            start_offset = leftover_space / 2

            for i in range(n_windows):
                offset = start_offset + i * (current_window_width + self.distance_between_windows)

                if self.wall_orientation == 0:  #south-facing
                    x_local = self.x_offset + offset
                    y_local = self.y_offset
                    dir_x, dir_y = 1, 0
                elif self.wall_orientation == 1:  #east arm 1
                    x_local = self.x_offset + self.wall_length
                    y_local = self.y_offset + offset
                    dir_x, dir_y = 0, 1
                elif self.wall_orientation == 2:  #north inner length
                    x_local = self.x_offset + self.wall_length - offset
                    y_local = self.y_offset + self.arm_1
                    dir_x, dir_y = -1, 0
                elif self.wall_orientation == 3:  #east inner width
                    x_local = self.x_offset + self.arm_2 - self.thickness
                    y_local = self.y_offset + self.wall_width - offset
                    dir_x, dir_y = 0, -1
                elif self.wall_orientation == 4:  #north arm 2
                    x_local = self.x_offset + self.arm_2 - offset
                    y_local = self.y_offset + self.wall_width
                    dir_x, dir_y = -1, 0
                elif self.wall_orientation == 5:  #west width
                    x_local = self.x_offset
                    y_local = self.y_offset + self.wall_width - offset
                    dir_x, dir_y = 0, -1

                #rotating the position
                x_global, y_global = self.rotate_point(x_local, y_local)

                #creating window placement matrix
                window_matrix = np.identity(4)
                window_matrix[0:3, 3] = [x_global, y_global, self.level_height + self.window_sill_height]

                #rotating wall local direction vector
                global_dir_x = dir_x * self.cos_a - dir_y * self.sin_a
                global_dir_y = dir_x * self.sin_a + dir_y * self.cos_a

                window_matrix[0:3, 0] = [global_dir_x, global_dir_y, 0]   
                window_matrix[0:3, 1] = [-global_dir_y, global_dir_x, 0]  

                #creating window
                window = ifcopenshell.api.root.create_entity(self.model, ifc_class="IfcWindow", name=f"Window {self.wall_orientation + 1}-{i+1}")
                ifcopenshell.api.geometry.edit_object_placement(self.model, product=window, matrix=window_matrix)

                window_representation = ifcopenshell.api.geometry.add_wall_representation(
                    self.model, context=self.context, length=current_window_width, height=current_window_height, thickness=self.thickness
                )
                ifcopenshell.api.geometry.assign_representation(self.model, product=window, representation=window_representation)
                ifcopenshell.api.spatial.assign_container(self.model, relating_structure=self.storey, products=[window])



