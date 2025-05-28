#not in use, but added for comarison
#this code is previously used in the old buildingcomposer for adding pitched roofs to non-oriented buildings

import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.geometry
import numpy as np


class Pitched:
    def __init__(self, shape, model, storey, width, length, thickness, placement_height, top_height, overhang, arm1_thickness, arm2_thickness, context, x_offset, y_offset):
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

    def AddPitchedRoof(self):
        #create the roof entity
        pitched_roof = ifcopenshell.api.root.create_entity(self.model, ifc_class="IfcRoof", name="Pitched Roof")

        if self.shape == "Rectangle":
            #define vertices with offsets
            vertices = [[
                (self.x_offset, self.y_offset - self.overhang, self.placement_height),  # P0  
                (self.x_offset + self.length, self.y_offset-self.overhang, self.placement_height),  # P1  
                (self.x_offset + self.length, self.y_offset + self.width, self.placement_height), # P2
                (self.x_offset, self.y_offset + self.width, self.placement_height),  # P3
                (self.x_offset + self.length, self.y_offset + self.width, self.placement_height + self.top_height), #B2
                (self.x_offset, self.y_offset + self.width, self.placement_height + self.top_height), #B3
                
            ]]
            #define faces with gables
            faces = [[
                (0, 1, 2, 3), #base
                (0, 1, 4, 5), #pitched roof, Solar penl roof prfile (south)
                (1, 2, 4),    #side profile
                (2, 3, 5, 4), #back profile 
                (3, 5, 0)     #side profile
            ]]

        elif self.shape == "L-shape":
            #define vertices for L-shape roof with offsets
            vertices = [[
                (self.x_offset, self.y_offset - self.overhang, self.placement_height),          # P0
                (self.x_offset + self.length, self.y_offset - self.overhang, self.placement_height),# P1
                (self.x_offset + self.length, self.y_offset + self.arm1_thickness, self.placement_height), # P2
                (self.x_offset + self.arm2_thickness, self.y_offset + self.arm1_thickness, self.placement_height), # P3
                (self.x_offset + self.arm2_thickness, self.y_offset + self.width, self.placement_height), # P4
                (self.x_offset, self.y_offset + self.width, self.placement_height),                  # P5

                (self.x_offset + self.length, self.y_offset + self.arm1_thickness, self.placement_height+self.top_height), #B2 (6)
                (self.x_offset + self.arm2_thickness, self.y_offset + self.arm1_thickness, self.placement_height+self.top_height), #B3 (7)
                (self.x_offset + self.arm2_thickness, self.y_offset + self.width, self.placement_height+self.top_height),#B4 (8)
                (self.x_offset, self.y_offset + self.width, self.placement_height+self.top_height) #B5 (9)

                 
            ]]
            #faces for L-shape pitched roof (slopes and vertical ends)
            faces = [[
                (0, 1, 2, 3, 4, 5),  #base
                (0, 1, 6, 7, 8, 9), #pitched roof Solar panel roof profile (south)
                (1, 2, 6),          #side profile
                (2, 3, 7, 6),       #fron profile 1
                (3, 4, 8, 7),       #side profile
                (4, 5, 9, 8),       #front profile 2
                (5, 9, 0)           #front profile 2

                            
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

        #assign the roof to the storey
        ifcopenshell.api.spatial.assign_container(self.model, relating_structure=self.storey, products=[pitched_roof])
        return pitched_roof, vertices[0], faces[0]