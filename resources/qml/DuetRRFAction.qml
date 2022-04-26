import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 2.7
import QtQuick.Window 2.2

import UM 1.5 as UM
import Cura 1.1 as Cura

Cura.MachineAction
{
    id: base;
    anchors.fill: parent;

    property var finished: manager.finished
    property var selectedInstance: null
    property bool validUrl: true;

    onFinishedChanged: if(manager.finished) {completed()}

    function reset()
    {
        manager.reset()
    }

    Component.onCompleted: {
        actionDialog.minimumWidth = screenScaleFactor * 500;
        actionDialog.minimumHeight = screenScaleFactor * 300;
    }

    Column {
        spacing: UM.Theme.getSize("thin_margin").height;
        anchors {
            fill: parent;
            leftMargin: UM.Theme.getSize("thin_margin").width;
            rightMargin: UM.Theme.getSize("thin_margin").width;
            top: parent.top;
            topMargin: UM.Theme.getSize("thin_margin").height;
        }

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

        Item {
            width: errorMsgLabel.implicitWidth
            height: errorMsgLabel.implicitHeight
            UM.Label {
                id: errorMsgLabel
                visible: !base.validUrl
                text: catalog.i18nc("@error", "URL not valid. Example: http://192.168.1.42/")
                color: "red"
                Layout.fillWidth: true
            }
        }

        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width
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
