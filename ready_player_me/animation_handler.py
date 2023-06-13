"""this module handles various animation actions"""

import contextlib

import bpy
from ready_player_me.data import anim_path

# Declaring this because we want to grab the current animation without knowing what was from UI
current_animation = ""


def select_skeleton():
    """Select the Armature. Returns the selected active Armature"""
    with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
        with contextlib.suppress(Exception):
            bpy.ops.object.mode_set(mode="OBJECT")
        try:
            armature = bpy.data.objects["Armature"]
            # Select the Armature in the scene.
            armature.select_set(True)

            # Make the selected object the active object.
            bpy.context.view_layer.objects.active = armature
            return armature

        except KeyError:
            print("No armature present in the scene")
            return


def get_pose_position():
    """Get the skeletal mesh pose position"""
    armature = select_skeleton()
    with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
        try:
            pose_position = armature.data.pose_position
            return pose_position
        except AttributeError:
            print("No armature selected. Noting to set in Pose position")
            return "POSE"


def clear_animation():
    """Unlinks all the animations from the AMATURE."""
    armature = select_skeleton()
    # Clearing the animation.
    try:
        armature.animation_data_clear()
    except AttributeError:
        print("No animation to clear")


def stop_playback():
    """Stops the playback of the animation"""
    with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
        bpy.ops.screen.animation_cancel(restore_frame=False)


def reset_pose():
    """Reset the bone poses. This is mandatory after an animation has unloaded"""
    select_skeleton()
    # Reset the Armature to the default POSE.
    with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
        try:
            for bone in bpy.context.object.pose.bones:
                bone.location = (0, 0, 0)
                bone.rotation_quaternion = (1, 0, 0, 0)
                bone.rotation_axis_angle = (0, 0, 1, 0)
                bone.rotation_euler = (0, 0, 0)
                bone.scale = (1, 1, 1)
        except AttributeError:
            print("Could not reset the pose. No armature found")


def set_x_view(set):
    """Make the bones visible through the mesh"""
    select_skeleton()
    with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
        try:
            bpy.context.object.show_in_front = set
        except AttributeError:
            print("No armature selected. Noting to set in Xview")


def set_pose_position(pose_position="POSE"):
    """Force the skeletal mesh to POSE position. can also be overwritten with REST position."""
    select_skeleton()
    with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
        try:
            bpy.context.object.data.pose_position = pose_position
        except AttributeError:
            print("No armature selected. Noting to set in Pose position")


def remove_animations():
    """Simply removes all the animations from the SCENE."""
    for animation in bpy.data.actions:
        bpy.data.actions.remove(animation)


def get_animations_name(animation_file=anim_path):
    """Get a list of animations from a blend file."""

    # Load the .blend file into Blender.
    try:
        with bpy.data.libraries.load(filepath=animation_file) as (data_from, animations):
            # Import only the actions.
            animations.actions = data_from.actions
        # Debug line to see the animations loaded.
        print(animations.actions)

        return animations.actions
    except OSError:
        print("Could not open file. Make sure you get it from Plastic")
        return None


def get_frame_index():
    """Gets the current frame nr."""
    return bpy.context.scene.frame_current


def set_frame_index(value):
    """sets the current frame nr."""
    bpy.context.scene.frame_set(value)


def set_playback_speed(value):
    """sets the playback speed"""
    # Right now is a bit of a hack. It only limits the FPS.
    # Would be nice if we could resize / remap the animation for the playback, but is much more complex
    bpy.context.scene.render.fps = value


def set_playback_range(start, end):
    """Set the playback range to match the animation in Blender"""
    scene = bpy.context.scene
    scene.frame_start = start
    scene.frame_end = end


def get_anim_framerange_from_blender():
    """Get the active animation Start / End frame from active animation"""
    with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
        try:
            anim = bpy.context.object.animation_data.action
            start, end = map(int, anim.frame_range)
            return (start, end)
        except AttributeError:
            print("No animation into the scene. loading defaults")
            return (0, 100)


def link_animation(animation):
    """Linking an animation to an existing Armature."""
    # clear existing animation before linking another. Otherwise it will create a lot of duplicates.

    global current_animation

    clear_animation()
    reset_pose()
    set_pose_position()
    armature = select_skeleton()

    with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):

        try:
            # # Create a new NLA track for the armature.
            armature.animation_data_create()

            # Set the linked animation as the active action.
            armature.animation_data.action = bpy.data.actions[animation]

            # Update the global variable with the name of the currently linked animation
            current_animation = animation

            # Return the name of the currently linked animation
            return current_animation
        except AttributeError:
            print("could not link Animation")
            return current_animation


def update_animation():
    """
    Re-apply the animation to an existing Armature.
    This is useful when changing garments with modular tool.
    """
    if not (armature := select_skeleton()):
        return
    try:
        animation = current_animation
    except AttributeError:
        print("No active animation found")
        return

    with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):

        armature.animation_data_create()

        # Set the linked animation as the active action.
        try:
            armature.animation_data.action = bpy.data.actions[animation]
        except KeyError:
            print("No animation named", animation, "found in the scene")
