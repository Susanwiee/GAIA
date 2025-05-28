#pitched roof with orientation

import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.geometry
import numpy as np
import math


class Pitched: 
    def __init__(self, shape, model, storey, width, length, thickness, placement_height, top_height, overhang, arm1_thickness, arm2_thickness, context, x_offset, y_offset, angle_deg):
        self.shape = shape
        self.model = model 
        self.storey = storey
        self.width = width 
        self.length = length 
        self.thickness = thickness
        self.placement_height = placement_height
        self.top_height = top_height
        self.overhang = overhang
        self.arm1_thickness = arm1_thickness
        self.arm2_thickness = arm2_thickness
        self.context = context 
        
        self.x_offset = x_offset   
        self.y_offset = y_offset  
        
        self.angle_deg = angle_deg
        angle_rad = math.radians(angle_deg)
        self.cos_a = math.cos(angle_rad)
        self.sin_a = math.sin(angle_rad)

        self.rotation_matrix = np.identity(4)
        self.rotation_matrix[0:3, 0] = [self.cos_a, self.sin_a, 0.0]
        self.rotation_matrix[0:3, 1] = [-self.sin_a, self.cos_a, 0.0]
        self.rotation_matrix[0:3, 3] = [self.x_offset, self.y_offset, self.placement_height]

    def rotate_point(self, x, y):
        rel_x = x - self.x_offset
        rel_y = y - self.y_offset
        x_rot = rel_x * self.cos_a - rel_y * self.sin_a
        y_rot = rel_x * self.sin_a + rel_y * self.cos_a
        return x_rot + self.x_offset, y_rot + self.y_offset


    def AddPitchedRoof(self):
        #creating the roof entity
        pitched_roof = ifcopenshell.api.root.create_entity(self.model, ifc_class="IfcRoof", name="Pitched Roof")
        placement_height = 0
        if self.shape == "Rectangle":
            #define vertices with offsets
            vertices = [[
                (0, - self.overhang, placement_height),  # P0  
                (self.length, -self.overhang, placement_height),  # P1  
                (self.length,  self.width, placement_height), # P2
                (0,  self.width, placement_height),  # P3
                (self.length,  self.width, placement_height + self.top_height), #B2
                (0,  self.width, placement_height + self.top_height), #B3
                
            ]]
            # define faces with gables
            faces = [[
                (0, 1, 2, 3),  #base
                (0, 1, 4, 5),  #pitched roof
                (1, 2, 4),     #side profile
                (2, 3, 5, 4),  #back profile 
                (3, 5, 0)      #side profile
            ]]

        elif self.shape == "L-shape":
            #define vertices for L-shape roof with offsets
            vertices = [[
                (0, - self.overhang, placement_height),          # P0
                ( self.length, - self.overhang, placement_height),# P1
                ( self.length,  self.arm1_thickness, placement_height), # P2
                ( self.arm2_thickness,  self.arm1_thickness, placement_height), # P3
                ( self.arm2_thickness,  self.width, placement_height), # P4
                (0,  self.width, placement_height),                  # P5

                ( self.length,  self.arm1_thickness, placement_height+self.top_height), #B2 
                ( self.arm2_thickness,  self.arm1_thickness, placement_height+self.top_height), #B3
                ( self.arm2_thickness,  self.width, placement_height+self.top_height),#B4 
                (0, self.width, placement_height+self.top_height) #B5 

                 
            ]]
            # faces for L-shape pitched roof (slopes and vertical ends)
            faces = [[
                (0, 1, 2, 3, 4, 5),    # Base
                (0, 1, 6, 7, 8, 9),     #pitched 
                (1, 2, 6),              #side profile
                (2, 3, 7, 6),           #fron profile 1
                (3, 4, 8, 7),           #side profile
                (4, 5, 9, 8),           #front profile 2
                (5, 9, 0)               #front profile 2

                            
            ]]

        else:
            raise ValueError(f"Unsupported shape '{self.shape}' for pitched roof.")

        #add mesh representation
        representation = ifcopenshell.api.geometry.add_mesh_representation(
            self.model, context=self.context, vertices=vertices, faces=faces
        )

        #assign representation to the roof
        roof_shape = self.model.create_entity("IfcProductDefinitionShape", Representations=[representation])
        pitched_roof.Representation = roof_shape

        #create local placement for the pitched roof
        placement_point = self.model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
        placement_axis = self.model.create_entity("IfcAxis2Placement3D", Location=placement_point)
        pitched_roof.ObjectPlacement = self.model.create_entity("IfcLocalPlacement", RelativePlacement=placement_axis)
        ifcopenshell.api.geometry.edit_object_placement(self.model, product=pitched_roof, matrix=self.rotation_matrix)


        #assign the roof to the storey
        ifcopenshell.api.spatial.assign_container(self.model, relating_structure=self.storey, products=[pitched_roof])
        return pitched_roof, vertices[0], faces[0]