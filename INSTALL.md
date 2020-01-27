# Installation and running the RPi-LoRa-Gateway

## Install needed packages
`
sudo apt install python3 python3-rpi.gpio python3-spidev aprx python-spidev screen git
`

## Checkout the code
With
<br/>
`
cd
`
<br/>
change into the homedirectory of the current user.

Enter following commands:<br/>
`git clone https://github.com/tomelec/RPi-LoRa-KISS-TNC.git`<br/>
`cd RPi-LoRa-KISS-TNC`<br/>
`git clone https://github.com/mayeranalytics/pySX127x.git`<br/>
to checkout the code and the LoRa Chip-Driver.

## Configuration
Afterwards configure as following:
### Edit aprx/aprx.conf.lora-aprs file
Type `pico -w aprs/aprx.conf.lora-aprs` to open the config file.
The most important settings are:
* mycall
* myloc
* passcode
* server
to save and close the file do:
`Strg + x` -> Y -> Enter

### Edit pySX127x/SX127x/board_config.py
Type ` pico -w pySX127x/SX127x/board_config.py` change in line 36
from<br/>
`DIO0 = 22   # RaspPi GPIO 22`to<br/>
`DIO0 = 5   # RaspPi GPIO 5`<br/>
to fix the SPI connection #todo how can we config this from outside?

## Start the LoRa KISS TNC and aprx server instance
`python3 Start.py &`<br/>
`sudo aprx -f aprx/aprx.conf.lora-aprs`


## Stop the server
`sudo killall aprx python3`
