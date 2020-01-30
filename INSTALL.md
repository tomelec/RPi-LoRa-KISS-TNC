# Installation and running the RPi-LoRa-Gateway

## Install needed packages
`
sudo apt install python3 python3-rpi.gpio python3-spidev aprx screen git python3-pil python3-smbus
`

## Checkout the code
Enter following commands:<br/>
```
cd
git clone https://github.com/tomelec/RPi-LoRa-KISS-TNC.git
cd RPi-LoRa-KISS-TNC
git clone https://github.com/mayeranalytics/pySX127x.git
```
to change into homedirectory and then checkout the code and the LoRa Chip-Driver in the right directory.

## Configuration
Afterwards configure as following:
### Edit aprx/aprx.conf.lora-aprs file
Type:
```
cd
cd RPi-LoRa-KISS-TNC
sudo cp aprx/aprx.conf.lora-aprs /etc/aprx.conf
pico -w /etc/aprx.conf
```
to copy and then open the config file.

The most important settings are:
* **mycall**<br/>
Your call with an apropriate SSID suffix<br/>[Paper on SSID's from aprs.org](http://www.aprs.org/aprs11/SSIDs.txt) 
* **myloc**<br/>
NMEA lat/lon form:
```
lat ddmm.mmN lon dddmm.mmE
```
Example:
```
lat 4812.52N lon 01622.39E
```
(simplest way to find the right coordinats for this? Go to [aprs.fi](http://www.aprs.fi) on your location right-click and choose "Add marker" then click on the marker and you should see your coordinates in the NMEA style - enter this infos without any symbols into the config file as seen in the example above)


* **passcode**<br/>
see [see here to generate appropiate setting](https://apps.magicbug.co.uk/passcode/)
* **server**<br/>
either leave the default server or if you're connected to Hamnet as well insert an APRSIS Server within the hamnet - a List of Aprs Hamnet servers can be found in the [OEVSV Wiki](http://wiki.oevsv.at/index.php/Anwendungen_am_HAMNET#APRS_Server))


to save and close the file do:
`Strg + x` -> Y -> Enter

### Edit driver config file
Type 
```
pico -w pySX127x/SX127x/board_config.py
```
change in line 36
from
```
DIO0 = 22  # RaspPi GPIO 22
DIO0 = 5   # RaspPi GPIO 5
```
to fix the SPI connection #todo how can we config this from outside?

## Start the LoRa KISS TNC and aprx server instance
```
python3 Start_lora-tnc.py &
sudo aprx
```

## Stop the server's
```
sudo killall aprx python3
```
