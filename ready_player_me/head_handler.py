"""This module provides functions for manipulating the head and hair model in Blender used by the modular tool."""
import math
from pathlib import Path

import bpy
import mathutils
from ready_player_me.util import add_constraint


def get_head_objs() -> list[bpy.types.Object]:
    """Get a list of head objects in the scene, including hair and predicted hair."""
    head_objs: list[bpy.types.Object] = []
    obj_names = ("Wolf3D_Hair_female", "head", "PredictedHair")
    window = bpy.context.window_manager.windows[0]
    with bpy.context.temp_override(window=window):
        head_objs.extend(bpy.data.objects[name] for name in obj_names if name in bpy.data.objects)
    return head_objs


def get_head_obj() -> bpy.types.Object | None:
    """Get the head object in the scene."""
    window = bpy.context.window_manager.windows[0]
    with bpy.context.temp_override(window=window):
        return bpy.data.objects.get("head")


def transform_head_to_deltas(loc: tuple[float, float, float], rot: tuple[float, float, float]):
    """Move and rotate the head using delta transforms.

    :param loc: location for the object
    :param rot: rotation for the object in degrees (Euler XYZ)
    """
    if not (head := get_head_obj()):
        return

    # Translate the object.
    head.delta_location = loc  # type: ignore[union-attr]

    # Rotate the object.
    head.delta_rotation_euler = mathutils.Euler(  # type: ignore[union-attr]
        (*map(math.radians, rot),),
    )


def add_head_constraints(lib_path: str | Path):
    """Add the copy transform modifier specifics for the head.

    :param lib_path: path to the linked armature's library
    """
    with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
        if not (head := get_head_obj()):
            return
        target = bpy.data.objects["Armature", str(lib_path)]
        constraint = add_constraint(head, target, "COPY_TRANSFORMS")
        constraint.subtarget = "Neck"
        constraint.mix_mode = "BEFORE_FULL"

        # This can be adjusted. It had a different values but i guess putting it at 0 makes the neck gap less visible.
        constraint.head_tail = 0.822


def get_armature_path() -> str | None:
    """Get the path of the armature. It can be absolute or relative."""
    window = bpy.context.window_manager.windows[0]
    with bpy.context.temp_override(window=window):
        armature = bpy.data.objects.get("Armature")
        try:
            return armature.library.filepath
        except AttributeError:
            return None


def move_the_head():
    """Constrain the head to the armature."""
    with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
        if not (head := get_head_obj()):
            return
        # To stay compatible with Unix and Windows style separators, we use the Path class to find the library link.
        path = get_armature_path()
        lib_path = str(Path(path))
        try:
            target = bpy.data.objects["Armature", lib_path]
        except KeyError:
            return
        add_constraint(head, target, "COPY_TRANSFORMS")


def scale_head(x: float, y: float, z: float):
    """Scale the head related objects."""
    for obj in get_head_objs():
        obj.scale = (x, y, z)


def offset_head(x: float, y: float, z: float):
    """Move head related objects to the given location."""
    for obj in get_head_objs():
        obj.location = (x, y, z)
