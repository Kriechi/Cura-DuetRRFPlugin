import os
import json

from UM.Logger import Logger

from . import DuetRRFPlugin, DuetRRFAction, DuetRRFSettings


def getMetaData():
    return {}


def register(app):
    v = DuetRRFSettings.get_plugin_version()
    if v:
        Logger.log("d", f"DuetRRFPlugin version: {v}")
    else:
        Logger.log("w", "DuetRRFPlugin failed to get version information!")

    plugin = DuetRRFPlugin.DuetRRFPlugin()
    return {
        "extension": plugin,
        "output_device": plugin,
        "machine_action": DuetRRFAction.DuetRRFAction()
    }
