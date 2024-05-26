# Changelog of Cura-DuetRRFPlugin

## v1.2.11: 2024-06-15
* potential fix for thumbnail generation on Cura 5.7+ on unsupported Linux distros
* allow disabling of thumbnail embedding (disabled by default for non-Duet-RRF printers)
* allow custom thumbnail sizes, defaulting to 48x48, 240x240, 320x320

## v1.2.10: 2024-01-20
* fix HTTP Basic Auth
* bump compatibility for Cura 5.6 / API 8.6
* require Cura 5 API compatibility

## v1.2.9: 2022-10-19
* bump compatibility for Cura 5.2 / API 8.2

## v1.2.8: 2022-08-15
* also embed QOI thumbnail images when using "Save to Disk" option
* fix window layout to fit content in Cura 5.1

## v1.2.7: 2022-04-26
* bump compatibility for Cura 5.0 / API 8.0, while retaining compatibility with Cura 4.11 / 7.7 and up

## v1.2.6: 2022-04-23
* bump compatibility for Cura 5.0 / API 8.0, for older Cura versions, please use plugin v1.2.5 or older
* fixed simulation progress reports

## v1.2.5: 2022-02-11
* bump compatibility for Cura 4.13 / API 7.9, oldest supported release is now 4.11 / 7.7
* embed QOI thumbnail images of the sliced scene into the uploaded gcode file
* add plugin metadata as comment to uploaded gcode file

## v1.2.4: 2021-09-19
* auto-dismiss success message notifications after 15sec

## v1.2.3: 2021-01-30
* move deleting of unmapped settings to action button on message
* correctly bump plugin version metadata

## v1.2.2: 2021-01-27
* add OutputDevices on currently active printer after saving config
* remove OutputDevices on currently active printer after deleting config

## v1.2.1: 2021-01-21
* fix button width on high-dpi screens
* fix race condition when checking for unmapped settings

## v1.2.0: 2021-01-10
* store settings in local preferences instead of sharable metadata
* use managed HttpRequestManager instead of low-level QNetworkAccessManager
* add a "Configure" output device for easy initial setup

## v1.1.0: 2020-11-13
* BREAKING CHANGE: migrate settings to be printer-specific
* auto-migrate legacy settings for active printers if printer name matches
* bump compatibility for Cura 4.8 / API 7.4

## v1.0.11: 2020-08-29
* bump compatibility for Cura 4.7 / API 7.3
* fix Cura crashes with non-latin strings in Message boxes

## v1.0.10: 2020-07-22
* fix Cura crashes when using Duet3 with SBC

## v1.0.9: 2020-05-02
* bump compatibility for Cura 4.6 / API 7.2
* fix simulation result reply for RRF HTTP API

## v1.0.8: 2020-04-20
* support new HTTP API for Duet3 with SBC running DuetSoftwareFramework

## v1.0.7: 2020-04-04
* bump compatibility for Cura 4.5 / API 7.1

## v1.0.6: 2020-04-04
* correctly encode special characters in filenames
* mention Duet 3 controllers

## v1.0.5: 2019-11-10
* sanitize filename and forbid certain characters

## v1.0.4: 2019-11-10
* bump compatibility for Cura 4.4 / API 7.0

## v1.0.3: 2019-02-02
* require Cura 4.0 API compatibility
* if you are on Cura 3.6, please install v1.0.2 of this plugin

## v1.0.2: 2019-01-06
* fix layout issues on Cura 4.0-beta
* bump compatibility for Cura 4.0 / API 6.0

## v1.0.1: 2018-12-19
* do not try to delete the gcode file before uploading:
  RRF safely handles this, https://forum.duet3d.com/topic/8194/cura-duet-reprap-firmware-integration-question

## v1.0.0: 2018-11-25
* tested with Cura 3.6
* add Duet3D icon - permission granted by Think3dPrint3d
* fixed a update issue when changing connection details
* replace deprecated preferences API in favor of the new one
* code cleanup

## v0.0.20: 2018-10-06
* fix broken dialogs

## v0.0.19: 2018-10-05
* fix more Cura 3.5 incompatibilities

## v0.0.18: 2018-10-05
* fix Cura 3.5 incompatibility
* bump API code

## v0.0.17: 2018-08-10
* fix missing settings at the end of the gcode file
* make use of the default GCodeWrite that Cura uses for "Save to File"

## v0.0.16: 2018-04-11
* improve simulation mode

## v0.0.15: 2018-04-01
* fix message box progress

## v0.0.14: 2018-04-01
* fixes #10

## v0.0.13: 2018-03-28
* fixes gcode retrieval for Cura 3.0, 3.1, 3.2, and the latest 3.3 beta
* also see https://github.com/Ultimaker/Cura/commit/495fc8bbd705f5145fe8312207b3f048a7dcc106#diff-a4cb192cad5ce77939fdd0bf0600208d

## v0.0.12: 2018-03-21
* fix removal error

## v0.0.11: 2018-03-20
* fixes and slashes

## v0.0.10: 2018-03-20
* improve setting parsing

## v0.0.9: 2018-03-01
* updated plugin location paths
* updated RRF status letter

## v0.0.8: 2018-02-17
* hide message after click

## v0.0.7: 2018-02-17
* fix disconnect params

## v0.0.6: 2018-02-15
* improve error handling

## v0.0.5: 2018-02-13
* fix Cura 3.2 incompatibility to access the generated G-code.

## v0.0.4: 2017-11-21
* send disconnect when done

## v0.0.3: 2017-11-07
* fix error handling

## v0.0.2: 2017-11-07
* add a file-rename dialog
* add network error handling

## v0.0.1: 2017-10-21
* initial commit
