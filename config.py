import sys
sys.path.insert(0, './pySX127x/')
from SX127x.constants import *

# Where to listen?
#		TCP_HOST can be "localhost", "0.0.0.0" or a specific interface address
#		TCP_PORT as configured in aprx.conf <interface> section
TCP_HOST = "0.0.0.0"
TCP_PORT = 10001

# LoRa parameters
FREQUENCY = 433.775
PREAMBLE = 8
BANDWIDTH = BW.BW125
SPREADINGFACTOR = 12
CODINGRATE = CODING_RATE.CR4_5

# Append signal report to beacon comment? Only for position frames.
APPEND_SIGNAL_REPORT = True

