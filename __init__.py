from UM.Logger import Logger

from . import DuetRRFPlugin, DuetRRFAction, DuetRRFSettings


def getMetaData():
    return {}


def register(app):
    v = DuetRRFSettings.get_plugin_version() or "failed to get version information!"
    Logger.log("d", f"DuetRRF plugin version: {v}")

    plugin = DuetRRFPlugin.DuetRRFPlugin()
    action = DuetRRFAction.DuetRRFAction()
    return {
        "extension": plugin,
        "output_device": plugin,
        "machine_action": action,
    }
