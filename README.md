# Cura-DuetRRFPlugin
Plugin for Cura 3 that adds output devices for a Duet RepRapFirmware printer: "Print", "Simulate", and "Upload".

## Installation

With Cura not running, unpack the zip file from the [release](https://github.com/Kriechi/Cura-DuetRRFPlugin/releases/latest) to this specific folder:

### Windows
`C:\Users\<username>\AppData\Roaming\cura\3.2\plugins\Cura-DuetRRFPlugin`

### Mac
`~/Library/Application Support/Cura/3.2/plugins/Cura-DuetRRFPlugin`

### Linux
`/home/<username>/.local/share/cura/3.2/plugins/Cura-DuetRRFPlugin`

Be careful, the unzipper often tacks on the name of the zip as a folder at the
bottom and you don't want it nested.  You want the files to show up in that
folder.

## Running from source
Alternatively you can run from the source directly. It'll make it easy to
update in the future. Use git to clone this repository into the folders given
above.

## Configuration

* Start Cura
* From the menu bar choose: Extensions -> DuetRRF -> DuetRRF Connections
* Click "Add"
* Enter the name of your printer
  - e.g., `MyBigBox`
* Enter the URL to your DuetWifi/DuetEthernet board
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

Look at the bottom right - there should be the big blue button with you printer name on it!

## Features

* Upload / Simulate / Print
* Works with HTTP and HTTPS connections and URLS
* Works with HTTP Basic Auth (optional)
* Works with RRF passwords (if you used `M551`, default is `reprap`)
* No support for UNC paths, only IP addresses or resolvable domain names (DNS)


## Use
After you load up a model and it has sliced, click the down arrow button on the
"Print to (PrinterName)" button on the lower right hand corner. It will upload
the gcode file to the SD card and start printing it. You can select "Simulate
on (PrinterName)" to upload and simulate the print, which returns the simulated
print time an the actual printer. Or you can just "Upload to (PrinterName)" to
copy the gcode to the SD card.

## License
This project is based on https://github.com/markwal/Cura-OctoPrintUpload and
therefore published under the same license.
