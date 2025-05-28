#not in use, but added for comarison
#this code is previously used in the old buildingcomposer for adding pyramid roofs to non-oriented buildings

import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.geometry
import numpy as np


class Pyramid: 
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

    def AddPyramidRoof(self):

        #create a pyramid roof entity
        pyramid_roof = ifcopenshell.api.root.create_entity(self.model, ifc_class="IfcRoof", name="Pyramid Roof")

        if self.shape == "L-shape":
            #define vertices (roof base and apex) with offsets
            vertices = [[
                (self.x_offset - self.overhang, self.y_offset - self.overhang, self.placement_height),                                # P0
                (self.x_offset + self.length + self.overhang, self.y_offset - self.overhang, self.placement_height),                      # P1
                (self.x_offset + self.length + self.overhang, self.y_offset + self.arm1_thickness + self.overhang, self.placement_height),     # P2
                (self.x_offset + self.arm2_thickness + self.overhang, self.y_offset + self.arm1_thickness + self.overhang, self.placement_height), # P3
                (self.x_offset + self.arm2_thickness + self.overhang, self.y_offset + self.width + self.overhang, self.placement_height),      # P4
                (self.x_offset - self.overhang, self.y_offset + self.width + self.overhang, self.placement_height),                       # P5
                (self.x_offset + self.arm2_thickness / 2, self.y_offset + self.arm1_thickness / 2, self.placement_height + self.top_height), # A1 = 6
                (self.x_offset + self.arm2_thickness / 2, self.y_offset + self.width - self.top_height, self.placement_height + self.top_height), # A2 = 7
                (self.x_offset + self.length - self.top_height, self.y_offset + self.arm1_thickness / 2, self.placement_height + self.top_height) # A3 = 8
            ]]
            faces = [[
                (0, 1, 2, 3, 4, 5),   #base
                (0, 6, 8, 1),         #length face, Solar Panel roof profile (south)
                (1, 8, 2),            #right triangle on arm 1
                (2, 8, 6, 3),         #inner length face
                (3, 6, 7, 4),         #inner width face
                (4, 7, 5),            #upper triangle on arm 2
                (5, 7, 6, 0)          #width face
            ]]

        elif self.shape == "Rectangle":
            adjusted_length = self.length 
            adjusted_width = self.width 
            vertices = [[
                (self.x_offset - self.overhang, self.y_offset - self.overhang, self.placement_height),                        # Base corner 1
                (self.x_offset - self.overhang, self.y_offset + adjusted_width + self.overhang, self.placement_height),       # Base corner 2
                (self.x_offset + adjusted_length + self.overhang, self.y_offset + adjusted_width + self.overhang, self.placement_height), # Base corner 3
                (self.x_offset + adjusted_length + self.overhang, self.y_offset - self.overhang, self.placement_height),      # Base corner 4
                (self.x_offset + adjusted_length / 2, self.y_offset + adjusted_width / 2, self.placement_height + self.top_height) # Apex
            ]]
            faces = [[
                (0, 1, 2, 3),   #base of the pyramid
                (0, 4, 1),      #left triangle 
                (1, 4, 2),      #front triangle, Solar panel roof profle (south) 
                (2, 4, 3),      #right triangle
                (3, 4, 0)       #back triangle
            ]]

        #add mesh representation
        representation = ifcopenshell.api.geometry.add_mesh_representation(
            self.model, context=self.context, vertices=vertices, faces=faces
        )
        

        #assign representation to the pyramid roof
        roof_shape = self.model.create_entity("IfcProductDefinitionShape", Representations=[representation])
        pyramid_roof.Representation = roof_shape

        #create local placement for the pyramid roof
        placement_point = self.model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
        placement_axis = self.model.create_entity("IfcAxis2Placement3D", Location=placement_point)
        pyramid_roof.ObjectPlacement = self.model.create_entity("IfcLocalPlacement", RelativePlacement=placement_axis)

        #assign the roof to the storey
        ifcopenshell.api.spatial.assign_container(self.model, relating_structure=self.storey, products=[pyramid_roof])
        return pyramid_roof, vertices[0], faces[0]