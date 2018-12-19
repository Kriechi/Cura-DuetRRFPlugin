import os.path
import datetime
import base64
import urllib
import json
from io import StringIO
from time import time, sleep
from typing import cast

from PyQt5 import QtNetwork
from PyQt5.QtCore import QFile, QUrl, QObject, QCoreApplication, QByteArray, QTimer, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtQml import QQmlComponent, QQmlContext

from UM.Application import Application
from UM.Logger import Logger
from UM.Message import Message
from UM.Mesh.MeshWriter import MeshWriter
from UM.PluginRegistry import PluginRegistry
from UM.OutputDevice.OutputDevice import OutputDevice
from UM.OutputDevice import OutputDeviceError

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

from cura.CuraApplication import CuraApplication


from enum import Enum
class OutputStage(Enum):
    ready = 0
    writing = 1

class DeviceType(Enum):
    print = 0
    simulate = 1
    upload = 2


class DuetRRFOutputDevice(OutputDevice):
    def __init__(self, name, url, duet_password, http_user, http_password, device_type):
        self._device_type = device_type
        if device_type == DeviceType.print:
            description = catalog.i18nc("@action:button", "Print on {0}").format(name)
            name_id = name + "-print"
            priority = 30
        elif device_type == DeviceType.simulate:
            description = catalog.i18nc("@action:button", "Simulate on {0}").format(name)
            name_id = name + "-simulate"
            priority = 20
        elif device_type == DeviceType.upload:
            description = catalog.i18nc("@action:button", "Upload to {0}").format(name)
            name_id = name + "-upload"
            priority = 10
        else:
            assert False

        super().__init__(name_id)
        self.setShortDescription(description)
        self.setDescription(description)
        self.setPriority(priority)

        self._stage = OutputStage.ready
        self._name = name
        self._name_id = name_id
        self._device_type = device_type
        self._url = url
        self._duet_password = duet_password
        self._http_user = http_user
        self._http_password = http_password

        Logger.log("d", self._name_id + " | New DuetRRFOutputDevice created")
        Logger.log("d", self._name_id + " | URL: " + self._url)
        Logger.log("d", self._name_id + " | Duet password: " + ("set." if self._duet_password else "empty."))
        Logger.log("d", self._name_id + " | HTTP Basic Auth user: " + ("set." if self._http_user else "empty."))
        Logger.log("d", self._name_id + " | HTTP Basic Auth password: " + ("set." if self._http_password else "empty."))

        self._qnam = QtNetwork.QNetworkAccessManager()

        self._stream = None
        self._cleanupRequest()

        if hasattr(self, '_message'):
            self._message.hide()
        self._message = None


    def _timestamp(self):
        return ("time", datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))

    def _send(self, command, query=None, next_stage=None, data=None):
        enc_query = urllib.parse.urlencode(query or dict())
        if enc_query:
            command += '?' + enc_query
        self._request = QtNetwork.QNetworkRequest(QUrl(self._url + "rr_" + command))
        self._request.setRawHeader(b'User-Agent', b'Cura Plugin DuetRRF')
        self._request.setRawHeader(b'Accept', b'application/json, text/javascript')
        self._request.setRawHeader(b'Connection', b'keep-alive')

        if self._http_user and self._http_password:
            self._request.setRawHeader(b'Authorization', b'Basic ' + base64.b64encode("{}:{}".format(self._http_user, self._http_password).encode()))

        if data:
            self._request.setRawHeader(b'Content-Type', b'application/octet-stream')
            self._reply = self._qnam.post(self._request, data)
            self._reply.uploadProgress.connect(self._onUploadProgress)
        else:
            self._reply = self._qnam.get(self._request)

        if next_stage:
            self._reply.finished.connect(next_stage)
        self._reply.error.connect(self._onNetworkError)

    def requestWrite(self, node, fileName=None, *args, **kwargs):
        if self._stage != OutputStage.ready:
            raise OutputDeviceError.DeviceBusyError()

        if fileName:
            fileName = os.path.splitext(fileName)[0] + '.gcode'
        else:
            fileName = "%s.gcode" % Application.getInstance().getPrintInformation().jobName
        self._fileName = fileName

        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'qml', 'UploadFilename.qml')
        self._dialog = CuraApplication.getInstance().createQmlComponent(path, {"manager": self})
        self._dialog.textChanged.connect(self.onFilenameChanged)
        self._dialog.accepted.connect(self.onFilenameAccepted)
        self._dialog.show()
        self._dialog.findChild(QObject, "nameField").setProperty('text', self._fileName)
        self._dialog.findChild(QObject, "nameField").select(0, len(self._fileName) - 6)
        self._dialog.findChild(QObject, "nameField").setProperty('focus', True)

    def onFilenameChanged(self):
        fileName = self._dialog.findChild(QObject, "nameField").property('text')
        self._dialog.setProperty('validName', len(fileName) > 0)

    def onFilenameAccepted(self):
        self._fileName = self._dialog.findChild(QObject, "nameField").property('text')
        if not self._fileName.endswith('.gcode') and '.' not in self._fileName:
            self._fileName += '.gcode'
        Logger.log("d", self._name_id + " | Filename set to: " + self._fileName)

        self._dialog.deleteLater()

        # create the temp file for the gcode
        self._stream = StringIO()
        self._stage = OutputStage.writing
        self.writeStarted.emit(self)

        # show a progress message
        self._message = Message(catalog.i18nc("@info:progress", "Uploading to {}").format(self._name), 0, False, -1)
        self._message.show()

        Logger.log("d", self._name_id + " | Loading gcode...")

        # get the g-code through the GCodeWrite plugin
        # this serializes the actual scene and should produce the same output as "Save to File"
        gcode_writer = cast(MeshWriter, PluginRegistry.getInstance().getPluginObject("GCodeWriter"))
        success = gcode_writer.write(self._stream, None)
        if not success:
            Logger.log("e", "GCodeWrite failed.")
            return

        # start
        Logger.log("d", self._name_id + " | Connecting...")
        self._send('connect', [("password", self._duet_password), self._timestamp()], self.onUploadReady)

    def onUploadReady(self):
        if self._stage != OutputStage.writing:
            return

        Logger.log("d", self._name_id + " | Uploading...")
        self._stream.seek(0)
        self._postData = QByteArray()
        self._postData.append(self._stream.getvalue().encode())
        self._send('upload', [("name", "0:/gcodes/" + self._fileName), self._timestamp()], self.onUploadDone, self._postData)

    def onUploadDone(self):
        if self._stage != OutputStage.writing:
            return

        Logger.log("d", self._name_id + " | Upload done")

        self._stream.close()
        self.stream = None

        if self._device_type == DeviceType.simulate:
            Logger.log("d", self._name_id + " | Simulating...")
            if self._message:
                self._message.hide()
            self._message = Message(catalog.i18nc("@info:progress", "Simulating print on {}...\nPLEASE CLOSE DWC AND DO NOT INTERACT WITH THE PRINTER!").format(self._name), 0, False, -1)
            self._message.show()

            self._send('gcode', [("gcode", 'M37 P"0:/gcodes/' + self._fileName + '"')], self.onSimulationPrintStarted)
        elif self._device_type == DeviceType.print:
            self.onReadyToPrint()
        elif self._device_type == DeviceType.upload:
            self._send('disconnect')
            if self._message:
                self._message.hide()
            text = "Uploaded file {} to {}.".format(os.path.basename(self._fileName), self._name)
            self._message = Message(catalog.i18nc("@info:status", text), 0, False)
            self._message.addAction("open_browser", catalog.i18nc("@action:button", "Open Browser"), "globe", catalog.i18nc("@info:tooltip", "Open browser to DuetWebControl."))
            self._message.actionTriggered.connect(self._onMessageActionTriggered)
            self._message.show()

            self.writeSuccess.emit(self)
            self._cleanupRequest()

    def onReadyToPrint(self):
        if self._stage != OutputStage.writing:
            return

        Logger.log("d", self._name_id + " | Ready to print")
        self._send('gcode', [("gcode", 'M32 "0:/gcodes/' + self._fileName + '"')], self.onPrintStarted)

    def onPrintStarted(self):
        if self._stage != OutputStage.writing:
            return

        Logger.log("d", self._name_id + " | Print started")

        self._send('disconnect')
        if self._message:
            self._message.hide()
        text = "Print started on {} with file {}".format(self._name, self._fileName)
        self._message = Message(catalog.i18nc("@info:status", text), 0, False)
        self._message.addAction("open_browser", catalog.i18nc("@action:button", "Open Browser"), "globe", catalog.i18nc("@info:tooltip", "Open browser to DuetWebControl."))
        self._message.actionTriggered.connect(self._onMessageActionTriggered)
        self._message.show()

        self.writeSuccess.emit(self)
        self._cleanupRequest()

    def onSimulationPrintStarted(self):
        if self._stage != OutputStage.writing:
            return

        Logger.log("d", self._name_id + " | Simulation print started for file " + self._fileName)

        # give it some to start the simulation
        QTimer.singleShot(15000, self.onCheckStatus)

    def onCheckStatus(self):
        if self._stage != OutputStage.writing:
            return

        Logger.log("d", self._name_id + " | Checking status...")

        self._send('status', [("type", "3")], self.onStatusReceived)

    def onStatusReceived(self):
        if self._stage != OutputStage.writing:
            return

        reply_body = bytes(self._reply.readAll()).decode()
        Logger.log("d", self._name_id + " | Status received | " + reply_body)

        status = json.loads(reply_body)
        if status["status"] in ['P', 'M'] :
            # still simulating
            # RRF 1.21RC2 and earlier used P while simulating
            # RRF 1.21RC3 and later uses M while simulating
            if self._message and "fractionPrinted" in status:
                self._message.setProgress(float(status["fractionPrinted"]))
            QTimer.singleShot(5000, self.onCheckStatus)
        else:
            Logger.log("d", self._name_id + " | Simulation print finished")
            self._send('reply', [], self.onReported)

    def onReported(self):
        if self._stage != OutputStage.writing:
            return

        reply_body = bytes(self._reply.readAll()).decode().strip()
        Logger.log("d", self._name_id + " | Reported | " + reply_body)

        if self._message:
            self._message.hide()

        text = "Simulation finished on {}:\n\n{}".format(self._name, reply_body)
        self._message = Message(catalog.i18nc("@info:status", text), 0, False)
        self._message.addAction("open_browser", catalog.i18nc("@action:button", "Open Browser"), "globe", catalog.i18nc("@info:tooltip", "Open browser to DuetWebControl."))
        self._message.actionTriggered.connect(self._onMessageActionTriggered)
        self._message.show()

        self._send('disconnect')
        self.writeSuccess.emit(self)
        self._cleanupRequest()

    def _onProgress(self, progress):
        if self._message:
            self._message.setProgress(progress)
        self.writeProgress.emit(self, progress)

    def _cleanupRequest(self):
        self._reply = None
        self._request = None
        if self._stream:
            self._stream.close()
        self._stream = None
        self._stage = OutputStage.ready
        self._fileName = None

    def _onMessageActionTriggered(self, message, action):
        if action == "open_browser":
            QDesktopServices.openUrl(QUrl(self._url))
            if self._message:
                self._message.hide()
            self._message = None

    def _onUploadProgress(self, bytesSent, bytesTotal):
        if bytesTotal > 0:
            self._onProgress(int(bytesSent * 100 / bytesTotal))

    def _onNetworkError(self, errorCode):
        Logger.log("e", "_onNetworkError: %s", repr(errorCode))
        if self._message:
            self._message.hide()
        self._message = None

        if self._reply:
            errorString = self._reply.errorString()
        else:
            errorString = ''
        message = Message(catalog.i18nc("@info:status", "There was a network error: {} {}").format(errorCode, errorString), 0, False)
        message.show()

        self.writeError.emit(self)
        self._cleanupRequest()
