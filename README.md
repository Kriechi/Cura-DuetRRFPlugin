# Cura-DuetRRFPlugin

Plugin for Cura that adds output devices for a RepRapFirmware printer running
Duet3D motion controllers: **Print**, **Simulate**, and **Upload** with a single
click!

All modern [Duet3D motion controllers](https://duet3d.com) are supported:
  * Duet 2 WiFi
  * Duet 2 Ethernet
  * Duet 2 Maestro
  * Duet 3
  * Duet 3 with SBC
  * ... and potentially other RepRapFirmware-based printers

[RepRapFirmware](https://github.com/Duet3D/RepRapFirmware) in `v2` and `v3`
flavours, with or without SBC, are supported through their DWC and DSF APIs.

![Screenshot of the print button](/screenshots/print-button.png)

## Installation via Cura Marketplace

Simply open Cura and go to the **Marketplace** in the menubar, look for the
DuetRRF plugin and install it!

## Manual Installation

Or go the manual route: with Cura not running, unpack the zip file from the
[release](https://github.com/Kriechi/Cura-DuetRRFPlugin/releases/latest) to this
specific folder:

  * Windows: `C:\Users\<username>\AppData\Roaming\cura\<latest version>\plugins\DuetRRFPlugin`
  * macOS: `~/Library/Application Support/Cura/<latest version>/plugins/DuetRRFPlugin`
  * Linux: `/home/<username>/.local/share/cura/<latest version>/plugins/DuetRRFPlugin`

Be careful, the unzipper often tacks on the name of the zip as a folder at the
bottom and you don't want it nested.  You want the files to show up in that
folder.

Make sure that the plugin folder name is a listed above and it does not have any
trailing version numbers (`-1.0.0`) or similar.

## Running from source

Alternatively you can run from the source directly. It'll make it easy to update
in the future. Use git to clone this repository into the folders given above.

## Configuration

**Do NOT try to add a new "networked printer"!** This is only for Ultimaker
printers.

Duet-based printers are configured through Cura preferences for Printers:

* Open Cura **Preferences**
* Select **Printers**
* Activate and select your Duet RepRapFirmware-based printer
* Click on **Connect Duet RepRapFirmware**
* Enter the URL to your controller board
  - make sure this URL works if you copy & paste it into your browser
  - if you browse to that URL, you should see the DuetWebControl (DWC)
  - e.g., `http://printer.local/` or `http://192.168.1.42/`
* If you used `M551` in your `config.g`, enter the password
  - e.g., `my_little!secret` or the default `reprap`
* If you use a reverse proxy to add *HTTP Basic Auth*, enter the credentials
  - if you don't know what *HTTP Basic Auth* is, leave these fields empty
  - e.g., username: `alice`, password: `ecila`
* Click "Save & Test"
* Done!

![Screenshot of the print button](/screenshots/edit-dialog.png)

Now you can load a model and slice it. Then look at the bottom right - there
should be a nice big blue button with you printer name on it!

This button is also a dropdown to choose between **Print**, **Simulate**, or
**Upload**.

## Features

* Uses the Cura Printers integration for configuration
* Print / Simulate / Upload
* Works with HTTP and HTTPS connections and URLs
* Works with HTTP Basic Auth (optional)
* Works with RRF passwords (if you used `M551`, default is `reprap`)
* No support for UNC paths, only IP addresses or resolvable domain names (DNS)

## Use

After you load up a model and it has been sliced, click the down arrow button on
the "Print to (PrinterName)" button on the lower right hand corner. It will
upload the gcode file to the SD card and start printing it. You can select
"Simulate on (PrinterName)" to upload and simulate the print, which returns the
simulated print time an the actual printer. Or you can just "Upload to
(PrinterName)" to copy the gcode to the SD card.

## Troubleshooting

Please [create a new GitHub
issue](https://github.com/Kriechi/Cura-DuetRRFPlugin/issues/new?template=bug_report.md)
and provide all details according to the template.

## License

This project was originally based on
https://github.com/markwal/Cura-OctoPrintUpload and therefore published under
the same license.
