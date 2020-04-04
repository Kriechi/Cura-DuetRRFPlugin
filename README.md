# Cura-DuetRRFPlugin

Plugin for Cura 4.5 that adds output devices for a RepRapFirmware printer
running a Duet 2 Wifi, Duet 2 Ethernet, Duet 2 Maestro, or Duet 3 motion
controller: "Print", "Simulate", and "Upload".

![Screenshot of the print button](/screenshots/print-button.png)

## Installation via Cura Marketplace

Simply open Cura and go to the **Marketplace** in the menubar, search for
the DuetRRF plugin and install it!

## Manual Installation

Or go the manual route: with Cura not running, unpack the zip file from the
[release](https://github.com/Kriechi/Cura-DuetRRFPlugin/releases/latest) to this
specific folder:

  * Windows: `C:\Users\<username>\AppData\Roaming\cura\4.5\plugins\DuetRRFPlugin`
  * macOS: `~/Library/Application Support/Cura/4.5/plugins/DuetRRFPlugin`
  * Linux: `/home/<username>/.local/share/cura/4.5/plugins/DuetRRFPlugin`

Be careful, the unzipper often tacks on the name of the zip as a folder at the
bottom and you don't want it nested.  You want the files to show up in that
folder.

Make sure that the plugin folder name is a listed above and it does not have
any trailing version numbers (`-1.0.0`) or similar.

## Running from source

Alternatively you can run from the source directly. It'll make it easy to
update in the future. Use git to clone this repository into the folders given
above.

## Configuration

**Do NOT try to add a new "networked printer"!** This is only for Ultimaker printers.

Duet-based printers are configured through
the extension menu bar:

* Start Cura
* From the menu bar choose: Extensions -> DuetRRF -> DuetRRF Connections

![Screenshot of the menu bar entry](/screenshots/menu-bar.png)

* Click "Add"

![Screenshot of the edit dialog](/screenshots/edit-dialog.png)

* Enter the name of your printer
  - e.g., `LittlePrinter`
* Enter the URL to your controller board
  - make sure this URL works if you copy & paste it into your browser
  - if you browse to that URL, you should see the DuetWebControl (DWC)
  - e.g., `http://printer.local/` or `http://192.168.1.42/`
* If you used `M551` in your `config.g`, enter the password
  - e.g., `my_little!secret` or the default `reprap`
* If you use a reverse proxy to add *HTTP Basic Auth*, enter the credentials
  - if you don't know what *HTTP Basic Auth* is, leave these fields empty
  - e.g., username: `alice`, password: `ecila`
* Click "Ok"
* Done!

Now you can load a model and slice it. Then look at the bottom right - there
should be the big blue button with you printer name on it!

## Features

* Upload / Simulate / Print
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

## License

This project is based on https://github.com/markwal/Cura-OctoPrintUpload and
therefore published under the same license.
