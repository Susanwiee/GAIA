## SquareSiteOriented.py ##
#This script is used in the BuildingComposer to generate square sites aligned to building orientations.

import math
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.geometry


class SquareSiteOriented:
    def __init__(self, model, context, site, site_width, site_length, name, orientation_deg=0, position=(0.0, 0.0)):
        self.model = model
        self.context = context
        self.site = site
        self.site_width = site_width
        self.site_length = site_length
        self.name = name 
        self.orientation_deg = orientation_deg
        self.position = position  

    def AddSquareSite(self):
        floor_thickness = -0.1  #slight negative Z to stay under floors

        #defining the local square before rotation
        local_vertices = [
            (0, 0, floor_thickness),
            (self.site_length, 0, floor_thickness),
            (self.site_length, self.site_width, floor_thickness),
            (0, self.site_width, floor_thickness),
        ]

        #rotate the points around (0, 0), then translate to position
        angle_rad = math.radians(self.orientation_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        rotated_translated_vertices = []

        for x, y, z in local_vertices:
            x_rot = x * cos_a - y * sin_a
            y_rot = x * sin_a + y * cos_a
            x_final = x_rot + self.position[0]
            y_final = y_rot + self.position[1]
            rotated_translated_vertices.append((x_final, y_final, z))

        #create site slab
        site_slab = ifcopenshell.api.root.create_entity(
            self.model, ifc_class="IfcSlab", name=self.name
        )

        site_representation = ifcopenshell.api.geometry.add_mesh_representation(
            file=self.model,
            context=self.context,
            vertices=[[(*v,) for v in rotated_translated_vertices]],
            faces=[[list(range(len(rotated_translated_vertices)))]]
        )

        ifcopenshell.api.geometry.assign_representation(
            self.model, product=site_slab, representation=site_representation
        )

        ifcopenshell.api.spatial.assign_container(
            self.model, relating_structure=self.site, products=[site_slab]
        )

        return site_slab
