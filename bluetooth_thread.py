#!/usr/bin/env python
##################################################################################################################
# Copyright 2020, 2023 Ralph Carl Blach III
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR
# ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH
# THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
##############################################################################################################

import threading
import time
import socket
import radio_constants


class BluetoothTransmitThread(threading.Thread):
    """
    this is a thread class for the bluetooth radio
    When establishing a bluetooth socket, one uses the local bluetooth mac address
    """
    __slots__ = ['args', 'kwargs', 'lock_location_class', 'event', 'mac_address', 'timeout']

    def __init__(self, name:str, *args: list, **kwargs: dict):
        """
        this is the init class for the thread

        :param name: The name of the thread
        :param args: The args, it must be a tuple consisting of
                                (gps_lock_and_location, event, network, log.log, args.sleep_time)
        :param kwargs: a dictionary that must contain the mac address and the timeout
                        example {'mac_address': xx:xx:xx:xx:xx, 'timeout':10}  the timeout is optional but the mac address is not
        """
        super().__init__(name=name, args=args, kwargs=kwargs)

        if args is None:
            raise ValueError('Args cannot be None')

        self.args = args
        self.kwargs = kwargs
        self.lock_location_class, self.event, self.network, self.logger, self.sleep_time_in_sec = self.args
        self.thread_name = name
        self.mac_address = self.kwargs['MacAddress']
        self.timeout = self.kwargs.get('TimeOut', 30)
        self.port = self.kwargs.get('RfcommPort', 4)

    def bluetooth_connect(self, mac_address, bluetooth_port: int = 4, timeout: int = 30):
        """
        connect to blue tooth client

        :param mac_address: the mac address of the client to which we will connect
        :param bluetooth_port: the rfcomm bluetooth port, However, it must match the bluetooth_port used by the client.
        :param timeout: the length of time in seconds to wait for a connect
        :return: at tuple with the local_socket, client_socket, and address if successful, False, false if it fails
                note the client socket is used to write
        """

        self.logger.info(f'bluetooth_port = {bluetooth_port}, mac_address = {mac_address}, len={len(mac_address)}')
        backlog = 1
        # size = 1024
        #
        local_socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        self.logger.info(f'local_socket={local_socket}  mac address = {mac_address}, type ={type(mac_address)}')
        try:
            local_socket.bind((mac_address, bluetooth_port))
        except OSError as error:
            local_socket.close()
            if str(error) == 'bad bluetooth address':
                raise OSError from error
            self.logger.info(f'bluetooth bind socket failed error = {error}')
            return False, False, False
        else:
            self.logger.info("bind worked ok")
        local_socket.listen(backlog)
        local_socket.settimeout(timeout)

        try:
            client_socket, address = local_socket.accept()
        except OSError as error:
            self.logger.info(f'bluetooth accept failed error = {error}')
            return False, False, False
        self.logger.info(f'bluetooth accept passed client_socket = {client_socket}, address = {address}')
        # the client socket is the socket to which the writes/reads will go
        # the address the remote bluetooth mac address and the rfcomm port
        return local_socket, client_socket, address

    @staticmethod
    def send_data(write_socket, data):
        """
        send the data to the bluetooth client

        :param write_socket: the client address to which to send the data
        :param data: the data to send,should be a string
        :return True if the send is successful or False if not
        """
        try:
            byte_data_array = bytearray(('{}\n'.format(data).encode('utf-8')))
            write_socket.send(byte_data_array)
        except OSError:
            return False
        return True

    @staticmethod
    def process_packet(packet_list, counter):
        """
        process the packet

        :param packet_list: a list that is either a packet or none
        :param counter a counter ot show movement on phone
        :return: a string with the packet in it
        """
        # short circuit will prevent the exception in the second half
        # see if the positon is not valid
        if packet_list is None or packet_list[radio_constants.POSITION_VALID] == radio_constants.POSITION_NOT_VALID_VALUE:
            lat_long = 'No valid location'
        else:
            # latitude has the form of Latitude (DDmm.mm)
            latitude = packet_list[radio_constants.LATITUDE]

            # longitude has the form Longitude (DDDmm.mm)
            longitude = packet_list[radio_constants.LONGITUDE]

            # send the position fix indicator
            lat_long = longitude + ', ' + latitude + '{}'.format(' ') + packet_list[radio_constants.POSITION_VALID] + ' {}'.format(counter)
        return lat_long

    def run(self):
        """
            This overrides run on the threading class

        :return: None
        """
        connected = False
        counter = 0

        while True:
            if self.event.is_set():
                return
            time.sleep(.5)
            if not connected:
                local_socket, bluetooth_write_socket, address_pair = self.bluetooth_connect(mac_address=self.mac_address)
                if local_socket:
                    connected = True
                    self.logger.info(f"Paired with {address_pair}")
            elif connected:
                # ok we are connected.
                packet_list = self.lock_location_class.data
                lat_long = self.process_packet(packet_list, counter)
                counter = counter + 1 if counter < 16 else 0
                lat_long = lat_long + "\r\n"

                return_code = self.send_data(bluetooth_write_socket, lat_long)
                if not return_code:
                    connected = False
                    bluetooth_write_socket.close()
                    local_socket.close()
                    continue
            # only delay if we are connected
            time.sleep(self.sleep_time_in_sec)
