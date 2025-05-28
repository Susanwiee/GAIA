#pyramid roof with orientation

import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.geometry
import numpy as np
import math



class Pyramid: 
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


    def AddPyramidRoof(self):

        #create a pyramid roof entity
        pyramid_roof = ifcopenshell.api.root.create_entity(self.model, ifc_class="IfcRoof", name="Pyramid Roof")
        placement_height = 0
        if self.shape == "L-shape":
            
            vertices = [[
                (- self.overhang, - self.overhang, placement_height),                                # P0
                ( self.length + self.overhang,  - self.overhang, placement_height),                      # P1
                ( self.length + self.overhang, self.arm1_thickness + self.overhang, placement_height),     # P2
                (self.arm2_thickness + self.overhang,  self.arm1_thickness + self.overhang, placement_height), # P3
                ( self.arm2_thickness + self.overhang,  self.width + self.overhang, placement_height),      # P4
                (- self.overhang, self.width + self.overhang, placement_height),                       # P5
                ( self.arm2_thickness / 2, self.arm1_thickness / 2, placement_height + self.top_height), # A1 = 6
                ( self.arm2_thickness / 2,  self.width - self.top_height, placement_height + self.top_height), # A2 = 7
                (self.length - self.top_height, self.arm1_thickness / 2, placement_height + self.top_height) # A3 = 8
            ]]
            faces = [[
                (0, 1, 2, 3, 4, 5),   # base
                (0, 6, 8, 1),         # length face, Solar Panel roof profile (south)
                (1, 8, 2),            # right triangle on arm 1
                (2, 8, 6, 3),         # inner length face
                (3, 6, 7, 4),         # inner width face
                (4, 7, 5),            # upper triangle on arm 2
                (5, 7, 6, 0)          # width face
            ]]



        elif self.shape == "Rectangle":
            adjusted_length = self.length 
            adjusted_width = self.width 
            vertices = [[
                (- self.overhang,  - self.overhang, placement_height),                        # base corner 1
                (- self.overhang,  + adjusted_width + self.overhang, placement_height),       # base corner 2
                ( adjusted_length + self.overhang,  adjusted_width + self.overhang, placement_height), # base corner 3
                ( adjusted_length + self.overhang,  - self.overhang, placement_height),      # base corner 4
                ( adjusted_length / 2,  adjusted_width / 2, placement_height + self.top_height) # Apex
            ]]
            faces = [[
                (0, 1, 2, 3),   #base of the pyramid
                (0, 4, 1),      #left triangle 
                (1, 4, 2),      #front triangle, Solar panel roof profle (south) 
                (2, 4, 3),      #right triangle
                (3, 4, 0)       #back triangle
            ]]


        #add mesh representation with the rotated vertices
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
        ifcopenshell.api.geometry.edit_object_placement(self.model, product=pyramid_roof, matrix=self.rotation_matrix)

        #assign the roof to the storey
        ifcopenshell.api.spatial.assign_container(self.model, relating_structure=self.storey, products=[pyramid_roof])
        return pyramid_roof, vertices[0], faces[0]