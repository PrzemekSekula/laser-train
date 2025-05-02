# -*- coding: utf-8 -*-
# !/usr/bin/env python

# #############################################################################
#  ATTENTION
# #############################################################################
#
#  This software is for guidance only. It is provided "as is".
#  It only aims at providing coding information to the customer in order for
#  them to save time. As a result no warranties, whether express, implied or
#  statutory, including, but not limited to implied warranties of
#  merchantability and fitness for a particular purpose apply to this software.
#  A·P·E Angewandte Physik und Elektronik GmbH shall not be held liable for any
#  direct, indirect or consequential damages with respect to any claims arising
#  from the content of such sourcecode and/or the use made by customers of the
#  coding information contained herein in connection with their products.
#
#  File Version: 1.5
#
#  Changelog:
#    1.0 - Initial Version
#    1.1 - Python Version check implemented for V>= 3.0 (2015/05/26)
#    1.2 - Code is now compatible with python versions 2.7.x and 3.x
#    1.3 - Added timeout for reading oprerations, added buffer-clear before reading
#    1.4 - Added optional interface ident in host name for pulseCheck NX
#        - Added checkStatus with error handling
#    1.5 - Fix compatibility for NX devices, remove compatibility for old devices
#
# #############################################################################

import socket
import time
import re
from select import select


class ape_device:
    def __init__(self, host="127.0.0.1", port=5025, name="APEDevice"):
        self.host = host
        self.port = port
        self.name = name
        self.connected = False
        self.dev = None
        self.timeout = 0.5
        self.connect()

    def _clearBuffer(self):
        '''Clears the device buffer'''
        while True:
            ready = select([self.dev], [], [], 0)
            if ready[0]:
                rc = self.dev.recv(1)
                if rc == "":
                    break
            else:
                break

    def connect(self):
        if self.connected:
            raise Exception('[Connect] Error. Already Connected')

        elif not isinstance(self.host, str) or not self.host:
            raise Exception('[Connect] Hostname must be passed as string')

        elif not isinstance(self.port, int) or not self.port or not 1 <= self.port <= 65535:
            raise Exception('[Connect] Portnumber must be passed as integer (range 1..65535)')
        else:
            try:
                check_interface = re.compile('(\w+-)?(S\d{5})%(usb|USB|eth|ETH|lan|LAN)', re.IGNORECASE)
                matcher = check_interface.match(self.host)
                if matcher:
                    # Validate optional Interface
                    product = matcher.group(1).lower()[:-1] if matcher.group(1) else ""
                    serial = matcher.group(2)
                    interface = matcher.group(3).lower()
                    if (product == "") or (product.lower() == "pulsecheck"):
                        if interface == "lan":
                            self.host = product + '-' + serial if product else serial
                        elif interface == "usb":
                            self.host = "169.254." + str(int(serial[2:4])) + "." + str(int(serial[4:6]))
                        elif interface == "eth":
                            self.host = "169.254.1" + str(int(serial[2:4])) + "." + str(int(serial[4:6]))
                self.dev = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.dev.settimeout(self.timeout)
                self.dev.connect((self.host, self.port))
                self.connected = True
                time.sleep(1)
                print('Connected to: ' + self.host + ':' + str(self.port))
                print('--------------------------------------------')

            except socket.gaierror:
                self.connected = False
                self.dev = None
                raise Exception(
                    'Error. Unable to open TCP connection to the specified remote host. Please make sure the specified connection details.')

    def disconnect(self):
        if not self.connected:
            raise Exception('[Disconnect] Not connected')
        else:
            self.dev.close()

    def send(self, command):
        if not self.connected:
            raise Exception('[Send] Error. Not connected')
        else:
            cmd = command.rstrip() + "\r\n"
            self._clearBuffer()
            self.dev.send(cmd.encode())

    def read_scpi(self):
        if not self.connected:
            raise Exception('[Read_SCPI] Error. Not connected.')
            return bytearray([])
        else:
            if self.receive(1)[0] != ord("#"):
                return bytearray([])
            else:
                header_len = int(self.receive(1).decode())
                if header_len < 0:
                    return bytearray([])
                else:
                    data_len = int(self.receive(header_len).decode())
                    if data_len <= 0:
                        return bytearray([])
                    else:
                        temp = self.receive(data_len)
                        # read until newline char
                        while True:
                            buffer = self.dev.recv(1)
                            if buffer[0] == 0x0a:
                                break
                        return temp

    def receive(self, length=-1):
        data_read = length
        answer = bytearray([])
        buffer = bytearray([])
        if not isinstance(length, int):
            raise Exception('[Receive] Data length must be passed as integer')

        if not self.connected:
            raise Exception('[Receive] Error. Not connected')
        else:
            try:
                if length == 0:
                    answer = bytearray([])

                elif length > 0:
                    while data_read > 0:
                        buffer = self.dev.recv(data_read)
                        answer.extend(buffer)
                        data_read -= len(buffer)
                else:
                    while True:
                        buffer = self.dev.recv(1)
                        if buffer[0] != 0:
                            answer.extend(buffer)
                        if buffer[0] == 0x0a:
                            break
            except:
                import traceback
                traceback.print_exc()
                raise Exception('[Receive] Error while reading data')

            return answer

    def query(self, command, block=False):
        answer = bytearray([])
        self.send(command)
        if block == False:
            answer = self.receive().decode().rstrip()
        else:
            answer = self.read_scpi()

        return answer

    def idn(self):
        return self.query("*idn?")

    def stb(self):
        self._stb = int(self.query("*stb?"))
        return self._stb

    def esr(self):
        self._esr = int(self.query("*esr?"))
        return self._esr

    def hasError(self):
        return (self.stb() & 4) > 0

    def nextError(self):
        self._error = self.query("syst:err?")
        return self._error

    def checkStatus(self):
        status = self.stb()
        if (status & 36) > 0:
            errors = ""
            check_status = status
            while (check_status & 36) > 0:
                # read *ESR if bit 2 (event queue) or bit 5 (esr)
                if (status & 36) > 0:
                    self.esr()
                # read SYST:ERR if bit 2 (event queue)
                if (status & 4) > 0:
                    errors = errors + self.nextError() + "\r\n"
                check_status = self.stb()
            raise Exception('[CheckStatus] Error(s) from Device:\r\n' + errors)
        return (status & 4) == 0