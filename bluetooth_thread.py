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

hostMACAddress = 'DC:A6:32:06:56:1D' # The MAC address of a Bluetooth adapter on the server. The server might have multiple Bluetooth adapters.
port = 3 # 3 is an arbitrary choice. However, it must match the port used by the client.
backlog = 1
size = 1024
local_socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
local_socket.bind((hostMACAddress,port))
local_socket.listen(backlog)
client = None
try:
    client, address = local_socket.accept()
    while 1:
        data = client.recv(size)
        print('datatype = {} data={}'.format(type(data), data))
        mystr_list = bytearray('abcdef{}\n'.format(data.decode("utf-8")), 'utf-8')
        length = client.send(mystr_list)
        print('length send ={}'.format(length))
except:
    print("Closing socket")
    client.close()
    local_socket.close()

class BluetoothSocketThread(threading.Thread):
    """
    A thread to endless attempt to open a bluetooth socket to a paired phone on a mac address
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
        super(BluetoothSocketThread, self).__init__(name=name, args=args, kwargs=kwargs)

        if args is None:
            raise ValueError('Args cannot be None')

        if args is None:
            raise ValueError()
        self.args = args
        self.kwargs = kwargs
        self.socket_data_lock = self.args[0]
        self.name = name
        self.event = self.args[1]
        self.mac_address = self.kwargs['mac_address']
        self.timeout = self.kwargs.get('timeout', 10)

    def connect(self, mac_address, timeout=10):
        """
        connect to blue tooth client

        :param mac_address: the mac address of the client to which we will connect
        :return: at tuple with the client, and address if successfule, False, false if it fails
        """
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
            return False, False
        print('socket accepted, ')
        return client, address

    def run(self):
        """
        override the threading run

        :return:
        """
        while True:
            client, address = self.connect(self.mac_address, self.timeout)
            if not client or not address:
                print('connect failed, try again in 1 second')
            if self.event.is_set():
                print('event Terminate thread')
                return
            time.sleep(1)

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

    def connect(self, mac_address, timeout):
        """
        connect to blue tooth client

        :param mac_address: the mac address of the client to which we will connect
        :return: at tuple with the client, and address if successfule, False, false if it fails
        """
        hostMACAddress = mac_address  # The MAC address of a Blue tooth adapter on the server. The server might have multiple Bluetooth adapters.
        port = 3  # 3 is an arbitrary choice. However, it must match the port used by the client.
        backlog = 1
        size = 1024
        local_socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        local_socket.bind((hostMACAddress, port))
        local_socket.settimeout(10)
        local_socket.listen(backlog)
        try:
            client, address = socket.accept()
        except Exception as error:
            print("accept error=\'{}\'".format(error))
            socket.close()
            return False, False
        return client, address

    def run(self):
        """
        This overrides run on the threading class

        :return:
        """

        # this is the degree sign for displaying to the display and is specific to the font5x8
        while True:
            client, address = self.connect(mac_address=self.mac_address, timeout=self.timeout)
            if not client:
                print('connection failed, tryinmg again')
                time.sleep(1)
            if self.event.is_set():
                return
            time.sleep(1)

    def send_data(self, client, address, data):
        """

        :param client: the client address to which to send the data
        :param address: the receiver address
        :param data: the data to send
        :return True if the send is successful or False if not
        """

        try:
            byte_data_array = bytearray('{}\n'.format(data, 'utf-8'))
            length = client.send(byte_data_array)
            print('length send ={}'.format(length))
        except:
            return False
        return True


    def run(self):
        """
        This overrides run on the threading class

        :return:
        """

        # this is the degree sign for displaying to the display and is specific to the font5x8
        degree_sign_utf8 = u"\u00b0"
        minutes_sign = u"\u0027"

        counter = 0
        while True:
            packet_list = self.lock_location_class.gps_location
            # short circuit will prevent the exception in the second half
            if packet_list is None or packet_list[radio_constants.VALID] != 'A':
                continue
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

            counter = counter + 1 if counter < 16 else 0
            # test to see if the it is time to exit
            if self.event.is_set():
                return
            time.sleep(1)