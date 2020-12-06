import json

from PyQt5.QtCore import Qt, QTimer

from cura.CuraApplication import CuraApplication
from cura.Settings.CuraContainerRegistry import CuraContainerRegistry

from UM.Message import Message
from UM.Logger import Logger
from UM.Extension import Extension
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from UM.i18n import i18nCatalog

catalog = i18nCatalog("cura")

from .DuetRRFOutputDevice import DuetRRFOutputDevice, DuetRRFDeviceType
from .DuetRRFSettings import delete_config, get_config, init_settings, DUETRRF_SETTINGS


class DuetRRFPlugin(Extension, OutputDevicePlugin):
    def __init__(self):
        super().__init__()
        self._application = CuraApplication.getInstance()
        self._application.globalContainerStackChanged.connect(self._checkDuetRRFOutputDevices)

        init_settings()

        self.addMenuItem(catalog.i18n("(moved to Preferences→Printer)"), self._showUnmappedSettingsMessage)

        self._found_unmapped = {}

        self._change_timer = QTimer()
        self._change_timer.setInterval(2000)
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self._check_unmapped_settings)
        self._change_timer.start()

    def start(self):
        pass

    def stop(self, store_data: bool = True):
        pass

    def _check_unmapped_settings(self):
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
            self.addMenuItem(catalog.i18n("Show unmapped settings..."), self._showUnmappedSettingsMessage)
            self.addMenuItem(catalog.i18n("Delete unmapped settings"), self._deleteUnmappedSettings)
            self._showUnmappedSettingsMessage()

    def _showUnmappedSettingsMessage(self):
        Logger.log("d", "DuetRRF showUpgradeMessage called.")
        msg = (
            "Settings for the DuetRRF plugin moved to the Printer preferences.\n\n"
            "Please go to:\n"
            "→ Cura Preferences\n"
            "→ Printers\n"
            "→ activate and select your printer\n"
            "→ click on 'Connect Duet RepRapFirmware'\n"
            "\n"
            "You can can delete unmapped settings of unknown printers via:\n"
            "→ Extensions menu → DuetRRF → Delete unmapped settings\n"
            "\n"
            "You have unmapped settings for unknown printers:\n"
        )
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
        message.show()

    def _deleteUnmappedSettings(self):
        Logger.log("d", "DuetRRF deleteUnmappedSettings called: {}".format(self._found_unmapped.keys()))

        for printer_id in self._found_unmapped.keys():
            delete_config(printer_id)

        message = Message(
            "Unmapped settings have been deleted for the following printers:\n{}\n\n"
            "Please restart Cura.".format(
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

        # remove all DuetRRF output devices - the new stack might not need them
        manager.removeOutputDevice("duetrrf-print")
        manager.removeOutputDevice("duetrrf-simulate")
        manager.removeOutputDevice("duetrrf-upload")

        # check and load new output devices
        s = get_config()
        if s:
            Logger.log("d", "DuetRRF is active for printer: id:{}, name:{}".format(
                global_container_stack.getId(),
                global_container_stack.getName(),
            ))
            manager.addOutputDevice(DuetRRFOutputDevice(s, DuetRRFDeviceType.print))
            manager.addOutputDevice(DuetRRFOutputDevice(s, DuetRRFDeviceType.simulate))
            manager.addOutputDevice(DuetRRFOutputDevice(s, DuetRRFDeviceType.upload))
        else:
            Logger.log("d", "DuetRRF is not available for printer: id:{}, name:{}".format(
                global_container_stack.getId(),
                global_container_stack.getName(),
            ))
