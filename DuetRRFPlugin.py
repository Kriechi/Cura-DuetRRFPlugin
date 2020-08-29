import os
import json
import re

from cura.CuraApplication import CuraApplication

from UM.Message import Message
from UM.Logger import Logger
from UM.Extension import Extension
from UM.PluginRegistry import PluginRegistry
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

from .DuetRRFOutputDevice import DuetRRFOutputDevice, DuetRRFDeviceType


class DuetRRFPlugin(Extension, OutputDevicePlugin):
    def __init__(self):
        super().__init__()
        self._application = CuraApplication.getInstance()
        self._application.globalContainerStackChanged.connect(self.checkDuetRRFOutputDevices)

        # LEGACY code - remove me!
        # only add legacy menu item if legacy settings exist
        try:
            self._instances = json.loads(CuraApplication.getInstance().getPreferences().getValue("duetrrf/instances"))
            Logger.log("d", "found legacy settings for {}".format(", ".join(self._instances.keys())))
            self.addMenuItem(catalog.i18n("(moved to Preferences→Printer)"), self.showSettingsDialog)
            self.addMenuItem(catalog.i18n("(delete all old legacy settings)"), self.deleteAllOldLegacySettings)
        except:
            pass

    def migrateOldSettings(self):
        """
        This is only to provide legacy compatibility and will be removed in a future release.
        """
        try:
            self._instances = json.loads(CuraApplication.getInstance().getPreferences().getValue("duetrrf/instances"))
        except:
            return

        global_container_stack = self._application.getGlobalContainerStack()
        name = global_container_stack.getName()

        if name in self._instances.keys():
            Logger.log("d", "migrating legacy settings for {}".format(name))
            global_container_stack.setMetaDataEntry("duetrrf", True)
            global_container_stack.setMetaDataEntry("duetrrf_url", self._instances[name]["url"])
            global_container_stack.setMetaDataEntry("duetrrf_duet_password", self._instances[name]["duet_password"])
            global_container_stack.setMetaDataEntry("duetrrf_http_user", self._instances[name]["http_user"])
            global_container_stack.setMetaDataEntry("duetrrf_http_password", self._instances[name]["http_password"])

            # delete this printer from the old settings - the new metadata is now the only source of truth.
            del self._instances[name]
            if len(self._instances) == 0:
                CuraApplication.getInstance().getPreferences().removePreference("duetrrf/instances")
            else:
                CuraApplication.getInstance().getPreferences().setValue("duetrrf/instances", json.dumps(self._instances))

    def showSettingsDialog(self):
        """
        This is only to provide legacy compatibility and will be removed in a future release.
        """
        Logger.log("d", "DuetRRF showSettingsDialog called.")
        message = Message(
            "Settings for the DuetRRF plugin moved to the Printer preferences.\n\n"
            "Please go to:\n"
            "\t → Cura Preferences\n"
            "\t → Printers\n"
            "\t → activate and select your printer\n"
            "\t → click on 'Connect Duet RepRapFirmware'\n\n"
            "You still have legacy settings for other printers:\n{}\n\n"
            "Please check all your printer settings!".format(
                ",\n".join(self._instances.keys())
            ),
            lifetime=0,
            title="Deprecation: DuetRRF settings have moved to Cura Preferences!",
        )
        message.show()

    def deleteAllOldLegacySettings(self):
        """
        This is only to provide legacy compatibility and will be removed in a future release.
        """
        Logger.log("d", "DuetRRF deleteAllOldLegacySettings called.")
        CuraApplication.getInstance().getPreferences().removePreference("duetrrf/instances")
        message = Message(
            "Legacy settings have been deleted for the following printers:\n{}\n\n"
            "Please restart Cura.".format(
                ",\n".join(self._instances.keys())
            ),
            lifetime=0,
            title="Legacy DuetRRF settings successfully deleted!",
        )
        message.show()

    def checkDuetRRFOutputDevices(self):
        global_container_stack = self._application.getGlobalContainerStack()
        if not global_container_stack:
            return

        self.migrateOldSettings() # LEGACY code - remove me!

        manager = self.getOutputDeviceManager()

        # remove all DuetRRF output devices - the new stack might not need them
        manager.removeOutputDevice("duetrrf-print")
        manager.removeOutputDevice("duetrrf-simulate")
        manager.removeOutputDevice("duetrrf-upload")

        # check and load new output devices
        if global_container_stack.getMetaDataEntry("duetrrf"):
            Logger.log("d", "DuetRRF is active for printer: " + global_container_stack.getName())
            manager.addOutputDevice(DuetRRFOutputDevice("duetrrf-print", DuetRRFDeviceType.print))
            manager.addOutputDevice(DuetRRFOutputDevice("duetrrf-simulate", DuetRRFDeviceType.simulate))
            manager.addOutputDevice(DuetRRFOutputDevice("duetrrf-upload", DuetRRFDeviceType.upload))
        else:
            Logger.log("d", "DuetRRF is not active for printer: " + global_container_stack.getName())
