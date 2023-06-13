from pathlib import Path

import bpy
import pyblend.object
from pyblend.armature import set_armature_on_objects


def link_armatures(source_path: Path | str, link: bool = True, relative: bool = True) -> list[bpy.types.Object]:
    """Link armatures from another blend-file into the current scene.

    Call this within a modified context.

    :param source_path: Path to blend-file to link armatures from.
    :param link: Link or append the armatures.
    :param relative: Use relative paths.
    :return: List of linked armatures.
    """
    with bpy.data.libraries.load(filepath=str(source_path), link=link, relative=relative) as (data_from, data_to):
        data_to.armatures = data_from.armatures

    linked_obj = []
    for block in data_to.armatures:
        try:
            obj = bpy.data.objects.new(block.name, block)
            bpy.context.scene.collection.objects.link(obj)
        except (RuntimeError, TypeError, AttributeError) as error:
            print(error)
            continue
        linked_obj.append(obj)

    return linked_obj


def import_armature(source_path: Path | str):
    """Import an armature from another blend-file into the current scene and attach the active object to it.

    :param source_path: Path to blend-file to import armature from.
    """
    window = bpy.context.window_manager.windows[0]
    with bpy.context.temp_override(window=window):
        linked_armature_objs = link_armatures(source_path, link=True)

        # Get selected asset to transfer skinning to.
        target_obj = bpy.context.active_object

        set_armature_on_objects([target_obj], linked_armature_objs[0])


def transfer_skin(source_path: Path | str):
    """Import meshes from another blend-file and transfer skin weights to the active object.

    Uses the last of the linked meshes to get skin weights.

    :param source_path: Path to blend-file to import armature from.
    """
    # Get active object to transfer skinning to. This is not necessarily the selected object.
    asset_obj = bpy.context.active_object

    if asset_obj is None:
        return

    linked_objs = pyblend.object.import_objects(source_path, obj_type="MESH")

    # TODO fix hack since first mesh is Head, second is body. we should only have 1 mesh in here.
    source_obj = linked_objs[-1]

    # Add transfer data modifier to asset.
    mod = asset_obj.modifiers.new(name="SkinTransfer", type="DATA_TRANSFER")
    mod.use_vert_data = True
    mod.object = source_obj
    mod.data_types_verts = {"VGROUP_WEIGHTS"}

    # Transfer skinning.
    bpy.ops.object.datalayout_transfer(modifier="SkinTransfer", data_type="VGROUP_WEIGHTS")

    bpy.ops.object.modifier_apply(modifier="SkinTransfer")

    # Unlink objects again after transfer.
    for obj in linked_objs:
        bpy.context.scene.collection.objects.unlink(obj)
