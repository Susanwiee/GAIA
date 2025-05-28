#not in use, but added for comarison
#this code is previously used in the old buildingcomposer for adding prism roofs to non-oriented buildings


import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.geometry


class Prism: 
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

    def AddPrismRoof(self):
        prism_roof = ifcopenshell.api.root.create_entity(self.model, ifc_class="IfcRoof", name="Prism Roof")

        if self.shape == "Rectangle":
            vertices = [[
                (self.x_offset - self.overhang, self.y_offset - self.overhang, self.placement_height),                        # 0
                (self.x_offset - self.overhang, self.y_offset + self.width + self.overhang, self.placement_height),           # 1
                (self.x_offset + self.length + self.overhang, self.y_offset + self.width + self.overhang, self.placement_height), # 2
                (self.x_offset + self.length + self.overhang, self.y_offset - self.overhang, self.placement_height),           # 3
                (self.x_offset - self.overhang, self.y_offset + self.width / 2, self.placement_height + self.top_height),      # 4
                (self.x_offset + self.length + self.overhang, self.y_offset + self.width / 2, self.placement_height + self.top_height) # 5
            ]]
            faces = [[
                (0, 1, 2, 3),  # base
                (5, 3, 0, 4),  # side face, solar panel roof profile (south) 
                (4, 1, 2, 5),  # opposite side face
                (2, 3, 5),     # right triangle
                (0, 1, 4)      # left triangle
            ]]

        elif self.shape == "L-shape":
            vertices = [[
                (self.x_offset - self.overhang, self.y_offset - self.overhang, self.placement_height),                          # P0
                (self.x_offset + self.length + self.overhang, self.y_offset - self.overhang, self.placement_height),            # P1
                (self.x_offset + self.length + self.overhang, self.y_offset + self.arm1_thickness + self.overhang, self.placement_height), # P2
                (self.x_offset + self.arm2_thickness + self.overhang, self.y_offset + self.arm1_thickness + self.overhang, self.placement_height), # P3
                (self.x_offset + self.arm2_thickness + self.overhang, self.y_offset + self.width + self.overhang, self.placement_height), # P4
                (self.x_offset - self.overhang, self.y_offset + self.width + self.overhang, self.placement_height),             # P5
                (self.x_offset + self.arm2_thickness / 2, self.y_offset + self.arm1_thickness / 2, self.placement_height + self.top_height), # A1 = 6
                (self.x_offset + self.arm2_thickness / 2, self.y_offset + self.width + self.overhang, self.placement_height + self.top_height), # A2 = 7
                (self.x_offset + self.length + self.overhang, self.y_offset + self.arm1_thickness / 2, self.placement_height + self.top_height) # A3 = 8
            ]]
            faces = [[
                (0, 1, 2, 3, 4, 5),   # base
                (0, 6, 8, 1),         # length face Solar panel roof profile (south)
                (1, 8, 2),            # right triangle on arm 1
                (2, 8, 6, 3),         # inner length face
                (3, 6, 7, 4),         # inner width face
                (4, 7, 5),            # upper triangle on arm 2
                (5, 7, 6, 0)          # width face
            ]]

        #add mesh representation
        representation = ifcopenshell.api.geometry.add_mesh_representation(self.model, context=self.context, vertices=vertices, faces=faces)

        #assign representation to the roof
        roof_shape = self.model.create_entity("IfcProductDefinitionShape", Representations=[representation])
        prism_roof.Representation = roof_shape

        #create local placement for the roof
        placement_point = self.model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
        placement_axis = self.model.create_entity("IfcAxis2Placement3D", Location=placement_point)
        prism_roof.ObjectPlacement = self.model.create_entity("IfcLocalPlacement", RelativePlacement=placement_axis)

        #assign the roof to the storey
        ifcopenshell.api.spatial.assign_container(self.model, relating_structure=self.storey, products=[prism_roof])
        return prism_roof, vertices[0], faces[0]