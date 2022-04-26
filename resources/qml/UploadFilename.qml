import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Window 2.2

import UM 1.5 as UM
import Cura 1.1 as Cura

UM.Dialog
{
    id: base;
    property string object: "";

    property alias newName: nameField.text;
    property bool validName: true;
    property string validationError;
    property string dialogTitle: "Upload Filename";

    title: dialogTitle;

    minimumWidth: screenScaleFactor * 400
    minimumHeight: screenScaleFactor * 120

    property variant catalog: UM.I18nCatalog { name: "uranium"; }

    signal textChanged(string text);
    signal selectText()
    onSelectText: {
        nameField.selectAll();
        nameField.focus = true;
    }

    margin: UM.Theme.getSize("default_margin").width
    buttonSpacing: UM.Theme.getSize("default_margin").width

    Column {
        anchors.fill: parent;

        UM.Label {
            text: "Enter the filename for uploading, use forward slashes (/) as directory separator if needed:"
            width: parent.width
            wrapMode: Text.WordWrap
        }

        TextField {
            objectName: "nameField"
            id: nameField
            width: parent.width
            text: base.object
            maximumLength: 100
            selectByMouse: true
            onTextChanged: base.textChanged(text)
            Keys.onReturnPressed: { if (base.validName) base.accept(); }
            Keys.onEnterPressed: { if (base.validName) base.accept(); }
            Keys.onEscapePressed: base.reject()
        }

        UM.Label {
            visible: !base.validName
            text: base.validationError
        }
    }

    Item
    {
        ButtonGroup {
            buttons: [cancelButton, okButton]
            checkedButton: okButton
        }
    }

    rightButtons: [
        Cura.PrimaryButton {
            id: okButton
            text: catalog.i18nc("@action:button", "OK")
            onClicked: base.accept()
            enabled: base.validName
        },
        Cura.SecondaryButton {
            id: cancelButton
            text: catalog.i18nc("@action:button", "Cancel")
            onClicked: base.reject()
        }
    ]
}
