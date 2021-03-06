import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.2 as UM
import Cura 1.0 as Cura


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
        anchors.fill: parent;

        Item { width: parent.width; }
        Label { text: catalog.i18nc("@label", "Duet Address (URL)"); }
        TextField {
            id: urlField;
            text: manager.printerSettingUrl;
            maximumLength: 1024;
            anchors.left: parent.left;
            anchors.right: parent.right;
            onTextChanged: {
                base.validUrl = manager.validUrl(urlField.text);
            }
        }

        Item { width: parent.width; }
        Label { text: catalog.i18nc("@label", "Duet Password (if you used M551)"); }
        TextField {
            id: duet_passwordField;
            text: manager.printerSettingDuetPassword;
            maximumLength: 1024;
            anchors.left: parent.left;
            anchors.right: parent.right;
        }

        Item { width: parent.width; }
        Label { text: catalog.i18nc("@label", "HTTP Basic Auth: user (if you run a reverse proxy)"); }
        TextField {
            id: http_userField;
            text: manager.printerSettingHTTPUser;
            maximumLength: 1024;
            anchors.left: parent.left;
            anchors.right: parent.right;
        }

        Item { width: parent.width; }
        Label { text: catalog.i18nc("@label", "HTTP Basic Auth: password (if you run a reverse proxy)"); }
        TextField {
            id: http_passwordField;
            text: manager.printerSettingHTTPPassword;
            maximumLength: 1024;
            anchors.left: parent.left;
            anchors.right: parent.right;
        }

        Item { width: parent.width; }
        Label {
            visible: !base.validUrl;
            text: catalog.i18nc("@error", "URL not valid. Example: http://192.168.1.42/");
            color: "red";
        }

        Item {
            width: saveButton.implicitWidth
            height: saveButton.implicitHeight
        }

        Button {
            id: saveButton;
            text: catalog.i18nc("@action:button", "Save Config");
            width: screenScaleFactor * 100;
            onClicked: {
                manager.saveConfig(urlField.text, duet_passwordField.text, http_userField.text, http_passwordField.text);
                actionDialog.reject();
            }
            enabled: base.validUrl;
        }

        Button {
            id: deleteButton;
            text: catalog.i18nc("@action:button", "Delete Config");
            width: screenScaleFactor * 100;
            onClicked: {
                manager.deleteConfig();
                actionDialog.reject();
            }
        }
    }
}
