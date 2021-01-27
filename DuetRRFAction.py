import os
import json
import re
from typing import Dict, Type, TYPE_CHECKING, List, Optional, cast

from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal

from cura.CuraApplication import CuraApplication
from cura.MachineAction import MachineAction

from UM.Logger import Logger
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

from .DuetRRFSettings import delete_config, get_config, save_config


class DuetRRFAction(MachineAction):
    def __init__(self, parent: QObject = None) -> None:
        super().__init__("DuetRRFAction", catalog.i18nc("@action", "Connect Duet RepRapFirmware"))

        self._qml_url = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'qml', 'DuetRRFAction.qml')

        self._application = CuraApplication.getInstance()
        self._application.globalContainerStackChanged.connect(self._onGlobalContainerStackChanged)
        ContainerRegistry.getInstance().containerAdded.connect(self._onContainerAdded)

    def _onGlobalContainerStackChanged(self) -> None:
        self.printerSettingsUrlChanged.emit()
        self.printerSettingsDuetPasswordChanged.emit()
        self.printerSettingsHTTPUserChanged.emit()
        self.printerSettingsHTTPPasswordChanged.emit()

    def _onContainerAdded(self, container: "ContainerInterface") -> None:
        # Add this action as a supported action to all machine definitions
        if (
            isinstance(container, DefinitionContainer) and
            container.getMetaDataEntry("type") == "machine" and
            container.getMetaDataEntry("supports_usb_connection")
        ):
            self._application.getMachineActionManager().addSupportedAction(container.getId(), self.getKey())

    def _reset(self) -> None:
        self.printerSettingsUrlChanged.emit()
        self.printerSettingsDuetPasswordChanged.emit()
        self.printerSettingsHTTPUserChanged.emit()
        self.printerSettingsHTTPPasswordChanged.emit()

    printerSettingsUrlChanged = pyqtSignal()
    printerSettingsDuetPasswordChanged = pyqtSignal()
    printerSettingsHTTPUserChanged = pyqtSignal()
    printerSettingsHTTPPasswordChanged = pyqtSignal()

    @pyqtProperty(str, notify=printerSettingsUrlChanged)
    def printerSettingUrl(self) -> Optional[str]:
        s = get_config()
        if s:
            return s["url"]
        return ""

    @pyqtProperty(str, notify=printerSettingsDuetPasswordChanged)
    def printerSettingDuetPassword(self) -> Optional[str]:
        s = get_config()
        if s:
            return s["duet_password"]
        return ""

    @pyqtProperty(str, notify=printerSettingsHTTPUserChanged)
    def printerSettingHTTPUser(self) -> Optional[str]:
        s = get_config()
        if s:
            return s["http_user"]
        return ""

    @pyqtProperty(str, notify=printerSettingsHTTPPasswordChanged)
    def printerSettingHTTPPassword(self) -> Optional[str]:
        s = get_config()
        if s:
            return s["http_password"]
        return ""

    @pyqtSlot(str, str, str, str)
    def saveConfig(self, url, duet_password, http_user, http_password):
        if not url.endswith('/'):
            url += '/'

        save_config(url, duet_password, http_user, http_password)
        Logger.log("d", "config saved")

        # trigger a stack change to reload the output devices
        self._application.globalContainerStackChanged.emit()

    @pyqtSlot()
    def deleteConfig(self):
        if delete_config():
            Logger.log("d", "config deleted")

            # trigger a stack change to reload the output devices
            self._application.globalContainerStackChanged.emit()
        else:
            Logger.log("d", "no config to delete")

    @pyqtSlot(str, result=bool)
    def validUrl(self, newUrl):
        if newUrl.startswith('\\\\'):
            # no UNC paths
            return False
        if not re.match('^https?://.', newUrl):
            # missing https?://
            return False
        if '@' in newUrl:
            # @ is probably HTTP basic auth, which is a separate setting
            return False

        return True
