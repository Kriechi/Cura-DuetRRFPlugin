import os
import json
import re

from PyQt5.QtCore import QObject, pyqtSlot

from cura.CuraApplication import CuraApplication
from cura.MachineAction import MachineAction

from UM.Logger import Logger
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


class DuetRRFAction(MachineAction):
    def __init__(self, parent: QObject = None) -> None:
        super().__init__("DuetRRFAction", catalog.i18nc("@action", "Connect Duet RepRapFirmware"))

        self._qml_url = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'qml', 'DuetRRFAction.qml')
        self._application = CuraApplication.getInstance()

        ContainerRegistry.getInstance().containerAdded.connect(self._onContainerAdded)

    def _onContainerAdded(self, container: "ContainerInterface") -> None:
        # Add this action as a supported action to all machine definitions
        if (
            isinstance(container, DefinitionContainer) and
            container.getMetaDataEntry("type") == "machine" and
            container.getMetaDataEntry("supports_usb_connection")
        ):
            self._application.getMachineActionManager().addSupportedAction(container.getId(), self.getKey())

    @pyqtSlot(result=str)
    def printerSettingUrl(self):
        global_container_stack = self._application.getGlobalContainerStack()
        if global_container_stack:
            return global_container_stack.getMetaDataEntry("duetrrf_url", "")
        return ""

    @pyqtSlot(result=str)
    def printerSettingDuetPassword(self):
        global_container_stack = self._application.getGlobalContainerStack()
        if global_container_stack:
            return global_container_stack.getMetaDataEntry("duetrrf_duet_password", "")
        return ""

    @pyqtSlot(result=str)
    def printerSettingHTTPUser(self):
        global_container_stack = self._application.getGlobalContainerStack()
        if global_container_stack:
            return global_container_stack.getMetaDataEntry("duetrrf_http_user", "")
        return ""

    @pyqtSlot(result=str)
    def printerSettingHTTPPassword(self):
        global_container_stack = self._application.getGlobalContainerStack()
        if global_container_stack:
            return global_container_stack.getMetaDataEntry("duetrrf_http_password", "")
        return ""

    @pyqtSlot(str, str, str, str)
    def testAndSave(self, url, duet_password, http_user, http_password):
        if not url.endswith('/'):
            url += '/'

        global_container_stack = self._application.getGlobalContainerStack()
        if not global_container_stack:
            Logger.log("e", "failed to save config: global_container_stack is missing")
            return

        global_container_stack.setMetaDataEntry("duetrrf", True)
        global_container_stack.setMetaDataEntry("duetrrf_url", url)
        global_container_stack.setMetaDataEntry("duetrrf_duet_password", duet_password)
        global_container_stack.setMetaDataEntry("duetrrf_http_user", http_user)
        global_container_stack.setMetaDataEntry("duetrrf_http_password", http_password)
        Logger.log("d", "config saved: " + global_container_stack.getName())

    @pyqtSlot()
    def deleteConfig(self):
        global_container_stack = self._application.getGlobalContainerStack()
        if not global_container_stack:
            Logger.log("e", "failed to delete config: global_container_stack is missing")
            return

        global_container_stack.removeMetaDataEntry("duetrrf")
        global_container_stack.removeMetaDataEntry("duetrrf_url")
        global_container_stack.removeMetaDataEntry("duetrrf_duet_password")
        global_container_stack.removeMetaDataEntry("duetrrf_http_user")
        global_container_stack.removeMetaDataEntry("duetrrf_http_password")
        Logger.log("d", "config deleted: " + global_container_stack.getName())

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
