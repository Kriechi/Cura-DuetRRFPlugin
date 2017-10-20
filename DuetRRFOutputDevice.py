import os.path
from io import StringIO
from time import time, sleep
import datetime
import base64
import urllib
import json

from PyQt5 import QtNetwork
from PyQt5.QtCore import QFile, QUrl, QCoreApplication, QByteArray, QTimer
from PyQt5.QtGui import QDesktopServices

from UM.Application import Application
from UM.Logger import Logger
from UM.Message import Message
from UM.OutputDevice.OutputDevice import OutputDevice
from UM.OutputDevice import OutputDeviceError

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


from enum import Enum
class OutputStage(Enum):
    ready = 0
    writing = 1

class DeviceType(Enum):
    print = 0
    simulate = 1
    upload = 2


class DuetRRFOutputDevice(OutputDevice):
    def __init__(
            self,
            name="DuetRRF",
            url="http://printer.local",
            duet_password="reprap",
            http_user=None,
            http_password=None,
            device_type=DeviceType.print
    ):
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

        if not url.endswith('/'):
            url += '/'
        self._url = url

        self._duet_password = duet_password
        self._http_user = http_user
        self._http_password = http_password

        self._qnam = QtNetwork.QNetworkAccessManager()

        self._stream = None
        self._cleanupRequest()

    def _timestamp(self):
        return ("time", datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))

    def _send(self, command, query, next_stage=None, data=None):
        enc_query = urllib.parse.urlencode(query)
        self._request = QtNetwork.QNetworkRequest(QUrl(self._url + "rr_" + command + "?" + enc_query))
        self._request.setRawHeader(b'User-Agent', b'Cura Plugin DuetRRF')
        self._request.setRawHeader(b'Accept', b'application/json, text/javascript')
        self._request.setRawHeader(b'Connection', b'keep-alive')

        Logger.log("d", "%s %s %s" % (self._http_user, self._http_password, self._duet_password))
        if self._http_user and self._http_password:
            self._request.setRawHeader(b'Authorization', b'Basic ' + base64.b64encode("{}:{}".format(self._http_user, self._http_password).encode()))

        if data:
            self._request.setRawHeader(b'Content-Type', b'application/octet-stream')
            self._reply = self._qnam.post(self._request, data)
            self._reply.uploadProgress.connect(self._onUploadProgress)
        else:
            self._reply = self._qnam.get(self._request)

        self._reply.finished.connect(next_stage)
        self._reply.error.connect(self._onNetworkError)

    def requestWrite(self, node, fileName = None, *args, **kwargs):
        if self._stage != OutputStage.ready:
            raise OutputDeviceError.DeviceBusyError()

        if fileName:
            fileName = os.path.splitext(fileName)[0] + '.gcode'
        else:
            fileName = "%s.gcode" % Application.getInstance().getPrintInformation().jobName
        self._fileName = fileName

        # create the temp file for the gcode
        self._stream = StringIO()
        self._stage = OutputStage.writing
        self.writeStarted.emit(self)

        # show a progress message
        self._message = Message(catalog.i18nc("@info:progress", "Uploading to {}").format(self._name), 0, False, -1)
        self._message.show()

        # send all the gcode to self._stream
        gcode = getattr(Application.getInstance().getController().getScene(), "gcode_list")
        lines = len(gcode)
        nextYield = time() + 0.05
        i = 0
        for line in gcode:
            i += 1
            self._stream.write(line)
            if time() > nextYield:
                self._onProgress(i / lines)
                QCoreApplication.processEvents()
                nextYield = time() + 0.05

        # start
        self._send('connect', [("password", self._duet_password), self._timestamp()], self.onConnected)

    def onConnected(self):
        self._stream.seek(0)
        self._postData = QByteArray()
        self._postData.append(self._stream.getvalue().encode())
        self._send('upload', [("name", "0:/gcodes/" + self._fileName), self._timestamp()], self.onUploadDone, self._postData)

    def onUploadDone(self):
        self._stream.close()
        self.stream = None

        if self._device_type == DeviceType.simulate:
            if self._message:
                self._message.hide()
            text = catalog.i18nc("@info:progress", "Simulating print on {}").format(self._name)
            self._message = Message(text, 0, False, -1)
            self._message.show()

            self._send('gcode', [("gcode", "M37 S1")], self.onReadyToPrint)
        elif self._device_type == DeviceType.print:
            self.onReadyToPrint()
        elif self._device_type == DeviceType.upload:
            if self._message:
                self._message.hide()
            text = "Uploaded file {} to {}.".format(os.path.basename(self._fileName), self._name)
            self._message = Message(catalog.i18nc("@info:status", text))
            self._message.addAction("open_browser", catalog.i18nc("@action:button", "Open Browser"), "globe", catalog.i18nc("@info:tooltip", "Open browser to DuetWebControl."))
            self._message.actionTriggered.connect(self._onMessageActionTriggered)
            self._message.show()

            self.writeSuccess.emit(self)
            self._cleanupRequest()

    def onReadyToPrint(self):
        self._send('gcode', [("gcode", "M32 /gcodes/" + self._fileName)], self.onPrintStarted)

    def onPrintStarted(self):
        if self._device_type == DeviceType.simulate:
            self.onCheckStatus()
        else:
            if self._message:
                self._message.hide()

            text = "Print started on {} with file {}".format(self._name, self._fileName)
            self._message = Message(catalog.i18nc("@info:status", text))
            self._message.addAction("open_browser", catalog.i18nc("@action:button", "Open Browser"), "globe", catalog.i18nc("@info:tooltip", "Open browser to DuetWebControl."))
            self._message.actionTriggered.connect(self._onMessageActionTriggered)
            self._message.show()

            self.writeSuccess.emit(self)
            self._cleanupRequest()

    def onSimulatedPrintFinished(self):
        self._send('gcode', [("gcode", "M37 S0")], self.onSimulationStopped)

    def onCheckStatus(self):
        self._send('status', [("type", "3")], self.onStatusReceived)

    def onStatusReceived(self):
        status_bytes = bytes(self._reply.readAll())
        Logger.log("d", status_bytes)

        status = json.loads(status_bytes.decode())
        if status["status"] == "P":
            # still printing
            if self._message and "fractionPrinted" in status:
                self._message.setProgress(float(status["fractionPrinted"]))
            QTimer.singleShot(1000, self.onCheckStatus)
        else:
            # not printing any more (or error?)
            self.onSimulatedPrintFinished()

    def onSimulationStopped(self):
        self._send('gcode', [("gcode", "M37")], self.onReporting)

    def onReporting(self):
        self._send('reply', [], self.onReported)

    def onReported(self):
        if self._message:
            self._message.hide()

        reply_body = bytes(self._reply.readAll()).decode()
        text = "Simulation performed on {} with file {}:\n{}".format(self._name, self._fileName, reply_body)
        self._message = Message(catalog.i18nc("@info:status", text))
        self._message.addAction("open_browser", catalog.i18nc("@action:button", "Open Browser"), "globe", catalog.i18nc("@info:tooltip", "Open browser to DuetWebControl."))
        self._message.actionTriggered.connect(self._onMessageActionTriggered)
        self._message.show()

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
        message = Message(catalog.i18nc("@info:status", "There was a network error: {} {}").format(errorCode, errorString))
        message.show()

    def _cancelUpload(self):
        if self._message:
            self._message.hide()
        self._message = None
        self._reply.abort()
