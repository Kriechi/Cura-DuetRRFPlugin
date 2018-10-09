import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Dialogs 1.2
import QtQuick.Window 2.1

import UM 1.1 as UM

UM.Dialog
{
    id: base;
    property string object: "";

    property alias newName: nameField.text;
    property bool validName: true;
    property string validationError;
    property string dialogTitle: "Upload Filename";

    title: dialogTitle;

    minimumWidth: 400 * screenScaleFactor
    minimumHeight: 120 * screenScaleFactor
    width: minimumWidth
    height: minimumHeight

    property variant catalog: UM.I18nCatalog { name: "uranium"; }

    signal textChanged(string text);
    signal selectText()
    onSelectText: {
        nameField.selectAll();
        nameField.focus = true;
    }

    Column {
        anchors.fill: parent;

        TextField {
            objectName: "nameField";
            id: nameField;
            width: parent.width;
            text: base.object;
            maximumLength: 100;
            onTextChanged: base.textChanged(text);
            Keys.onReturnPressed: base.accept();
            Keys.onEnterPressed: base.accept();
            Keys.onEscapePressed: base.reject();
        }

        Label {
            visible: !base.validName;
            text: base.validationError;
        }
    }

    rightButtons: [
        Button {
            text: catalog.i18nc("@action:button", "Cancel");
            onClicked: base.reject();
        },
        Button {
            text: catalog.i18nc("@action:button", "OK");
            onClicked: base.accept();
            enabled: base.validName;
            isDefault: true;
        }
    ]
}
