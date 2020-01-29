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

#from multiprocessing import Queue
from __future__ import print_function
import sys
import traceback
is_py2 = sys.version[0] == '2'
if is_py2:
    import Queue as Queue
else:
    import queue as Queue
from kiss import encode_kiss, decode_kiss
from TCPServer import KissServer
from config import *

sys.path.insert(0, './pySX127x/')
from SX127x.board_config import BOARD
from SX127x.LoRa import *

LORA_APRS_HEADER = b"<\xff\x01"

# APRS data types
DATA_TYPES_POSITION = b"!'/@`"
DATA_TYPE_MESSAGE = b":"
DATA_TYPE_THIRD_PARTY = b"}"

def aprs_data_type(lora_aprs_frame):
	delimiter_position = lora_aprs_frame.find(b":")
	try:
		return lora_aprs_frame[delimiter_position + 1]
	except IndexError:
		return ""

class LoRaARPSHat(LoRa):
		def __init__(self, verbose=False):
				super(LoRaARPSHat, self).__init__(verbose)
				self.set_mode(MODE.SLEEP)

				self.set_freq(FREQUENCY)
				self.set_preamble(PREAMBLE)
				self.set_spreading_factor(SPREADINGFACTOR)
				self.set_bw(BANDWIDTH)
				self.set_low_data_rate_optim(True)
				self.set_coding_rate(CODINGRATE)
				self.set_ocp_trim(100)

				self.set_pa_config(pa_select = 1, output_power = 15)
				self.set_max_payload_length(255)
				self.set_dio_mapping([0] * 6)	
				self.server = None

		def on_rx_done(self):
				payload = self.read_payload(nocheck=True)
				if not payload:
					print("No Payload!")
					return
				rssi = self.get_pkt_rssi_value()
				snr = self.get_pkt_snr_value()
				data = bytes(payload)
				print("LoRa RX[%idBm/%idB, %ibytes]: %s" %(rssi, snr, len(data), repr(data)))

				flags = self.get_irq_flags()
				if any([flags[s] for s in ['crc_error', 'rx_timeout']]):
					print("Receive Error, discarding frame.")
					#print(self.get_irq_flags())
					self.clear_irq_flags(RxDone=1, PayloadCrcError=1, RxTimeout=1) # clear rxdone IRQ flag
					self.reset_ptr_rx()
					self.set_mode(MODE.RXCONT)
					return

				if self.server:
					# remove LoRa-APRS header if present
					if data[0:len(LORA_APRS_HEADER)] == LORA_APRS_HEADER:
						data = data[len(LORA_APRS_HEADER):]
					if APPEND_SIGNAL_REPORT:
						# Signal report only for certain frames, not messages!
						if aprs_data_type(data) in DATA_TYPES_POSITION:
							data += b" RSSI=%idBm SNR=%idB" % (rssi, snr)
					try:
						encoded_data = encode_kiss(data)
					except:
						print("KISS encoding went wrong (exception while parsing)")
						traceback.print_tb(sys.exc_info())
						encoded_data = None
					if encoded_data != None:
						print("To Server: " + repr(encoded_data))
						self.server.send(encoded_data)
					else:
						print("KISS encoding went wrong")
				self.clear_irq_flags(RxDone=1) # clear rxdone IRQ flag
				self.reset_ptr_rx()
				self.set_mode(MODE.RXCONT)
				#self.set_mode(MODE.CAD)

		def on_tx_done(self):
				print("TX DONE")
				self.clear_irq_flags(TxDone=1) # clear txdone IRQ flag
				self.set_dio_mapping([0] * 6)
				self.set_mode(MODE.RXCONT)

		def transmit(self, data):
			self.write_payload([c for c in data])
			lora.set_dio_mapping([1,0,0,0,0,0])
			self.set_mode(MODE.TX)

		def set_server(self, server):
			self.server = server

if __name__ == '__main__':
		'''Raspberry Pi LoRa TNC'''
		import time

		# TX KISS frames go here (Digipeater -> TNC)
		KissQueue = Queue.Queue()

		# Init SX127x
		BOARD.setup()

		# TCP Server for the digipeater to connect
		server = KissServer(TCP_HOST, TCP_PORT, KissQueue)
		server.setDaemon(True)
		server.start()

		# LoRa tansceiver instance
		lora = LoRaARPSHat(verbose=False)
		lora.set_server(server)
		#print(lora)
		lora.reset_ptr_rx()
		lora.set_mode(MODE.RXCONT)


#	Experimental multi-SF reception. Does not yet work.		
#		lora.set_mode(MODE.STDBY)	
#		lora.set_mode(MODE.CAD)
#		f = lora.get_irq_flags()
#		while True:
#
#			for sf in [10, 11, 12]:
#				#m = lora.get_mode() # important to keep pySX127x updated
#				lora.set_mode(MODE.STDBY)
#				lora.set_spreading_factor(sf)
#				lora.set_mode(MODE.CAD)
#				#time.sleep(0.001)
#				while f["cad_done"] == 0:
#					time.sleep(0.05)
#					f = lora.get_irq_flags()
#					#print(sf, MODE.lookup[lora.get_mode()], f)
#				if f["cad_detected"]:
#					print("DET SF %i" % sf)
#					lora.set_mode(MODE.RXSINGLE)
#					time.sleep(3)
#				lora.clear_irq_flags(CadDone=1, CadDetected=1)
#				f = lora.get_irq_flags()
#				#print((lora.get_irq_flags()))
#			
#		import sys
#		sys.exit(0)

#			if f["cad_done"]:
#				lora.clear_irq_flags(CadDone=1)
#				if f["cad_detected"]:
#					lora.clear_irq_flags(CadDetected=1)
#					lora.set_mode(MODE.RXSINGLE)
#				else:
#					if mode == 1:
#						lora.set_spreading_factor(SPREADINGFACTOR)
#						lora.set_low_data_rate_optim(True)
#						mode = 2
#					else:
#						lora.set_spreading_factor(10)
#						lora.set_low_data_rate_optim(False)
#						mode = 1
#					lora.set_mode(MODE.CAD)
#			elif f["rx_timeout"]:
#				lora.clear_irq_flags(RxTimeout=1)
#				lora.set_mode(MODE.CAD)
#
#			if f["valid_header"]:
#				lora.clear_irq_flags(ValidHeader=1)


#			if lora.mode == MODE.RXCONT:
#				lora.set_mode(MODE.CAD)
#			time.sleep(0.001)


		while True:
				# only transmit if no signal is detected to avoid collisions
				if not lora.get_modem_status()["signal_detected"]:
					#print("RSSI: %idBm" % lora.get_rssi_value())
					#FIXME: Add noise floor measurement for telemetry
					if not  KissQueue.empty():
						try:
							data = KissQueue.get(block=False)
							#print("KISS frame:" + repr(data))
							decoded_data = decode_kiss(data)
							#print("Decoded:" + decoded_data)
							if aprs_data_type(decoded_data) == DATA_TYPE_THIRD_PARTY:
								# remove third party thing
								decoded_data = decoded_data[decoded_data.find(DATA_TYPE_THIRD_PARTY) + 1:]
							decoded_data = LORA_APRS_HEADER + decoded_data
							print("TX: " + repr(decoded_data))
							lora.transmit(decoded_data)
						except Queue.Empty:
							pass
					
				time.sleep(0.50)


