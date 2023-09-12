#!/usr/bin/env python
# Copyright 2023 Ralph Carl Blach III
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
import socket
import radio_constants


class LoggingThread(threading.Thread):
    """
    this is a thread class for the bluetooth radio
    When establishing a bluetooth socket, one uses the local bluetooth mac address
    """
    __slots__ = ['args', 'kwargs', 'lock_location_class', 'event', 'mac_address', 'timeout']

    def __init__(self, name, *args, **kwargs):
        """
        this is the init class for the thread

        :param name: The name of the thread
        :param args: The args, it must be a tuple consisting of
                                (gps_lock_and_location, event, network, log.log, args.sleep_time)
        :param kwargs: a dictionary that must contain the mac address and the timeout
                        example {'mac_address': xx:xx:xx:xx:xx, 'timeout':10}  the timeout is optional but the mac address is not
        """
        super(LoggingThread, self).__init__(name=name, args=args, kwargs=kwargs)

        if args is None:
            raise ValueError('Args cannot be None')

        self.args = args
        self.kwargs = kwargs
        self.lock_location_class = self.args[0]
        self.event = self.args[1]
        self.network = self.args[2]
        self.log = self.args[3]
        self.sleep_time_in_sec = self.args[4]
        self.log_file_name = self.args[5]
        self.name = name
        # truncate the log file to zero length


    def run(self):
        """
        This overrides run on the threading class

        :return:
        """
        log_file_object = open(self.log_file_name, "w+")
        log_file_object.truncate()
        log_file_object.close()
        self.log(f'logging thread {self.args}')
        counter = 0
        previous_lat_long = ""
        while True:

            if self.event.is_set():
                return
            packet_list = self.lock_location_class.data
            if not packet_list:
                continue
            callsign = packet_list[radio_constants.CALLSIGN]
            if packet_list[radio_constants.POSITION_VALID] == 'V':
                # the packet does not have a valid gps location
                self.log('Position indicator ={}'.format(packet_list[radio_constants.POSITION_VALID]))
                continue

            # latitude has the form of Latitude (DDmm.mm)
            latitude = packet_list[radio_constants.LATITUDE]
            longitude = packet_list[radio_constants.LONGITUDE]
            lat_long = longitude + " " + latitude + '\n'
            if lat_long != previous_lat_long:
                self.log(f'{self.name} {latitude}, {longitude} {counter}\r\n')
                previous_lat_long = lat_long
                counter += 1
                with open(self.log_file_name, "a") as file:
                    complete_log_string = packet_list[radio_constants.TIME_OF_FIX] + ' ' + \
                                          packet_list[radio_constants.FIX_DATE] + ' ' + lat_long
                    self.log(f'thread_name = {self.name} {complete_log_string}')
                    file.write(complete_log_string)

            time.sleep(self.sleep_time_in_sec)

