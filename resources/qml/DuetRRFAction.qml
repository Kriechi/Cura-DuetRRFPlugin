import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.2 as UM
import Cura 1.0 as Cura


Cura.MachineAction
{
    id: base;

    anchors.fill: parent;
    property var selectedInstance: null

    property alias url: urlField.text;
    property alias duet_password: duet_passwordField.text;
    property alias http_user: http_userField.text;
    property alias http_password: http_passwordField.text;

    property bool validUrl: true;

    Component.onCompleted: {
        url = manager.printerSettingUrl();
        duet_password = manager.printerSettingDuetPassword();
        http_user = manager.printerSettingHTTPUser();
        http_password = manager.printerSettingHTTPPassword();
        actionDialog.minimumWidth = screenScaleFactor * 500;
        actionDialog.minimumHeight = screenScaleFactor * 240;
        actionDialog.maximumWidth = screenScaleFactor * 500;
        actionDialog.maximumHeight = screenScaleFactor * 240;
    }

    Column {
        anchors.fill: parent;

        Item { width: parent.width; }
        Label { text: catalog.i18nc("@label", "Server Address (URL)"); }
        TextField {
            id: urlField;
            text: "";
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
            text: "";
            maximumLength: 1024;
            anchors.left: parent.left;
            anchors.right: parent.right;
        }

        Item { width: parent.width; }
        Label { text: catalog.i18nc("@label", "HTTP Basic Auth: user (if you run a reverse proxy)"); }
        TextField {
            id: http_userField;
            text: "";
            maximumLength: 1024;
            anchors.left: parent.left;
            anchors.right: parent.right;
        }

        Item { width: parent.width; }
        Label { text: catalog.i18nc("@label", "HTTP Basic Auth: password (if you run a reverse proxy)"); }
        TextField {
            id: http_passwordField;
            text: "";
            maximumLength: 1024;
            anchors.left: parent.left;
            anchors.right: parent.right;
        }

        Item { width: parent.width; }
        Label {
            visible: !base.validUrl;
            text: catalog.i18nc("@error", "URL not valid. Example: http://192.168.1.42/");
        }

        Item {
            width: saveButton.implicitWidth
            height: saveButton.implicitHeight
        }

        Button {
            id: saveButton;
            text: catalog.i18nc("@action:button", "Test && Save");
            width: 100;
            onClicked: {
                manager.testAndSave(urlField.text, duet_passwordField.text, http_userField.text, http_passwordField.text);
                actionDialog.reject();
            }
            enabled: base.validUrl;
        }

        Button {
            id: deleteButton;
            text: catalog.i18nc("@action:button", "Delete Config");
            width: 100;
            onClicked: {
                manager.deleteConfig();
                actionDialog.reject();
            }
        }
    }
}
