from io import StringIO
import json

try: # Cura 5
    from PyQt6.QtCore import QTimer
except: # Cura 4
    from PyQt5.QtCore import QTimer

from cura.CuraApplication import CuraApplication
from cura.Settings.CuraContainerRegistry import CuraContainerRegistry

from UM.Application import Application
from UM.Message import Message
from UM.Logger import Logger
from UM.Extension import Extension
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from UM.i18n import i18nCatalog

catalog = i18nCatalog("cura")

from .DuetRRFOutputDevice import DuetRRFConfigureOutputDevice, DuetRRFOutputDevice, DuetRRFDeviceType
from .DuetRRFSettings import get_plugin_version, delete_config, get_config, init_settings, DUETRRF_SETTINGS
from .thumbnails import generate_thumbnail

class DuetRRFPlugin(Extension, OutputDevicePlugin):
    def __init__(self):
        super().__init__()
        self._application = CuraApplication.getInstance()
        self._application.globalContainerStackChanged.connect(self._checkDuetRRFOutputDevices)
        self._application.initializationFinished.connect(self._delay_check_unmapped_settings)
        self._application.getOutputDeviceManager().writeStarted.connect(self._embed_thumbnails)

        init_settings()

        self.addMenuItem(catalog.i18n("(moved to Preferences→Printer)"), self._showUnmappedSettingsMessage)

        self._found_unmapped = {}

    def start(self):
        pass

    def stop(self, store_data: bool = True):
        pass

    def _embed_thumbnails(self, output_device) -> None:
        if not get_config().get("embed_thumbnails", False):
            Logger.log("d", f"Skipping disabled thumbnail embedding or not a Duet-RRF printer.")
            return

        # fetch sliced gcode from scene and active build plate
        active_build_plate_id = self._application.getMultiBuildPlateModel().activeBuildPlate
        scene = Application.getInstance().getController().getScene()
        gcode_dict = getattr(scene, "gcode_dict", None)
        if not gcode_dict:
            return
        gcode_list = gcode_dict[active_build_plate_id]
        if not gcode_list:
            return

        if ";Exported with Cura-DuetRRF" not in gcode_list[0]:
            # assemble everything and inject custom data
            Logger.log("i", "Assembling final gcode file...")

            version = get_plugin_version()
            thumbnail_stream = generate_thumbnail()
            gcode_list[0] += f";Exported with Cura-DuetRRF v{version} plugin by Thomas Kriechbaumer\n"
            gcode_list[0] += thumbnail_stream.getvalue()

            # store new gcode back into scene and active build plate
            gcode_dict[active_build_plate_id] = gcode_list
            setattr(scene, "gcode_dict", gcode_dict)
        else:
            Logger.log("e", "Already embedded thumbnails")

    def _delay_check_unmapped_settings(self):
        self._change_timer = QTimer()
        self._change_timer.setInterval(10000)
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self._check_unmapped_settings)
        self._change_timer.start()

    def _check_unmapped_settings(self):
        Logger.log("d", "called")
        try:
            instances = json.loads(self._application.getPreferences().getValue(DUETRRF_SETTINGS))

            stacks = CuraContainerRegistry.getInstance().findContainerStacks(type='machine')
            stacks = [stack.getId() for stack in stacks]

            for printer_id, data in instances.items():
                if printer_id not in stacks:
                    self._found_unmapped[printer_id] = data
        except Exception as e:
            Logger.log("d", str(e))

        if self._found_unmapped:
            Logger.log("d", "Unmapped settings found!")
            self._showUnmappedSettingsMessage()
        else:
            Logger.log("d", "No unmapped settings found.")

    def _showUnmappedSettingsMessage(self):
        Logger.log("d", "called: {}".format(self._found_unmapped.keys()))

        msg = (
            "Settings for the DuetRRF plugin moved to the Printer preferences.\n\n"
            "Please go to:\n"
            "→ Cura Preferences\n"
            "→ Printers\n"
            "→ activate and select your printer\n"
            "→ click on 'Connect Duet RepRapFirmware'\n"
        )
        if self._found_unmapped:
            msg += "\n\n"
            msg += "You have unmapped settings for unknown printers:\n"
            for printer_id, data in self._found_unmapped.items():
                t = "   {}:\n".format(printer_id)
                if "url" in data and data["url"].strip():
                    t += "→ URL: {}\n".format(data["url"])
                if "duet_password" in data and data["duet_password"].strip():
                    t += "→ Duet password: {}\n".format(data["duet_password"])
                if "http_username" in data and data["http_username"].strip():
                    t += "→ HTTP Basic username: {}\n".format(data["http_username"])
                if "http_password" in data and data["http_password"].strip():
                    t += "→ HTTP Basic password: {}\n".format(data["http_password"])
                msg += t

        message = Message(
            msg,
            lifetime=0,
            title="DuetRRF: Settings moved to Cura Preferences!",
        )
        if self._found_unmapped:
            message.addAction(
                action_id="ignore",
                name=catalog.i18nc("@action:button", "Ignore"),
                icon="",
                description="Close this message",
            )
            message.addAction(
                action_id="delete",
                name=catalog.i18nc("@action:button", "Delete"),
                icon="",
                description="Delete unmapped settings for unknown printers",
            )
            message.actionTriggered.connect(self._onActionTriggeredUnmappedSettings)
        message.show()

    def _onActionTriggeredUnmappedSettings(self, message, action):
        Logger.log("d", "called: {}, {}".format(action, self._found_unmapped.keys()))
        message.hide()

        if action == "ignore":
            return
        if action == "delete" and not self._found_unmapped:
            return

        for printer_id in self._found_unmapped.keys():
            if delete_config(printer_id):
                Logger.log("d", "successfully delete unmapped settings for {}".format(printer_id))
            else:
                Logger.log("e", "failed to delete unmapped settings for {}".format(printer_id))

        message = Message(
            "Unmapped settings have been deleted for the following printers:\n{}\n\n".format(
                ",\n".join(self._found_unmapped.keys())
            ),
            lifetime=5000,
            title="DuetRRF: unmapped settings successfully deleted!",
        )
        message.show()
        self._found_unmapped = {}

    def _checkDuetRRFOutputDevices(self):
        global_container_stack = self._application.getGlobalContainerStack()
        if not global_container_stack:
            return

        manager = self.getOutputDeviceManager()

        # remove all DuetRRF output devices - the new stack might not need them or have a different config
        manager.removeOutputDevice("duetrrf-configure")
        manager.removeOutputDevice("duetrrf-print")
        manager.removeOutputDevice("duetrrf-simulate")
        manager.removeOutputDevice("duetrrf-upload")

        # check and load new output devices
        config = get_config()
        if config:
            Logger.log("d", f"DuetRRF is active for printer: id:{global_container_stack.getId()}, name:{global_container_stack.getName(),}, config:{config}")
            manager.addOutputDevice(DuetRRFOutputDevice(config, DuetRRFDeviceType.print))
            manager.addOutputDevice(DuetRRFOutputDevice(config, DuetRRFDeviceType.simulate))
            manager.addOutputDevice(DuetRRFOutputDevice(config, DuetRRFDeviceType.upload))
        else:
            manager.addOutputDevice(DuetRRFConfigureOutputDevice())
            Logger.log("d", "DuetRRF is not available for printer: id:{}, name:{}".format(
                global_container_stack.getId(),
                global_container_stack.getName(),
            ))
