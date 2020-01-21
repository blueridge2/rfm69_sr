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

class BluetoothThread(threading.Thread):
    """
    this is a thread class for the bluetooth radio

    """
    def __init__(self, name, *args, **kwargs):
        """
        this is the init class for the thread

        :param name: The name of the thread
        :param args: The args, it must be a tuple consisting go the lock variable, the shared data, must be a list
                     the second arg is the event so cause a shutdown if button a is pushed
        :param kwargs: Noe used
        """
        super(BluetoothThread, self).__init__(name=name, args=args, kwargs=kwargs)

        if args is None:
            raise ValueError('Args cannot be None')

        if args is None:
            raise ValueError()
        self.args = args
        self.lock_location_class = self.args[0]
        self.name = name
        self.event = self.args[1]

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
            if packet_list is not None:
                callsign = packet_list[radio_constants.CALLSIGN]
                if packet_list[radio_constants.VALID] != 'A':
                    # the packet does not have a valid gps location
                    continue
            # latitude has the form of Latitude (DDmm.mm)
            lat_degrees = packet_list[radio_constants.LATITUDE][:2]
            lat_minutes_seconds = packet_list[radio_constants.LATITUDE][2:]
            north_south = '' if packet_list[radio_constants.LATITUDE_NS] == 'N' else '-'
            latitude = 'lat = ' + north_south + lat_degrees + degree_sign_utf8 + lat_minutes_seconds + minutes_sign
            # latitude_to_bluetooth = north_south + lat_degrees + degree_sign_utf8 + lat_minutes_seconds + minutes_sign
            # longitude has teh form Longitude (DDDmm.mm)
            long_degrees = packet_list[radio_constants.LONGITUDE][:3]
            long_minutes_seconds = packet_list[radio_constants.LONGITUDE][3:]

            east_west = '' if packet_list[radio_constants.LONGITUDE_EW] == 'E' else '-'
            longitude = 'log = ' + east_west + long_degrees + degree_sign_utf8 + long_minutes_seconds + minutes_sign
            # longitude_to_bluetooth = east_west + long_degrees + degree_sign_utf8 + long_minutes_seconds + minutes_sign

            counter = counter + 1 if counter < 16 else 0
            # test to see if the it is time to exit
            if self.event.is_set():
                return
            time.sleep(1)