import contextlib
import logging
import os
from pathlib import Path

import bmesh
import bpy
import pyblend.object
import pyblend.overrides
import pyblend.shapekeys
import pyblend.util
from ready_player_me.data import (
    BodyShapes,
    FullBodySection,
    Shape,
    body_path_hack,
    bodyshapes_female_path,
    bodyshapes_male_path,
)


def safe_copy_object(obj: bpy.types.Object) -> bpy.types.Object:
    """Copy an object and its data to prevent multi-user bug.

    Clear materials if the object type supports them.
    :param obj: Object to copy safely.
    """
    new_obj = obj.copy()
    new_obj.data = obj.data.copy()
    with contextlib.suppress(AttributeError):  # Not every object type has a materials attribute.
        new_obj.data.materials.clear()
    return new_obj


def obj_has_gender_shapes(target_obj: bpy.types.Object) -> bool:
    """Return whether the target object has all shape keys related to physique associated with gender.

    :param target_obj: Object to check for shape keys.
    """
    if target_obj.data.shape_keys:
        # The expected shape names are in the Shape enum. Check for the difference.
        current_shapes = target_obj.data.shape_keys.key_blocks.keys()
        return not set(Shape) - set(current_shapes)
    return False


def obj_has_body_shapes(target_obj: bpy.types.Object) -> bool:
    if target_obj.data.shape_keys:
        # The expected shape names are in the BodyShape enum. Check for the difference.
        current_shapes = target_obj.data.shape_keys.key_blocks.keys()
        return not set(BodyShapes) - set(current_shapes)
    return False


def add_modifier_surface_deform(obj: bpy.types.Object, source: bpy.types.Object) -> bpy.types.Modifier:
    """Add a surface deform modifier to the target object, using the source object for deformations."""
    # This modifier is only applicable to meshes.
    if obj.type != "MESH":
        raise TypeError(f"Object '{obj.name}' is not a mesh! Cannot add surface deform modifier.")
    mod = obj.modifiers.new(name="Surface Deform", type="SURFACE_DEFORM")
    # Set where to get our deformations from.
    mod.target = source
    # Bind the object to the target.
    window = bpy.context.window_manager.windows[0]
    with bpy.context.temp_override(window=window, object=obj, active_object=obj):
        bpy.ops.object.surfacedeform_bind(modifier=mod.name)
    return mod


def add_modifier_laplacian_deform(
    obj: bpy.types.Object, vertex_group: str | bpy.types.VertexGroup
) -> bpy.types.Modifier:
    """Add a laplacian deform modifier to the target object, using the vertex group as anchor points."""
    mod = obj.modifiers.new(name="Laplacian Deform", type="LAPLACIANDEFORM")
    mod.vertex_group = vertex_group.name if isinstance(vertex_group, bpy.types.VertexGroup) else vertex_group
    window = bpy.context.window_manager.windows[0]
    with bpy.context.temp_override(window=window, object=obj, active_object=obj):
        bpy.ops.object.laplaciandeform_bind(modifier=mod.name)
    return mod


def add_modifier_triangulate(obj: bpy.types.Object) -> bpy.types.Modifier:
    """Add a triangulate modifier to the target object if not present."""
    mod = next(filter(lambda m: m.type == "TRIANGULATE", obj.modifiers), None)
    if not mod:
        mod = obj.modifiers.new(name="Triangulate", type="TRIANGULATE")
    mod.quad_method = "FIXED_ALTERNATE"
    mod.keep_custom_normals = True
    mod.show_in_editmode = False
    return mod


def add_modifier_geo_mask(obj: bpy.types.Object, name: str = "Mask") -> bpy.types.Modifier | None:
    """Add geometry nodes modifier for custom masking if not present.

    :param obj: Object to add the modifier to.
    :param name: Name to give the modifier.
    """
    node_group = bpy.data.node_groups.get("Mask by Attribute")
    if not node_group:
        user_scripts = bpy.utils.script_path_pref() or os.environ.get("BLENDER_USER_SCRIPTS")
        if not user_scripts:
            logging.error("No user script path found.")
            return None
        lib_file = Path(user_scripts) / "resources" / "libraries" / "HiddenSurfaceRemoval.blend"
        node_group = pyblend.util.import_node_group(lib_file, "Mask by Attribute")
    if not node_group:
        return None
    geo_mods = (mod for mod in obj.modifiers if mod.type == "NODES" and mod.name == name)
    geo_mod = next(geo_mods, None) or obj.modifiers.new(name=name, type="NODES")
    geo_mod.node_group = node_group
    return geo_mod


def remove_modifiers(obj: bpy.types.Object):
    """Remove any modifiers from an object except for the Armature modifiers."""
    for mod in obj.modifiers[:]:
        if mod.type == "ARMATURE":
            continue
        obj.modifiers.remove(mod)


def apply_modifiers(obj: bpy.types.Object):
    """Apply all modifiers except for the Armature modifiers."""
    for mod in obj.modifiers[:]:
        if mod.type == "ARMATURE":
            continue
        with bpy.context.temp_override(active_object=obj):
            bpy.ops.object.modifier_apply(modifier=mod.name)


def add_constraint(
    obj: bpy.types.Object, target: bpy.types.Object, type_: str = "COPY_TRANSFORMS"
) -> bpy.types.Constraint:
    """Add a constraint to the object and set the given target, if applicable.

    :param obj: The object to add the constraint to.
    :param target: The target to set for the constraint.
    :param type_: The type of constraint to add. Defaults to "COPY_TRANSFORMS".
    :return: Existing or newly added constraint.
    """
    constraint = next(filter(lambda c: c.type == type_, obj.constraints), None) or obj.constraints.new(type_)
    constraint.name = f"{target.name} {type_}"
    if hasattr(constraint, "target"):
        constraint.target = target
    return constraint


def add_vertex_group_all(obj: bpy.types.Object, group_name: str = "all") -> bpy.types.VertexGroup:
    """Add a vertex group to the object, and add all vertices to it."""
    # This modifier is only applicable to meshes.
    if obj.type != "MESH":
        raise TypeError(f"Object '{obj.name}' is not a mesh! Cannot add vertex group.")
    # Create the group.
    group = obj.vertex_groups.new(name=group_name)
    # Add all vertices to the group.
    group.add(range(len(obj.data.vertices)), 1.0, "ADD")
    return group


def remove_doubles(obj: bpy.types.Object, verts=None, dist=0.0001):  # , use_sharp_edge_from_normals: bool = True):
    """Remove doubles from the object."""
    # use instead of blender's "remove doubles" operator  to avoid context issues

    # todo this doesnt yet work with normals,
    #  bpy.ops.mesh.remove_doubles has a kwarg use_sharp_edge_from_normals
    #  but bmesh.ops.remove_doubles does not!

    mesh = obj.data
    bm = bmesh.new()  # create an empty BMesh
    bm.from_mesh(mesh)  # fill it in from a Mesh

    verts = verts or bm.verts

    bmesh.ops.remove_doubles(bm, verts=verts, dist=dist)

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(mesh)
    bm.free()  # free and prevent further access

    mesh.validate()
    mesh.update()


# todo transfer to pyblend
def transfer_shape_key(src: bpy.types.Object, target: bpy.types.Object, key_name: str, merge_verts: bool = False):
    """Transfer shape keys from a source object to a target object.

    This function utilizes the deform modifiers for that purpose.
    Previously existing shape keys a cleared from the target object.

    :param src: Source object with shape key.
    :param target: Target object to transfer shape key to.
    :param key: Name of the shape key that will be transferred.
    """

    print("transfer shape key", src.name, target.name, key_name)
    # prep imported src meshes so they can be edited

    for datablock in [src, src.data]:
        pyblend.overrides.make_override_editable(datablock)

    if any(obj.type != "MESH" for obj in (src, target)):
        raise TypeError(f"Objects '{src.name}' and '{target.name}' must be meshes!")
    pyblend.shapekeys.clear_shape_keys_weights(src)

    # some meshes have split vertices, e.g. when importing GLBs hard edges are split into multiple vertices
    # weld the vertices to prevent the relaxing step creating gaps in the model
    if merge_verts:
        # prep target mesh so it can be edited
        for datablock in [target, target.data]:
            pyblend.overrides.make_override_editable(datablock)

        # ---------------------------------------------------------------------------------
        # everything in this block, is needed to get the remove_doubles operator to work consistently
        # deselect all, only works in object mode
        with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.context.active_object.select_set(False)

            # select the target obj
            bpy.context.view_layer.objects.active = target

            with bpy.context.temp_override(active_object=target):
                # remove_doubles(target)
                bpy.ops.object.mode_set(mode="EDIT")
                bpy.ops.mesh.select_all(action="SELECT")
                bpy.ops.mesh.remove_doubles(threshold=0.001, use_sharp_edge_from_normals=True)
                bpy.ops.mesh.select_all(action="DESELECT")
                bpy.ops.object.mode_set(mode="OBJECT")
        # ---------------------------------------------------------------------------------

    # We'll deform a temporary copy of the target object and feed it back as a shape key.
    shape_obj = safe_copy_object(target)
    # The shape key name on target_obj will be that of the shape_object.
    shape_obj.name = key_name

    # Link to scene. Required for binding deform modifiers. Needed under context.
    bpy.context.scene.collection.objects.link(shape_obj)

    # Remove shape keys for our duplicate since meshes with shape keys can't have modifiers.
    shape_obj.shape_key_clear()

    add_modifier_surface_deform(shape_obj, src)
    # Create a vertex group for the shape, containing all the vertices to use as anchor points for laplacian deform.
    vertex_group = add_vertex_group_all(shape_obj, group_name="temp_all_verts")
    add_modifier_laplacian_deform(shape_obj, vertex_group)
    # Set the shape key weight on the source object, so the target deforms with it.
    pyblend.shapekeys.set_exclusive_shape_weight(src.data, key=key_name)

    # Merge shape_obj into target_obj as a shape key.
    # Need to set the window in the context override, otherwise the join will fail.
    window = bpy.context.window_manager.windows[0]
    with bpy.context.temp_override(window=window, active_object=target, selected_editable_objects=[shape_obj]):
        bpy.ops.object.join_shapes()
    # Cleanup.
    pyblend.object.remove_object_from_file(shape_obj)


def add_gender_shapes(target_obj: bpy.types.Object):
    """Add gender shape keys to the target object.

    :param target_obj: Object to add shape keys to. Expecting a gender-neutral asset.
    """
    # Skip if we already have the shape keys.
    if obj_has_gender_shapes(target_obj):
        return

    # Get the body geometry that has deformation shape keys.
    body_obj = pyblend.object.import_objects(body_path_hack, obj_type="MESH", include=[FullBodySection.BODY])[0]
    for datablock in [body_obj, body_obj.data]:
        pyblend.overrides.make_override_editable(datablock)
    # Make sure we have the neutral base.
    pyblend.shapekeys.add_shape_key(target_obj, key_name=Shape.NEUTRAL)
    # Add the other shape keys in Shape to target_obj.
    for shape_name in list(Shape)[1:]:  # Skip neutral.
        transfer_shape_key(body_obj, target_obj, shape_name)

    # Remove the deform body mesh for cleanup.
    pyblend.object.remove_object_from_file(body_obj)


def add_body_shapes_male(target_obj: bpy.types.Object):
    add_body_shapes(target_obj, bodyshapes_male_path)


def add_body_shapes_female(target_obj: bpy.types.Object):
    add_body_shapes(target_obj, bodyshapes_female_path)


def add_body_shapes(target_obj: bpy.types.Object, blendshape_path):
    """Add gender shape keys to the target object.

    :param target_obj: Object to add shape keys to. Expecting a gender-neutral asset.
    """
    # Skip if we already have the shape keys.
    if obj_has_body_shapes(target_obj):
        return

    # Get the body geometry that has deformation shape keys for the correct gender
    body_obj = pyblend.object.import_objects(blendshape_path, obj_type="MESH", include=[FullBodySection.BODY])[0]

    # Add the other shape keys in bodyshapes to target_obj.
    for shape_name in BodyShapes:  # Skip neutral.
        transfer_shape_key(body_obj, target_obj, shape_name, merge_verts=True)

    # Remove the deform body mesh for cleanup.
    pyblend.object.remove_object_from_file(body_obj)
