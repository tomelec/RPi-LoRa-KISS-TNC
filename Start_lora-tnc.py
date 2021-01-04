#!/usr/bin/python3
# -*- coding: utf-8 -*-

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Usage: python3 Start_lora-tnc.py
#
from queue import Queue
from TCPServer import KissServer
from AXUDPServer import AXUDPServer
import config
from LoraAprsKissTnc import LoraAprsKissTnc

# TX KISS frames go here (Digipeater -> TNC)
kissQueue = Queue()

# KISSTCP or AXUDP Server for the digipeater to connect
if config.USE_AXUDP:
  server = AXUDPServer(kissQueue, config.AXUDP_LOCAL_IP, config.AXUDP_LOCAL_PORT, config.AXUDP_REMOTE_IP, config.AXUDP_REMOTE_PORT)  
else:
  server = KissServer(kissQueue, config.TCP_HOST, config.TCP_PORT)

server.setDaemon(True)
server.start()

# LoRa transceiver instance
lora = LoraAprsKissTnc(kissQueue, server, verbose=False, appendSignalReport = config.APPEND_SIGNAL_REPORT)

# this call loops forever inside
lora.startListening()
