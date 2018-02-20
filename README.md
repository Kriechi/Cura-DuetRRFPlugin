# Cura-DuetRRFPlugin
Plugin for Cura 3 that adds output devices for a Duet RepRapFirmware printer: "Print", "Simulate", and "Upload".

## Installation

With Cura not running, unpack the zip file from the [release](https://github.com/Kriechi/Cura-DuetRRFPlugin/releases/latest) to this specific folder:

### Windows
`C:\Users\<username>\AppData\Roaming\cura\3.2\plugins\Cura-DuetRRFPlugin`

### Mac
`~/Library/Application Support/Cura/3.2/plugins/Cura-DuetRRFPlugin`

### Linux
/home/[YOUR_USERNAME]/.local/share/cura/plugins/Cura-DuetRRFPlugin

Be careful, the unzipper often tacks on the name of the zip as a folder at the
bottom and you don't want it nested.  You want the files to show up in that
folder.

## Running from source
Alternatively you can run from the source directly. It'll make it easy to
update in the future. Use git to clone this repository into the folders given
above.

## Configuration
Boot up Cura, choose the following from the Menu Bar:
Extensions->DuetRRF->DuetRRF Connections.  Click "Add" and tell it the url to
your DuetRRF instance (i.e. http://printer.local). You can specify a password
(if you used `M551`, otherwise the default `reprap` is used). This plugin also
support HTTP-Basic-Auth.

## Use
After you load up a model and it has sliced, click the down arrow button on the
"Print to <PrinterName>" button on the lower right hand corner. It will upload
the gcode file to the SD card and start printing it. You can select "Simulate
on <PrinterName>" to upload and simulate the print, which returns the simulated
print time an the actual printer. Or you can just "Upload to <PrinterName>" to
copy the gcode to the SD card.

## License
This project is based on https://github.com/markwal/Cura-OctoPrintUpload and
therefore published under the same license.
