#!/usr/bin/env python
# Copyright 2020 Ralph Carl Blach III
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

import threading
import time
import radio_constants
import socket

class BluetoothTransmitThread(threading.Thread):
    """
    this is a thread class for the bluetooth radio

    """
    def __init__(self, name, *args, **kwargs):
        """
        this is the init class for the thread

        :param name: The name of the thread
        :param args: The args, it must be a tuple consisting go the lock variable, the shared data, must be a list
                     the second arg is the event so cause a shutdown if button a is pushed
        :param kwargs: a dictionary that must contain the mac address and the timeout
                        example {'mac_address': xx:xx:xx:xx:xx, 'timeout':10}  the timeout is optional but the mac address is not
        """
        super(BluetoothTransmitThread, self).__init__(name=name, args=args, kwargs=kwargs)

        if args is None:
            raise ValueError('Args cannot be None')

        if args is None:
            raise ValueError()
        self.args = args
        self.kwargs = kwargs
        self.lock_location_class = self.args[0]
        self.name = name
        self.event = self.args[1]
        self.mac_address = self.kwargs['mac_address']
        self.timeout = self.kwargs.get('timeout', 10)
        print('mac_address={}, timeout={}'.format(self.mac_address, self.timeout))

    def connect(self, mac_address, timeout=10):
        """
        connect to blue tooth client

        :param mac_address: the mac address of the client to which we will connect
        :return: at tuple with the client, and address if successful, False, false if it fails
        """
        print('in connect')
        hostMACAddress = mac_address  # The MAC address of a Blue tooth adapter on the server. The server might have multiple Bluetooth adapters.
        port = 3  # 3 is an arbitrary choice. However, it must match the port used by the client.
        backlog = 1
        size = 1024
        local_socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        local_socket.bind((hostMACAddress, port))
        local_socket.settimeout(timeout)
        local_socket.listen(backlog)
        try:
            client, address = local_socket.accept()
        except Exception as error:
            print("accept error=\'{}\'".format(error))
            return False, False, False
        return local_socket, client, address

    def send_data(self, client, address, data):
        """
        send the data to the client

        :param client: the client address to which to send the data
        :param address: the receiver address
        :param data: the data to send,should be a string
        :return True if the send is successful or False if not
        """

        try:

            byte_data_array = bytearray(('{}\n'.format(data).encode('utf-8')))
            length = client.send(byte_data_array)
            print('length send ={}'.format(length))
        except:
            return False
        return True

    def process_packet(self, packet_list):
        """
        process the packet
        :param packet: a list that is either a packet or none
        :return: a string with the packet in it
        """
        degree_sign_utf8 = u"\u00b0"
        minutes_sign = u"\u0027"

        # short circuit will prevent the exception in the second half
        if packet_list is None or packet_list[radio_constants.VALID] != 'A':
            lat_long = 'No valid location'
        else:
        # latitude has the form of Latitude (DDmm.mm)
            lat_degrees = packet_list[radio_constants.LATITUDE][:2]
            lat_minutes_seconds = packet_list[radio_constants.LATITUDE][2:]
            north_south = '' if packet_list[radio_constants.LATITUDE_NS] == 'N' else '-'
            latitude = 'lat = ' + north_south + lat_degrees + degree_sign_utf8 + lat_minutes_seconds + minutes_sign

            # longitude has teh form Longitude (DDDmm.mm)
            long_degrees = packet_list[radio_constants.LONGITUDE][:3]
            long_minutes_seconds = packet_list[radio_constants.LONGITUDE][3:]

            east_west = '' if packet_list[radio_constants.LONGITUDE_EW] == 'E' else '-'
            longitude = 'log = ' + east_west + long_degrees + degree_sign_utf8 + long_minutes_seconds + minutes_sign
            lat_long = longitude + latitude
        return lat_long

    def run(self):
        """
        This overrides run on the threading class

        :return:
        """
        connected = False
        counter = 0
        local_socket = None
        while True:
            if not connected:
                local_socket, client, address = self.connect(mac_address=self.mac_address, timeout=self.timeout)
                if not client or not address:
                    print('did not connect, so wait {} and continue'.format(self.timeout))
                    time.sleep(self.timeout)
            else:
                # ok we are connected.
                packet_list = self.lock_location_class.gps_location
                lat_long = self.process_packet(packet_list)
                send_status = self.send_data(client, address, lat_long)
                if not send_status:
                    client.close()
                    local_socket.close()
                    connected = False
                    print('not connected')
                counter = counter + 1 if counter < 16 else 0
                # test to see if the it is time to exit
                if self.event.is_set():
                    return
                time.sleep(1)