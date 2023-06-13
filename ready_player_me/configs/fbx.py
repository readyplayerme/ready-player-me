"""FBX settings for Ready Player Me."""
import math
from typing import Any

from mathutils import Matrix


def get_outfit_export_settings() -> dict[str, Any]:
    """Return default FBX export settings for the Ready Player Me platform.

    :return: Dictionary for use as keyword arguments in export function.
    :rtype: Dict[str, Any]
    """
    return {
        "use_selection": False,
        "use_visible": True,
        "use_active_collection": False,
        "global_scale": 1.0,
        "apply_unit_scale": False,
        "apply_scale_options": "FBX_SCALE_UNITS",
        "use_space_transform": True,
        "bake_space_transform": True,  # Otherwise, axis orientation is wrong.
        "object_types": {"MESH", "ARMATURE"},
        "use_mesh_modifiers": True,
        "use_mesh_modifiers_render": False,
        "mesh_smooth_type": "EDGE",
        "use_subsurf": False,
        "use_mesh_edges": False,
        "use_tspace": True,
        "use_triangles": False,
        "use_custom_props": False,
        "add_leaf_bones": False,  # Avoid memory/performance cost for something only useful for modelling
        "primary_bone_axis": "Y",
        "secondary_bone_axis": "X",
        "use_armature_deform_only": True,
        "armature_nodetype": "NULL",
        "bake_anim": False,
        "bake_anim_use_all_bones": True,
        "bake_anim_use_nla_strips": True,
        "bake_anim_use_all_actions": True,
        "bake_anim_force_startend_keying": True,
        "bake_anim_step": 1.0,
        "bake_anim_simplify_factor": 1.0,
        "path_mode": "COPY",
        "embed_textures": True,
        "batch_mode": "OFF",
        "use_batch_own_dir": True,
        "axis_forward": "-Z",
        "axis_up": "Y",
        # Not in UI.
        "global_matrix": Matrix.Rotation(-math.pi / 2.0, 4, "X"),
        "use_custom_normals": True,
    }
