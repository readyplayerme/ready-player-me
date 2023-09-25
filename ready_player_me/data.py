import os
from enum import Enum
from pathlib import Path

import bpy
from pyblend.file_io.paths import paths_exist


def alert_missing_paths(paths: list[Path]):
    """Alert the user if some paths are missing or include the local dir (".").

    :param paths: Paths to check.
    """
    if Path("") in paths or not paths_exist(paths):
        msg = (
            "Not all ENV vars are found: RPM_MODULAR_ASSETS, RPM_WARDROBE and RPM_ASSETLIB."
            "Run the BAT files in Plastic and restart blender."
        )
        print(msg)
        # Showing a message box this way is discouraged, but creating a new operator is overkill.
        # this crashes when blender is not fully initialized yet, but this module is imported an missing a path.
        # bpy.context.window_manager.popup_menu(lambda self, _: self.layout.label(text=msg), title="Error", icon="ERROR")

# Get paths to workspaces from environment variables.
modular_assets_path = Path(os.environ.get("RPM_MODULAR_ASSETS", ""))
wardrobe_path = Path(os.environ.get("RPM_WARDROBE", ""))
assetlib_path = Path(os.environ.get("RPM_ASSETLIB", ""))

# run the command "cm workspace list".
# the output liiks like this:
#   assetlib@WOLF-PC           c:\Users\USER\wkspaces\assetlib
#   wardrobe@WOLF-PC           c:\Users\USER\wkspaces\wardrobe
#   partner-assets@WOLF-PC     c:\Users\USER\wkspaces\partner-assets
#   modular_assets_2@WOLF-PC   c:\Users\USER\wkspaces\modular_assets
#   Blender-Tools@WOLF-PC      c:\Users\USER\wkspaces\Blender-Tools_2

# run it
import subprocess
output = subprocess.check_output("cm workspace list", shell=True)
output = output.decode("utf-8")  # output is a byte string, convert to utf-8
lines = output.split("\n")
lines = [line for line in lines if line]  # remove empty lines
lines = [line.split() for line in lines]  # split into name and path
lines = {line[0].split("@")[0]: Path(line[1]) for line in lines}

if not os.environ.get("RPM_MODULAR_ASSETS"):
    modular_assets_path = lines["modular_assets"]
if not os.environ.get("RPM_WARDROBE"):
    wardrobe_path = lines["wardrobe"]
if not os.environ.get("RPM_ASSETLIB"):
    assetlib_path = lines["assetlib"]

# Where there any environment variables not set?
alert_missing_paths([modular_assets_path, wardrobe_path, assetlib_path])

body_path = modular_assets_path / "body/body_neutral.blend"
body_legacy_path = modular_assets_path / "body/body_neutral_legacy.blend"
body_path_hack = (
    modular_assets_path / "body/legacy_v2_deform.blend"
)  # eventually we want to get rid of this, and merge it with body_path
head_path = str(modular_assets_path / Path("head/head.7.1.blend"))
anim_path = str(modular_assets_path / Path("animations/Animations.blend"))

# preferably only use for legacy gendered bodyshapes
bodyshapes_female_path = modular_assets_path / "body/bodyshapes_female.blend"
bodyshapes_male_path = modular_assets_path / "body/bodyshapes_male.blend"


class FullBodySection(str, Enum):
    TOP = "Wolf3D_Outfit_Top"
    BOTTOM = "Wolf3D_Outfit_Bottom"
    FOOTWEAR = "Wolf3D_Outfit_Footwear"
    BODY = "Wolf3D_Body"


class ArmaturePaths(Enum):
    NEUTRAL: Path = modular_assets_path / "armature" / "armature_neutral.blend"
    MALE_V2: Path = modular_assets_path / "armature" / "armature_v2_m.blend"
    FEMALE_V2: Path = modular_assets_path / "armature" / "armature_v2_f.blend"


class Shape(str, Enum):
    NEUTRAL = "neutral"
    MALE = "male"
    FEMALE = "female"


# final name
class BodyShapes(str, Enum):
    AVERAGE = "shapeBody01_average"
    ATHLETIC = "shapeBody02_athletic"
    HEAVYSET = "shapeBody03_heavyset"
    PLUSSIZE = "shapeBody04_plussize"


# input name is e.g. female_shapeBody01_average_bsps
