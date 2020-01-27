#!/usr/bin/python
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
# Usage: python3 Start.py
#
from queue import Queue
from TCPServer import KissServer
from config import *
from LoraAprsKissTnc import LoraAprsKissTnc

# TX KISS frames go here (Digipeater -> TNC)
kissQueue = Queue()

# TCP Server for the digipeater to connect
server = KissServer(kissQueue)
server.setDaemon(True)
server.start()

# LoRa transceiver instance
lora = LoraAprsKissTnc(kissQueue, server, verbose=False)

# this call loops forever inside
lora.startListening()
