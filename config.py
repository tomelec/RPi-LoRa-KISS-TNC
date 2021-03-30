## KISS Settings
# Where to listen?
#		TCP_HOST can be "localhost", "0.0.0.0" or a specific interface address
#		TCP_PORT as configured in aprx.conf <interface> section
TCP_HOST = "0.0.0.0"
TCP_PORT = 10001

## AXUDP Settings
# AXUDP_REMOTE_IP IP to wich udp packets are sent
# AXUDP_REMOTE_PORT UDP Port to wich udp packets are sent
# AXUDP_LOCAL_IP IP of Interface to listen on, 0.0.0.0 for all interfaces
# AXUDP_LOCAL_PORT Port to listen for incoming AXUDP packets

AXUDP_REMOTE_IP = "192.168.0.185"
AXUDP_REMOTE_PORT = 20000
AXUDP_LOCAL_IP = "0.0.0.0"
AXUDP_LOCAL_PORT = 20000

## Genral Settings
# USE_AXUDP Switch from KISS to AXUDP if True
# APPEND_SIGNAL_REPORT adds signal report to text of APRS-Message for debug purpose
#                      this will change the original message and could cause loops
USE_AXUDP = True
APPEND_SIGNAL_REPORT = True