from io import StringIO
from typing import cast

from UM.Logger import Logger
from UM.Mesh.MeshWriter import MeshWriter
from UM.PluginRegistry import PluginRegistry


def serializing_scene_to_gcode():
    # get the gcode through the GCodeWrite plugin
    # this serializes the actual scene and should produce the same output as "Save to File"

    Logger.log("d", "Serializing gcode...")
    gcode_writer = cast(MeshWriter, PluginRegistry.getInstance().getPluginObject("GCodeWriter"))
    gcode_stream = StringIO()
    success = gcode_writer.write(gcode_stream, None)
    if not success:
        Logger.log("e", "GCodeWriter failed.")
        return None
    return gcode_stream
