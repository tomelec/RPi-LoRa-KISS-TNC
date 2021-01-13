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

import sys
from asyncio import QueueEmpty
import traceback
sys.path.insert(0, './pySX127x/')
from pySX127x.SX127x.LoRa import LoRa
from pySX127x.SX127x.constants import *
from pySX127x.SX127x.board_config import BOARD
import time
#import KissHelper


class LoraAprsKissTnc(LoRa):
    LORA_APRS_HEADER = b"<\xff\x01"

    # APRS data types
    DATA_TYPES_POSITION = b"!'/@`"
    DATA_TYPE_MESSAGE = b":"
    DATA_TYPE_THIRD_PARTY = b"}"

    queue = None
    server = None

    # init has LoRa APRS default config settings - might be initialized different when creating object with parameters
    def __init__(self, queue, server, frequency=433.775, preamble=8, spreadingFactor=12, bandwidth=BW.BW125,
                 codingrate=CODING_RATE.CR4_5, appendSignalReport = True, paSelect = 1, outputPower = 15, verbose=False):
        # Init SX127x
        BOARD.setup()

        super(LoraAprsKissTnc, self).__init__(verbose)
        self.queue = queue
        self.appendSignalReport = appendSignalReport

        self.set_mode(MODE.SLEEP)

        self.set_freq(frequency)
        self.set_preamble(preamble)
        self.set_spreading_factor(spreadingFactor)
        self.set_bw(bandwidth)
        self.set_low_data_rate_optim(True)
        self.set_coding_rate(codingrate)
        self.set_ocp_trim(100)

        self.set_pa_config(paSelect, outputPower)
        self.set_max_payload_length(255)
        self.set_dio_mapping([0] * 6)
        self.server = server

        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)

    def startListening(self):
        try:
            while True:
                # only transmit if no signal is detected to avoid collisions
                if not self.get_modem_status()["signal_detected"]:
                    # print("RSSI: %idBm" % lora.get_rssi_value())
                    # FIXME: Add noise floor measurement for telemetry
                    if not self.queue.empty():
                        try:
                            data = self.queue.get(block=False)
                            if self.aprs_data_type(data) == self.DATA_TYPE_THIRD_PARTY:
                                # remove third party thing
                                data = data[data.find(self.DATA_TYPE_THIRD_PARTY) + 1:]
                                data = self.LORA_APRS_HEADER + data
                            print("LoRa TX: " + repr(data))
                            self.transmit(data)
                        except QueueEmpty:
                            pass

                time.sleep(0.50)
        except KeyboardInterrupt:
            BOARD.teardown()

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
            # print(self.get_irq_flags())
            self.clear_irq_flags(RxDone=1, PayloadCrcError=1, RxTimeout=1)  # clear rxdone IRQ flag
            self.reset_ptr_rx()
            self.set_mode(MODE.RXCONT)
            return

        if self.server:
            # remove LoRa-APRS header if present
            if data[0:len(self.LORA_APRS_HEADER)] == self.LORA_APRS_HEADER:
                data = data[len(self.LORA_APRS_HEADER):]
            if self.appendSignalReport:
                # Signal report only for certain frames, not messages!
                if self.aprs_data_type(data) in self.DATA_TYPES_POSITION:
                    data += b" RSSI=%idBm SNR=%idB" % (rssi, snr)
            self.server.send(data, {"level":rssi, "snr":snr})
        self.clear_irq_flags(RxDone=1)  # clear rxdone IRQ flag
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)

    # self.set_mode(MODE.CAD)

    def on_tx_done(self):
        print("TX DONE")
        self.clear_irq_flags(TxDone=1)  # clear txdone IRQ flag
        self.set_dio_mapping([0] * 6)
        self.set_mode(MODE.RXCONT)

    def transmit(self, data):
        self.write_payload([c for c in data])
        self.set_dio_mapping([1, 0, 0, 0, 0, 0])
        self.set_mode(MODE.TX)

    def aprs_data_type(self, lora_aprs_frame):
        delimiter_position = lora_aprs_frame.find(b":")
        try:
            return lora_aprs_frame[delimiter_position + 1]
        except IndexError:
            return ""