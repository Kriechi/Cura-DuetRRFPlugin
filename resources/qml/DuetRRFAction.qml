import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.2
import QtQuick.Window 2.2

import UM 1.5 as UM
import Cura 1.1 as Cura


Cura.MachineAction
{
    id: base;

    property var finished: manager.finished
    onFinishedChanged: if(manager.finished) {completed()}

    function reset()
    {
        manager.reset()
    }

    anchors.fill: parent;
    property var selectedInstance: null

    property bool validUrl: true;

    Component.onCompleted: {
        actionDialog.minimumWidth = screenScaleFactor * 500;
        actionDialog.minimumHeight = screenScaleFactor * 255;
        actionDialog.maximumWidth = screenScaleFactor * 500;
        actionDialog.maximumHeight = screenScaleFactor * 255;
    }

    Column {
        anchors.fill: parent

        Item { width: parent.width; }
        UM.Label {
            text: catalog.i18nc("@label", "Duet Address (URL)")
        }
        TextField {
            id: urlField
            text: manager.printerSettingUrl
            selectByMouse: true
            maximumLength: 1024
            anchors.left: parent.left
            anchors.right: parent.right
            onTextChanged: {
                base.validUrl = manager.validUrl(urlField.text)
            }
        }

        Item { width: parent.width; }
        UM.Label {
            text: catalog.i18nc("@label", "Duet Password (if you used M551)")
        }
        TextField {
            id: duet_passwordField
            text: manager.printerSettingDuetPassword
            selectByMouse: true
            maximumLength: 1024
            anchors.left: parent.left
            anchors.right: parent.right
        }

        Item { width: parent.width; }
        UM.Label {
            text: catalog.i18nc("@label", "HTTP Basic Auth: user (if you run a reverse proxy)")
        }
        TextField {
            id: http_userField
            text: manager.printerSettingHTTPUser
            selectByMouse: true
            maximumLength: 1024
            anchors.left: parent.left
            anchors.right: parent.right
        }

        Item { width: parent.width; }
        UM.Label {
            text: catalog.i18nc("@label", "HTTP Basic Auth: password (if you run a reverse proxy)")
        }
        TextField {
            id: http_passwordField
            text: manager.printerSettingHTTPPassword
            selectByMouse: true
            maximumLength: 1024
            anchors.left: parent.left
            anchors.right: parent.right
        }

        Item { width: parent.width; }
        UM.Label {
            visible: !base.validUrl
            text: catalog.i18nc("@error", "URL not valid. Example: http://192.168.1.42/")
            color: "red"
        }

        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            width: childrenRect.width
            spacing: UM.Theme.getSize("default_margin").width

            Cura.PrimaryButton {
                id: saveButton
                text: catalog.i18nc("@action:button", "Save Config")
                onClicked: {
                    manager.saveConfig(urlField.text, duet_passwordField.text, http_userField.text, http_passwordField.text)
                    actionDialog.reject()
                }
                enabled: base.validUrl
            }

            Cura.SecondaryButton {
                id: deleteButton
                text: catalog.i18nc("@action:button", "Delete config")
                onClicked: {
                    manager.deleteConfig()
                    actionDialog.reject()
                }
            }
        }
    }
}
