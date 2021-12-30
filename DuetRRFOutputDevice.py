import array
import os.path
import datetime
import base64
import urllib
import json
from io import StringIO
from typing import cast
from enum import Enum

from PyQt5 import QtNetwork, QtCore
from PyQt5.QtNetwork import QNetworkReply

from PyQt5.QtCore import QFile, QUrl, QObject, QCoreApplication, QByteArray, QTimer, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QDesktopServices, QImage
from PyQt5.QtQml import QQmlComponent, QQmlContext

from cura.CuraApplication import CuraApplication
from cura.Snapshot import Snapshot
from cura.PreviewPass import PreviewPass

from UM.Application import Application
from UM.Math.Matrix import Matrix
from UM.Math.Vector import Vector
from UM.Scene.Camera import Camera
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator

from UM.Application import Application
from UM.Logger import Logger
from UM.Message import Message
from UM.Mesh.MeshWriter import MeshWriter
from UM.PluginRegistry import PluginRegistry
from UM.OutputDevice.OutputDevice import OutputDevice
from UM.OutputDevice import OutputDeviceError
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

from .qoi import QOIEncoder


class OutputStage(Enum):
    ready = 0
    writing = 1

class DuetRRFDeviceType(Enum):
    print = 0
    simulate = 1
    upload = 2


class DuetRRFConfigureOutputDevice(OutputDevice):
    def __init__(self) -> None:
        super().__init__("duetrrf-configure")
        self.setShortDescription("DuetRRF Plugin")
        self.setDescription("Configure Duet RepRapFirmware...")
        self.setPriority(0)

    def requestWrite(self, node, fileName=None, *args, **kwargs):
        msg = (
            "To configure your Duet RepRapFirmware printer go to:\n"
            "→ Cura Preferences\n"
            "→ Printers\n"
            "→ activate and select your printer\n"
            "→ click on 'Connect Duet RepRapFirmware'\n"
        )
        message = Message(
            msg,
            lifetime=0,
            title="Configure DuetRRF in Cura Preferences!",
        )
        message.show()
        self.writeSuccess.emit(self)


class DuetRRFOutputDevice(OutputDevice):
    def __init__(self, settings, device_type):
        self._name_id = "duetrrf-{}".format(device_type.name)
        super().__init__(self._name_id)

        self._url = settings["url"]
        self._duet_password = settings["duet_password"]
        self._http_user = settings["http_user"]
        self._http_password = settings["http_password"]

        self.application = CuraApplication.getInstance()
        global_container_stack = self.application.getGlobalContainerStack()
        self._name = global_container_stack.getName()

        self._device_type = device_type
        if device_type == DuetRRFDeviceType.print:
            description = catalog.i18nc("@action:button", "Print on {0}").format(self._name)
            priority = 30
        elif device_type == DuetRRFDeviceType.simulate:
            description = catalog.i18nc("@action:button", "Simulate on {0}").format(self._name)
            priority = 20
        elif device_type == DuetRRFDeviceType.upload:
            description = catalog.i18nc("@action:button", "Upload to {0}").format(self._name)
            priority = 10
        else:
            assert False

        self.setShortDescription(description)
        self.setDescription(description)
        self.setPriority(priority)

        self._stage = OutputStage.ready
        self._device_type = device_type
        self._stream = None
        self._message = None

        self._use_rrf_http_api = True # by default we try to connect to the RRF HTTP API via rr_connect

        Logger.log("d",
            "New {} DuetRRFOutputDevice created | URL: {} | Duet password: {} | HTTP Basic Auth: user:{}, password:{}".format(
            self._name_id,
            self._url,
            "set" if self._duet_password else "<empty>",
            self._http_user if self._http_user else "<empty>",
            "set" if self._http_password else "<empty>",
        ))

        self._resetState()

    def _timestamp(self):
        return ("time", datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))

    def _send(self, command, query=None, next_stage=None, data=None, on_error=None, method='POST'):
        url = self._url + command

        if not query:
            query = dict()
        enc_query = urllib.parse.urlencode(query, quote_via=urllib.parse.quote)
        if enc_query:
            url += '?' + enc_query

        headers = {
            'User-Agent': 'Cura Plugin DuetRRF',
            'Accept': 'application/json, text/javascript',
            'Connection': 'keep-alive',
        }

        if self._http_user and self._http_password:
            auth = "{}:{}".format(self._http_user, self._http_password).encode()
            headers['Authorization'] = 'Basic ' + base64.b64encode(auth)

        if data:
            headers['Content-Type'] = 'application/octet-stream'
            if method == 'PUT':
                self.application.getHttpRequestManager().put(
                    url,
                    headers,
                    data,
                    callback=next_stage,
                    error_callback=on_error if on_error else self._onNetworkError,
                    upload_progress_callback=self._onUploadProgress,
                )
            else:
                self.application.getHttpRequestManager().post(
                    url,
                    headers,
                    data,
                    callback=next_stage,
                    error_callback=on_error if on_error else self._onNetworkError,
                    upload_progress_callback=self._onUploadProgress,
                )
        else:
            self.application.getHttpRequestManager().get(
                url,
                headers,
                callback=next_stage,
                error_callback=on_error if on_error else self._onNetworkError,
            )

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

    def create_thumbnail(self, width, height):
        scene = Application.getInstance().getController().getScene()
        active_camera = scene.getActiveCamera()
        render_width, render_height = active_camera.getWindowSize()
        render_width = int(render_width)
        render_height = int(render_height)
        Logger.log("d", f"Found active camera with {render_width=} {render_height=}")

        QCoreApplication.processEvents()

        satisfied = False
        zooms = 0
        preview_pass = PreviewPass(render_width, render_height)
        size = None
        fovy = 30
        while not satisfied and zooms < 5:
            preview_pass.render()
            pixel_output = preview_pass.getOutput().convertToFormat(QImage.Format_ARGB32)
            pixel_output.save(os.path.expanduser(f"~/Downloads/foo-a-zoom-{zooms}.png"), "PNG")

            min_x, max_x, min_y, max_y = Snapshot.getImageBoundaries(pixel_output)
            size = max((max_x - min_x) / render_width, (max_y - min_y) / render_height)
            if size > 0.5 or satisfied:
                satisfied = True
            else:
                # make it big and allow for some empty space around
                zooms += 1
                fovy *= 0.75
                projection_matrix = Matrix()
                projection_matrix.setPerspective(fovy, render_width / render_height, 1, 500)
                active_camera.setProjectionMatrix(projection_matrix)

            Logger.log("d", f"Rendered thumbnail: {zooms=}, {size=}, {min_x=}, {max_x=}, {min_y=}, {max_y=}, {fovy=}")

        # crop to content
        pixel_output = pixel_output.copy(min_x, min_y, max_x - min_x, max_y - min_y)
        Logger.log("d", f"Cropped thumbnail to {min_x}, {min_y}, {max_x - min_x}, {max_y - min_y}.")
        pixel_output.save(os.path.expanduser("~/Downloads/foo-b-cropped.png"), "PNG")

        # scale to desired width and height
        pixel_output = pixel_output.scaled(
            width, height,
            aspectRatioMode=QtCore.Qt.KeepAspectRatio,
            transformMode=QtCore.Qt.SmoothTransformation
        )
        Logger.log("d", f"Scaled thumbnail to {width=}, {height=}.")
        pixel_output.save(os.path.expanduser("~/Downloads/foo-c-scaled.png"), "PNG")

        # center image within desired width and height if one dimension is too small
        if pixel_output.width() < width:
            d = (width - pixel_output.width()) / 2.
            pixel_output = pixel_output.copy(-d, 0, width, pixel_output.height())
            Logger.log("d", f"Centered thumbnail horizontally {d=}.")
        if pixel_output.height() < height:
            d = (height - pixel_output.height()) / 2.
            pixel_output = pixel_output.copy(0, -d, pixel_output.width(), height)
            Logger.log("d", f"Centered thumbnail vertically {d=}.")
        pixel_output.save(os.path.expanduser("~/Downloads/foo-d-aspect-fixed.png"), "PNG")

        Logger.log("d", "Successfully created thumbnail of scene.")
        return pixel_output

    def embed_thumbnail(self):
        Logger.log("d", "Creating thumbnail in QOI format to include in gcode file...")
        try:
            # thumbnail = Snapshot.snapshot(width, height)

            # PanelDue: 480×272 (4.3" displays) or 800×480 pixels (5" and 7" displays)

            width = 320
            height = 320
            thumbnail = self.create_thumbnail(width, height)

            # https://qoiformat.org/qoi-specification.pdf
            pixels = [thumbnail.pixel(x, y) for y in range(height) for x in range(width)]
            pixels = [(unsigned_p ^ (1 << 31)) - (1 << 31) for unsigned_p in pixels]
            encoder = QOIEncoder()
            r = encoder.encode(width, height, pixels, alpha=thumbnail.hasAlphaChannel(), linear_colorspace=False)
            if not r:
                raise ValueError("image size unsupported")

            Logger.log("d", "Successfully encoded thumbnail in QOI format.")

            thumbnail.save(os.path.expanduser("~/Downloads/snapshot.png"), "PNG")
            with open(os.path.expanduser("~/Downloads/snapshot.qoi"), "wb") as f:
                actual_size = encoder.get_encoded_size()
                f.write(encoder.get_encoded()[:actual_size])
        except Exception as e:
            Logger.log("d", "failed to create snapshot: " + str(e))
            import traceback
            Logger.log("d", traceback.format_stack())
            # continue without the QOI snapshot

    def onFilenameChanged(self):
        fileName = self._dialog.findChild(QObject, "nameField").property('text').strip()

        forbidden_characters = "\"'´`<>()[]?*\,;:&%#$!"
        for forbidden_character in forbidden_characters:
            if forbidden_character in fileName:
                self._dialog.setProperty('validName', False)
                self._dialog.setProperty('validationError', 'Filename cannot contain {}'.format(forbidden_characters))
                return

        if fileName == '.' or fileName == '..':
            self._dialog.setProperty('validName', False)
            self._dialog.setProperty('validationError', 'Filename cannot be "." or ".."')
            return

        self._dialog.setProperty('validName', len(fileName) > 0)
        self._dialog.setProperty('validationError', 'Filename too short')

    def onFilenameAccepted(self):
        self._fileName = self._dialog.findChild(QObject, "nameField").property('text').strip()
        if not self._fileName.endswith('.gcode') and '.' not in self._fileName:
            self._fileName += '.gcode'
        Logger.log("d", "Filename set to: " + self._fileName)

        self._dialog.deleteLater()

        # create the temp file for the gcode
        self._stream = StringIO()
        self._stage = OutputStage.writing
        self.writeStarted.emit(self)

        # show a progress message
        self._message = Message(
            "Rendering thumbnail image...",
            lifetime=0,
            dismissable=False,
            progress=-1,
            title="DuetRRF: " + self._name,
        )
        self._message.show()

        # generate model thumbnail and embedd in gcode file
        self.embed_thumbnail()

        self._message.setText("Uploading {} ...".format(self._fileName))

        # get the g-code through the GCodeWrite plugin
        # this serializes the actual scene and should produce the same output as "Save to File"
        Logger.log("d", "Loading gcode...")
        gcode_writer = cast(MeshWriter, PluginRegistry.getInstance().getPluginObject("GCodeWriter"))
        success = gcode_writer.write(self._stream, None)
        if not success:
            Logger.log("e", "GCodeWrite failed.")
            return

        # start
        Logger.log("d", "Connecting...")
        self._send('rr_connect',
            query=[("password", self._duet_password), self._timestamp()],
            next_stage=self.onUploadReady,
            on_error=self._check_duet3_sbc,
        )

    def _check_duet3_sbc(self, reply, error):
        Logger.log("d", "rr_connect failed with error " + str(error))
        if error == QNetworkReply.ContentNotFoundError:
            Logger.log("d", "error indicates Duet3+SBC - let's try the DuetSoftwareFramework API instead...")
            self._use_rrf_http_api = False  # let's try the newer DuetSoftwareFramework for Duet3+SBC API instead
            self._send('machine/status',
                next_stage=self.onUploadReady
            )
        else:
            self._onNetworkError(reply, error)

    def onUploadReady(self, reply):
        if self._stage != OutputStage.writing:
            return
        if reply.error() != QNetworkReply.NoError:
            Logger.log("d", "Stopping due to reply error: " + reply.error())
            return

        Logger.log("d", "Uploading...")

        self._stream.seek(0)
        self._postData = QByteArray()
        self._postData.append(self._stream.getvalue().encode())

        if self._use_rrf_http_api:
            self._send('rr_upload',
                query=[("name", "0:/gcodes/" + self._fileName), self._timestamp()],
                next_stage=self.onUploadDone,
                data=self._postData,
            )
        else:
            self._send('machine/file/gcodes/' + self._fileName,
                next_stage=self.onUploadDone,
                data=self._postData,
                method='PUT',
            )

    def onUploadDone(self, reply):
        if self._stage != OutputStage.writing:
            return
        if reply.error() != QNetworkReply.NoError:
            Logger.log("d", "Stopping due to reply error: " + reply.error())
            return

        Logger.log("d", "Upload done")

        self._stream.close()
        self._stream = None

        if self._device_type == DuetRRFDeviceType.simulate:
            Logger.log("d", "Simulating...")
            if self._message:
                self._message.hide()
                self._message = None

            self._message = Message(
                "Simulating print {}...\nPlease close DWC and DO NOT interact with the printer!".format(self._fileName),
                lifetime=0,
                dismissable=False,
                progress=-1,
                title="DuetRRF: " + self._name,
            )
            self._message.show()

            gcode='M37 P"0:/gcodes/' + self._fileName + '"'
            Logger.log("d", "Sending gcode:" + gcode)
            if self._use_rrf_http_api:
                self._send('rr_gcode',
                    query=[("gcode", gcode)],
                    next_stage=self.onSimulationPrintStarted,
                )
            else:
                self._send('machine/code',
                    data=gcode.encode(),
                    next_stage=self.onSimulationPrintStarted,
                )
        elif self._device_type == DuetRRFDeviceType.print:
            self.onReadyToPrint()
        elif self._device_type == DuetRRFDeviceType.upload:
            if self._use_rrf_http_api:
                self._send('rr_disconnect')
            if self._message:
                self._message.hide()
                self._message = None

            self._message = Message(
                "Uploaded file: {}".format(self._fileName),
                lifetime=15,
                title="DuetRRF: " + self._name,
            )
            self._message.addAction("open_browser", catalog.i18nc("@action:button", "Open Browser"), "globe", catalog.i18nc("@info:tooltip", "Open browser to DuetWebControl."))
            self._message.actionTriggered.connect(self._onMessageActionTriggered)
            self._message.show()

            self.writeSuccess.emit(self)
            self._resetState()

    def onReadyToPrint(self):
        if self._stage != OutputStage.writing:
            return

        Logger.log("d", "Ready to print")

        gcode = 'M32 "0:/gcodes/' + self._fileName + '"'
        Logger.log("d", "Sending gcode:" + gcode)
        if self._use_rrf_http_api:
            self._send('rr_gcode',
                query=[("gcode", gcode)],
                next_stage=self.onPrintStarted,
            )
        else:
            self._send('machine/code',
                data=gcode.encode(),
                next_stage=self.onPrintStarted,
            )

    def onPrintStarted(self, reply):
        if self._stage != OutputStage.writing:
            return
        if reply.error() != QNetworkReply.NoError:
            Logger.log("d", "Stopping due to reply error: " + reply.error())
            return

        Logger.log("d", "Print started")

        if self._use_rrf_http_api:
            self._send('rr_disconnect')
        if self._message:
            self._message.hide()
            self._message = None

        self._message = Message(
            "Print started: {}".format(self._fileName),
            lifetime=15,
            title="DuetRRF: " + self._name,
        )
        self._message.addAction("open_browser", catalog.i18nc("@action:button", "Open Browser"), "globe", catalog.i18nc("@info:tooltip", "Open browser to DuetWebControl."))
        self._message.actionTriggered.connect(self._onMessageActionTriggered)
        self._message.show()

        self.writeSuccess.emit(self)
        self._resetState()

    def onSimulationPrintStarted(self, reply):
        if self._stage != OutputStage.writing:
            return
        if reply.error() != QNetworkReply.NoError:
            Logger.log("d", "Stopping due to reply error: " + reply.error())
            return

        Logger.log("d", "Simulation print started for file " + self._fileName)

        # give it some to start the simulation
        QTimer.singleShot(2000, self.onCheckStatus)

    def onCheckStatus(self):
        if self._stage != OutputStage.writing:
            return

        Logger.log("d", "Checking status...")

        if self._use_rrf_http_api:
            self._send('rr_status',
                query=[("type", "3")],
                next_stage=self.onStatusReceived,
            )
        else:
            self._send('machine/status',
                next_stage=self.onStatusReceived,
            )

    def onStatusReceived(self, reply):
        if self._stage != OutputStage.writing:
            return
        if reply.error() != QNetworkReply.NoError:
            Logger.log("d", "Stopping due to reply error: " + reply.error())
            return

        Logger.log("d", "Status received - decoding...")
        reply_body = bytes(reply.readAll()).decode()
        Logger.log("d", "Status: " + reply_body)

        status = json.loads(reply_body)
        if self._use_rrf_http_api:
            # RRF 1.21RC2 and earlier used P while simulating
            # RRF 1.21RC3 and later uses M while simulating
            busy = status["status"] in ['P', 'M']
        else:
            busy = status["result"]["state"]["status"] == 'simulating'

        if busy:
            # still simulating
            if self._message and "fractionPrinted" in status:
                self._message.setProgress(float(status["fractionPrinted"]))
            QTimer.singleShot(1000, self.onCheckStatus)
        else:
            Logger.log("d", "Simulation print finished")

            gcode='M37'
            Logger.log("d", "Sending gcode:" + gcode)
            if self._use_rrf_http_api:
                self._send('rr_gcode',
                    query=[("gcode", gcode)],
                    next_stage=self.onM37Reported,
                )
            else:
                self._send('machine/code',
                    data=gcode.encode(),
                    next_stage=self.onReported,
                )

    def onM37Reported(self, reply):
        if self._stage != OutputStage.writing:
            return
        if reply.error() != QNetworkReply.NoError:
            Logger.log("d", "Stopping due to reply error: " + reply.error())
            return

        Logger.log("d", "M37 finished - let's get it's reply...")
        reply_body = bytes(reply.readAll()).decode().strip()
        Logger.log("d", "M37 gcode reply | " + reply_body)

        self._send('rr_reply',
            next_stage=self.onReported,
        )

    def onReported(self, reply):
        if self._stage != OutputStage.writing:
            return
        if reply.error() != QNetworkReply.NoError:
            Logger.log("d", "Stopping due to reply error: " + reply.error())
            return

        Logger.log("d", "Simulation status received - decoding...")
        reply_body = bytes(reply.readAll()).decode().strip()
        Logger.log("d", "Reported | " + reply_body)

        if self._message:
            self._message.hide()
            self._message = None

        self._message = Message(
            "Simulation finished!\n\n{}".format(reply_body),
            lifetime=0,
            title="DuetRRF: " + self._name,
        )
        self._message.addAction("open_browser", catalog.i18nc("@action:button", "Open Browser"), "globe", catalog.i18nc("@info:tooltip", "Open browser to DuetWebControl."))
        self._message.actionTriggered.connect(self._onMessageActionTriggered)
        self._message.show()

        if self._use_rrf_http_api:
            self._send('rr_disconnect')
        self.writeSuccess.emit(self)
        self._resetState()

    def _onProgress(self, progress):
        if self._message:
            self._message.setProgress(progress)
        self.writeProgress.emit(self, progress)

    def _resetState(self):
        Logger.log("d", "called")
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

    def _onNetworkError(self, reply, error):
        # https://doc.qt.io/qt-5/qnetworkreply.html#NetworkError-enum
        Logger.log("e", repr(error))
        if self._message:
            self._message.hide()
            self._message = None

        errorString = ''
        if reply:
            errorString = reply.errorString()

        message = Message(
            "There was a network error: {} {}".format(error, errorString),
            lifetime=0,
            title="DuetRRF: " + self._name,
        )
        message.show()

        self.writeError.emit(self)
        self._resetState()
