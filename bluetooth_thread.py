#!/usr/bin/env python
##################################################################################################################
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
##############################################################################################################

import threading
import os
import stat
import time
import socket
import radio_constants

def char_dev_exists(dev_node: str = None) -> bool:
    """
    function so see if a character device is present
    @param dev_node: of the device node
    @return bool, true if present, fails if not

    """
    try:
        stat_value = os.stat(dev_node)
    except FileNotFoundError as error:
        return False

    return True if stat.S_ISCHR(stat_value.st_mode) else False


class BluetoothTransmitThread(threading.Thread):
    """
    this is a thread class for the bluetooth radio
    """
    __slots__ = ['args', 'kwargs', 'lock_location_class', 'event', 'mac_address', 'timeout']

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

        self.args = args
        self.kwargs = kwargs
        self.lock_location_class = self.args[0]
        self.name = name
        self.event = self.args[1]
        self.mac_address = self.kwargs['MacAddress']
        self.timeout = self.kwargs.get('TimeOut', 10)

    @staticmethod
    def rfcomm_connect(device: str = '/dev/rfcomm0'):
        """
        connect to an rfcomm serial port on bluetooth
        @param device: the sting for an rfcomm device devaults to /dev/rfcomm0
        @returns file_object
        """
        device_exist = False
        while not device_exist:
            time.sleep(1)
            device_exists = char_dev_exists(device)
            if device_exists:
                break
        try:
            file_handle = open(device, "w")
        except OSError as error:
            return False
        return file_handle

    @staticmethod
    def connect(mac_address, timeout=30):
        """
        connect to blue tooth client

        :param mac_address: the mac address of the client to which we will connect
        :param timeout: the length of time in seconds to wait for a connect
        :return: at tuple with the client, and address if successful, False, false if it fails
        """
        port = 3  # 3 is an arbitrary choice. However, it must match the port used by the client.
        print(f'port = {port}')
        backlog = 1
        # size = 1024
        #
        local_socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        print(f'local_socket={local_socket}  mac address = {mac_address}')
        try:
            local_socket.bind((mac_address, port))
        except Exception as error:
            local_socket.close()
            print(f'bluetooth bindsocket failed error = {error}')
            return (False, False, False)
        else:
            print("bind worked ok")
        local_socket.listen(backlog)
        local_socket.settimeout(timeout)
        try:
            client, address = local_socket.accept()
        except Exception as error:
            print(f'bluetooth accept failed error = {error}')
            return (False, False, False)
        print('bluetooth accept passed')
        return local_socket, client, address

    @staticmethod
    def send_data(client, data):
        """
        send the data to the bluetooth client

        :param client: the client address to which to send the data
        :param data: the data to send,should be a string
        :return True if the send is successful or False if not
        """
        try:
            byte_data_array = bytearray(('{}\n'.format(data).encode('utf-8')))
            client.send(byte_data_array)
        except Exception:
            return False
        return True

    @staticmethod
    def process_packet(packet_list, counter):
        """
        process the packet
        :param packet: a list that is either a packet or none
        :param counter a counter ot show movement on phone
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
            lat_long = longitude + latitude + ' ' + '{}'.format(counter)
        return lat_long

    def run(self):
        """
        This overrides run on the threading class

        :return:
        """
        connected = False
        counter = 0
        file_handle = None
        while True:
            if self.event.is_set():
                return
            time.sleep(.5)
            if not connected:

                file_handle = self.rfcomm_connect('/dev/rfcomm0')

                connected = True
            elif connected:
                # ok we are connected.
                packet_list = self.lock_location_class.data
                lat_long = self.process_packet(packet_list, counter)
                counter = counter + 1 if counter < 16 else 0
                lat_long = lat_long + "counter" + "\r\n"
                try:
                    file_handle.write(lat_long)
                except OSError as error:
                    print(f'oserror on write = {error}')
                    connected = False
                    try:
                        file_handle.close()
                    except OSError as error1:
                        print(f'oserror on close ={error1} ')


