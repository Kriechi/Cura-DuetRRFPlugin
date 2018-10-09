import re
import os.path
import json

from PyQt5.QtCore import QObject, QUrl, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt5.QtQml import QQmlComponent, QQmlContext

from UM.Message import Message
from UM.Logger import Logger

from UM.Preferences import Preferences
from UM.Extension import Extension
from UM.PluginRegistry import PluginRegistry
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin

from . import DuetRRFOutputDevice
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

from cura.CuraApplication import CuraApplication


class DuetRRFPlugin(QObject, Extension, OutputDevicePlugin):
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        Extension.__init__(self)
        OutputDevicePlugin.__init__(self)
        self.addMenuItem(catalog.i18n("DuetRRF Connections"), self.showSettingsDialog)
        self._dialogs = {}
        self._dialogView = None

        Preferences.getInstance().addPreference("duetrrf/instances", json.dumps({}))
        self._instances = json.loads(Preferences.getInstance().getValue("duetrrf/instances"))

    def start(self):
        manager = self.getOutputDeviceManager()
        for name, instance in self._instances.items():
            manager.addOutputDevice(DuetRRFOutputDevice.DuetRRFOutputDevice(name, instance["url"], instance["duet_password"], instance["http_user"], instance["http_password"], device_type=DuetRRFOutputDevice.DeviceType.print))
            manager.addOutputDevice(DuetRRFOutputDevice.DuetRRFOutputDevice(name, instance["url"], instance["duet_password"], instance["http_user"], instance["http_password"], device_type=DuetRRFOutputDevice.DeviceType.simulate))
            manager.addOutputDevice(DuetRRFOutputDevice.DuetRRFOutputDevice(name, instance["url"], instance["duet_password"], instance["http_user"], instance["http_password"], device_type=DuetRRFOutputDevice.DeviceType.upload))

    def stop(self):
        manager = self.getOutputDeviceManager()
        for name in self._instances.keys():
            manager.removeOutputDevice(name + "-print")
            manager.removeOutputDevice(name + "-simulate")
            manager.removeOutputDevice(name + "-upload")

    def _createDialog(self, qml):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'qml', qml)
        dialog = CuraApplication.getInstance().createQmlComponent(path, {"manager": self})
        return dialog

    def _showDialog(self, qml):
        if not qml in self._dialogs:
            self._dialogs[qml] = self._createDialog(qml)
        self._dialogs[qml].show()

    def showSettingsDialog(self):
        self._showDialog("DuetRRFPlugin.qml")

    serverListChanged = pyqtSignal()
    @pyqtProperty("QVariantList", notify=serverListChanged)
    def serverList(self):
        return list(self._instances.keys())

    @pyqtSlot(str, result=str)
    def instanceUrl(self, name):
        if name in self._instances.keys():
            return self._instances[name]["url"]
        return None

    @pyqtSlot(str, result=str)
    def instanceDuetPassword(self, name):
        if name in self._instances.keys():
            return self._instances[name]["duet_password"]
        return None

    @pyqtSlot(str, result=str)
    def instanceHTTPUser(self, name):
        if name in self._instances.keys():
            return self._instances[name]["http_user"]
        return None

    @pyqtSlot(str, result=str)
    def instanceHTTPPassword(self, name):
        if name in self._instances.keys():
            return self._instances[name]["http_password"]
        return None

    @pyqtSlot(str, str, str, str, str, str)
    def saveInstance(self, oldName, name, url, duet_password, http_user, http_password):
        manager = self.getOutputDeviceManager()
        if oldName and oldName != name:
            self.removeInstance(oldName)
        if not url.endswith('/'):
            url += '/'
        self._instances[name] = {
            "url": url,
            "duet_password": duet_password,
            "http_user": http_user,
            "http_password": http_password
        }
        manager.addOutputDevice(DuetRRFOutputDevice.DuetRRFOutputDevice(name, url, duet_password, http_user, http_password, device_type=DuetRRFOutputDevice.DeviceType.print))
        manager.addOutputDevice(DuetRRFOutputDevice.DuetRRFOutputDevice(name, url, duet_password, http_user, http_password, device_type=DuetRRFOutputDevice.DeviceType.simulate))
        manager.addOutputDevice(DuetRRFOutputDevice.DuetRRFOutputDevice(name, url, duet_password, http_user, http_password, device_type=DuetRRFOutputDevice.DeviceType.upload))
        Preferences.getInstance().setValue("duetrrf/instances", json.dumps(self._instances))
        self.serverListChanged.emit()
        Logger.log("d", "Instance saved: " + name)

    @pyqtSlot(str)
    def removeInstance(self, name):
        self.getOutputDeviceManager().removeOutputDevice(name + "-print")
        self.getOutputDeviceManager().removeOutputDevice(name + "-simulate")
        self.getOutputDeviceManager().removeOutputDevice(name + "-upload")
        del self._instances[name]
        Preferences.getInstance().setValue("duetrrf/instances", json.dumps(self._instances))
        self.serverListChanged.emit()
        Logger.log("d", "Instance removed: " + name)

    @pyqtSlot(str, str, result = bool)
    def validName(self, oldName, newName):
        if not newName:
            # empty string isn't allowed
            return False
        if oldName == newName:
            # if name hasn't changed, not a duplicate, just no rename
            return True

        # duplicates not allowed
        return (not newName in self._instances.keys())

    @pyqtSlot(str, str, result = bool)
    def validUrl(self, oldName, newUrl):
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
