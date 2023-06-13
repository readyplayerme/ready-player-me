"""glTF settings for Ready Player Me."""


def get_outfit_export_settings() -> dict[str, bool | str | int]:
    """Return default GLB export settings for the Ready Player Me platform.

    :return: Dictionary for use as keyword arguments in export function.
    :rtype: Dict[str, Any]
    """
    return {
        "export_format": "GLB",
        "export_copyright": "",  # No need for now.
        "export_image_format": "AUTO",
        "export_texture_dir": "",
        "export_keep_originals": False,
        "export_texcoords": True,
        "export_normals": True,
        "export_draco_mesh_compression_enable": False,
        "export_tangents": True,
        "export_materials": "EXPORT",
        "export_original_specular": False,
        "export_colors": False,
        "use_mesh_edges": False,
        "use_mesh_vertices": False,
        "export_cameras": False,
        "use_selection": False,
        "use_visible": True,
        "use_renderable": False,
        "use_active_collection": False,
        "use_active_scene": True,
        "export_extras": False,
        "export_yup": True,
        "export_apply": True,
        "check_existing": False,
        "export_animations": False,
        "export_frame_range": False,
        "export_frame_step": 1,
        "export_force_sampling": True,
        "export_nla_strips": True,
        "export_nla_strips_merged_animation_name": "Animation",
        "export_def_bones": True,
        "export_optimize_animation_size": True,
        "export_anim_single_armature": True,
        "export_current_frame": False,
        "export_skins": True,
        "export_all_influences": False,
        "export_morph": False,
        "export_morph_normal": False,
        "export_morph_tangent": False,
        "export_lights": False,
        "will_save_settings": False,
    }


def get_blendshape_export_settings() -> dict[str, bool | str | int]:
    """Return GLB export settings that include blendshapes for the Ready Player Me platform."""
    settings = get_outfit_export_settings()
    settings["export_apply"] = False
    settings["export_morph"] = True
    settings["export_morph_normal"] = False
    settings["export_morph_tangent"] = False
    return settings
