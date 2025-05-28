
## BuildingComposer.py ##
# This script generates IFC-files for oriented buildings based on specified site geometry, correct geographic location and orientation parameters 

#import ifcOpenSchell API modules
import ifcopenshell.api.root
import ifcopenshell.api.unit
import ifcopenshell.api.context
import ifcopenshell.api.project
import ifcopenshell.api.spatial
import ifcopenshell.api.geometry
import ifcopenshell.api.aggregate

#import libraries
import numpy as np
import math

#import BuildingComposer classes 
from BuildingComposer.Window.Rectangular_Oriented import Rectangular
from BuildingComposer.Roofs.Pyramid_Oriented import Pyramid
from BuildingComposer.Roofs.Prism_Oriented import Prism
from BuildingComposer.Roofs.Pitched_Oriented import Pitched
from BuildingComposer.SquareSiteOriented import SquareSiteOriented

class BuildingComposer:
    def __init__(self, sites, buildings, output_file=None):
        self.sites = sites
        self.buildings = buildings
        self.output_file =  output_file

    def build(self):
        if self.output_file is None:
            self.output_file = "multiple_buildings.ifc"

        model = ifcopenshell.api.project.create_file()
        project = ifcopenshell.api.root.create_entity(model, ifc_class="IfcProject", name="Multi-Building Project")
        ifcopenshell.api.unit.assign_unit(model)
        context = ifcopenshell.api.context.add_context(model, context_type="Model")
        body = ifcopenshell.api.context.add_context(
            model, context_type="Model", context_identifier="Body", target_view="MODEL_VIEW", parent=context
        )
        site = ifcopenshell.api.root.create_entity(model, ifc_class="IfcSite", name="Shared Site")
        ifcopenshell.api.aggregate.assign_object(model, relating_object=project, products=[site])

        for idx, site_params in enumerate(self.sites):
            site_name = site_params["name"]
            site_length = site_params["length"]
            site_width = site_params["width"]
            site_angle = site_params["angle"]
            site_pos_x = site_params.get("position_x", 0.0)
            site_pos_y = site_params.get("position_y", 0.0)
            orientation_deg_fix = -site_angle % 360

            add_square_site = SquareSiteOriented(
                model=model, context=body, site=site, site_width=site_width,
                site_length=site_length, name=site_name,
                orientation_deg=orientation_deg_fix, position=(site_pos_x, site_pos_y)
            )
            add_square_site.AddSquareSite()
            x_offset = site_pos_x
            y_offset = site_pos_y

            for building_params in self.buildings:
                if building_params["site"] != site_name:
                    continue

                building_name = f"{site_name}_Building"
                building = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuilding", name=building_name)
                ifcopenshell.api.aggregate.assign_object(model, relating_object=site, products=[building])

                location_point = model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
                placement = model.create_entity("IfcAxis2Placement3D", Location=location_point)
                building.ObjectPlacement = model.create_entity("IfcLocalPlacement", PlacementRelTo=site.ObjectPlacement, RelativePlacement=placement)

                shape = building_params["shape"]
                roof_type = building_params["roof_type"]
                window_type = building_params["window_type"]
                length = building_params["length"]
                width = building_params["width"]
                height = building_params["height"] 
                top_height = building_params["top_height"]
                thickness = building_params["thickness"]
                arm1_thickness = building_params.get("arm1_thickness")
                arm2_thickness = building_params.get("arm2_thickness")
                overhang = building_params["overhang"]
                num_levels = building_params["num_levels"]
                window_sill_height = building_params.get("window_sill_height")
                window_width = building_params.get("window_width")
                window_height = building_params.get("window_height")

                orientation_deg_fix = -site_angle % 360
                angle_rad = math.radians(orientation_deg_fix)
                cos_a = math.cos(angle_rad)
                sin_a = math.sin(angle_rad)

                def rotate_vector(dx, dy):
                    return dx * cos_a - dy * sin_a, dx * sin_a + dy * cos_a

                def rotate_point(x, y):
                    rel_x, rel_y = x - site_pos_x, y - site_pos_y
                    return rel_x * cos_a - rel_y * sin_a + site_pos_x, rel_x * sin_a + rel_y * cos_a + site_pos_y

                for level in range(num_levels):
                    storey = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuildingStorey", name=f"{building_name} - Level {level + 1}")
                    elevation_point = model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, level * height))
                    placement = model.create_entity("IfcAxis2Placement3D", Location=elevation_point)
                    storey.ObjectPlacement = model.create_entity("IfcLocalPlacement", PlacementRelTo=building.ObjectPlacement, RelativePlacement=placement)
                    ifcopenshell.api.aggregate.assign_object(model, relating_object=building, products=[storey])

                    if shape == "L-shape":
                        positions = [
                            (x_offset, y_offset),
                            (x_offset + length, y_offset),
                            (x_offset + length, y_offset + arm1_thickness),
                            (x_offset + arm2_thickness, y_offset + arm1_thickness),
                            (x_offset + arm2_thickness, y_offset + width),
                            (x_offset, y_offset + width)
                        ]
                        orientations = [(1, 0), (0, 1), (-1, 0), (0, 1), (-1, 0), (0, -1)]
                        wall_lengths = [length, arm1_thickness, length - arm2_thickness, width - arm1_thickness, arm2_thickness, width]
                    else:
                        positions = [
                            (x_offset, y_offset),
                            (x_offset + length, y_offset),
                            (x_offset + length, y_offset + width),
                            (x_offset, y_offset + width)
                        ]
                        orientations = [(1, 0), (0, 1), (-1, 0), (0, -1)]
                        wall_lengths = [length, width, length, width]

                    rotated_positions = [rotate_point(*pt) for pt in positions]
                    floor_vertices = [(x, y, level * height) for (x, y) in rotated_positions]

                    floor = ifcopenshell.api.root.create_entity(model, ifc_class="IfcSlab", name=f"{building_name} - Floor Level {level + 1}")
                    floor_representation = ifcopenshell.api.geometry.add_mesh_representation(model, context=body, vertices=[floor_vertices], faces=[[list(range(len(floor_vertices)))]] )
                    ifcopenshell.api.geometry.assign_representation(model, product=floor, representation=floor_representation)
                    ifcopenshell.api.spatial.assign_container(model, relating_structure=storey, products=[floor])

                    for i, (orig, dir_vec, wall_len) in enumerate(zip(rotated_positions, orientations, wall_lengths)):
                        wall = ifcopenshell.api.root.create_entity(model, ifc_class="IfcWall", name=f"{building_name} - Wall {i + 1} (Level {level + 1})")
                        matrix = np.identity(4)
                        matrix[0:3, 3] = [orig[0], orig[1], level * height]
                        matrix[0:3, 0] = [*rotate_vector(*dir_vec), 0]
                        ifcopenshell.api.geometry.edit_object_placement(model, product=wall, matrix=matrix)
                        wall_rep = ifcopenshell.api.geometry.add_wall_representation(model, context=body, length=wall_len, height=height, thickness=thickness)
                        ifcopenshell.api.geometry.assign_representation(model, product=wall, representation=wall_rep)
                        ifcopenshell.api.spatial.assign_container(model, relating_structure=storey, products=[wall])

                        if window_type == "standard":
                            Rectangular(
                                shape=shape,
                                model=model,
                                storey=storey,
                                wall=wall,
                                wall_length=length,
                                wall_width=width,
                                wall_length_windows=wall_len,
                                wall_orientation=i,
                                level_height=level * height,
                                window_width=window_width,
                                window_height=window_height,
                                window_sill_height=window_sill_height,
                                context=body,
                                thickness=thickness,
                                distance_between_windows=1,
                                arm_1=arm1_thickness,
                                arm_2=arm2_thickness,
                                x_offset=rotate_point(x_offset, y_offset)[0],
                                y_offset=rotate_point(x_offset, y_offset)[1],
                                angle_deg=orientation_deg_fix,  
                                factor_west=1,
                                factor_east=1,
                                factor_south=1,
                                factor_north=1
                            ).add_rectangular_windows()


                    roof_func = {"Pyramid": Pyramid, "Prism": Prism, "Pitched": Pitched}.get(roof_type)
                    placement_height = (num_levels) * height

                    if roof_func:
                        roof_func(
                            shape, model, storey, width, length, thickness,
                            placement_height, top_height, overhang,
                            arm1_thickness, arm2_thickness, body,
                            *rotate_point(x_offset, y_offset),
                            orientation_deg_fix  
                        ).__getattribute__(f"Add{roof_type}Roof")()

        model.write(self.output_file)
        print(f"IFC file with multiple buildings created: {self.output_file}")

