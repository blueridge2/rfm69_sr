#!/usr/bin/env python
####################################################################################################################################
# Copyright 2020 Ralph Carl Blach III
# Other copyright by Brent Rubel for Adafruit industries.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR
# ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH
# THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#######################################################################################################################################

# This is a program to read data sent by the Arduino program sketch_apr11a
# Learn Guide: https://learn.adafruit.com/lora-and-lorawan-for-raspberry-pi
# Author: Brent Rubell for Adafruit Industries
# Author: Ralph Blach reworked for my purposes
# you will need to download font5x8.bin from https://github.com/adafruit/Adafruit_CircuitPython_framebuf/raw/master/examples/font5x8.bin
# you could use  wget -O font5x8.bin https://github.com/adafruit/Adafruit_CircuitPython_framebuf/blob/master/examples/font5x8.bin?raw=true
#
# the callsign and rfm69 radio network are stored in a file called callsign.  The first six bytes are the callsign and the next two bytes
# are the radio network.  Only the first 8 bytes of the file are used.  The if thee call sign is less than 6 bytes, then it must be padded with
# spaces
#
# The header is 4 bytes
# byte 0 is the target address,( this machine as the receiver)
# byte 1 is the source address( the sender/transmitter)
# byte 2 not used by this program( a counter set by the sender/transmitter)
# byte 3 status 0 = Data 0x80 is an ack

# valid packet minus the 4 byte header will look like ['kf4wbk', 'A', '4009.6037', 'N', '10503.7000', 'W']
# an invalid packet minus the 4 byte header will look like ['kf4wbk', 'V']

# Import Python System Libraries
import argparse
# import logging
import os
import time
import threading
# Import Blinka Libraries
# import the SSD1306 module.
import adafruit_ssd1306
# Import the RFM69 radio module.
import adafruit_rfm69
import busio
import board
from digitalio import DigitalInOut
from digitalio import Direction
from digitalio import Pull
import lock_and_data
import bluetooth_thread
import radio_constants


class DisplayLocation(threading.Thread):
    """
    this is a thread class for the bluetooth radio

    """
    __slots__ = ['name', 'args', 'lock_location_class', 'event']

    def __init__(self, name, *args):
        """
        this is the init class for the thread

        :param name: The name of the thread
        :param args: The args, it must be a tuple consisting go the lock variable, the shared data, must be a list
                     the second arg is the event so cause a shutdown if button a is pushed
        :param kwargs: Noe used
        """
        super(DisplayLocation, self).__init__(name=name, args=args)

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
        # Create the I2C interface.
        i2c = busio.I2C(board.SCL, board.SDA)
        # this is the degree sign for displaying to the display and is specific to the font5x8
        degree_sign_bonnet = u"\u00f8"
        minutes_sign = u"\u0027"
        # now display the data
        display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, addr=0x3c)
        counter = 0
        # run around in loop getting data
        while True:
            display.fill(0)
            display.text('Remote Location', 0, 0, 1)
            display.show()

            packet_list = self.lock_location_class.data

            if packet_list is None:
                display.text('not valid {}'.format('no packet'), 0, 8, 1)
                display.show()
                time.sleep(1)
                continue
            else:
                callsign = packet_list[radio_constants.CALLSIGN]
                if packet_list[radio_constants.VALID] != 'A':
                    # the packet does not have a valid gps location
                    display.text('not valid {}'.format(callsign), 0, 8, 1)
                    display.show()
                    continue

            # latitude has the form of Latitude (DDmm.mm)
            lat_degrees = packet_list[radio_constants.LATITUDE][:2]
            lat_minutes_seconds = packet_list[radio_constants.LATITUDE][2:]
            north_south = '' if packet_list[radio_constants.LATITUDE_NS] == 'N' else '-'
            latitude = 'lat = ' + north_south + lat_degrees + degree_sign_bonnet + lat_minutes_seconds + minutes_sign
            # latitude_to_bluetooth = north_south + lat_degrees + degree_sign_utf8 + lat_minutes_seconds + minutes_sign
            # longitude has the form Longitude (DDDmm.mm)
            long_degrees = packet_list[radio_constants.LONGITUDE][:3]
            long_minutes_seconds = packet_list[radio_constants.LONGITUDE][3:]

            east_west = '' if packet_list[radio_constants.LONGITUDE_EW] == 'E' else '-'
            longitude = 'log = ' + east_west + long_degrees + degree_sign_bonnet + long_minutes_seconds + minutes_sign
            # longitude_to_bluetooth = east_west + long_degrees + degree_sign_utf8 + long_minutes_seconds + minutes_sign
            display.text(latitude, 0, 8, 1)
            display.text(longitude, 0, 16, 1)
            display.text('valid, {} {:01x}'.format(callsign, counter & 0xf), 0, 24, 1)
            display.show()
            counter = counter + 1 if counter < 16 else 0
            # test to see if the it is time to exit
            if self.event.is_set():
                return
            time.sleep(1)


class ReceiveRFM69Data(threading.Thread):
    """
    the class to receive from th rfm69 radio module
    """
    # prevent adding external weak adds
    __slots__ = ['name', 'args', 'lock_location_class', 'event', 'network']

    def __init__(self, name, *args):
        """
        The init function is empty for now.

        :param name: name the name of the thread
        :param location_data: the class that contains the gps location
        :param args: the tuple containing the gps lock and data
        :param kwargs: not used at this time

        """
        super(ReceiveRFM69Data, self).__init__(name=name, args=args)
        self.name = name
        self.args = args

        if args is None:
            raise ValueError('args cannot be None')
        self.lock_location_class = self.args[0]
        self.event = self.args[1]
        self.network = self.args[2]

    def run(self):
        """
        This runs the radio

        It does not exit and it does not return
        """
        button_a = DigitalInOut(board.D5)
        button_a.direction = Direction.INPUT
        button_a.pull = Pull.UP

        # board interrupt ping gpio 22
        gpio22 = DigitalInOut(board.D22)
        gpio22.direction = Direction.INPUT
        gpio22.pull = Pull.UP

        # Configure Packet Radio
        chip_select = DigitalInOut(board.CE1)
        reset_radio = DigitalInOut(board.D25)
        spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        # rfm69 = adafruit_rfm69.RFM69(spi, chip_select, reset_radio, 433.0, sync_word=b'\x2D\xD4')
        rfm69 = adafruit_rfm69.RFM69(spi, chip_select, reset_radio, 433.0, sync_word=self.network)
        while True:
            if not button_a.value:
                # Send Button A
                # button_a_data = bytes("Button A!\r\n", "utf-8")
                self.event.set()
                time.sleep(1)
                return
            # check for packet rx
            packet = rfm69.receive(with_header=True, rx_filter=1)
            if packet is not None:
                # send the data to data class
                header = packet[0:4]
                processed_packet = packet[4:]
                packet_text = str(processed_packet, "utf-8")
                packet_list = packet_text.split(',')
                self.lock_location_class.data = packet_list
                if packet_list[radio_constants.VALID] != 'A':
                    # the packet does not have a valid gps location
                    self.lock_location_class.data = 'not valid'
                    time.sleep(1)
                    continue
                # longitude has the form Longitude (DDDmm.mm)
                ack_data = bytes('a', 'utf-8')
                # create of tuple of to, from, id, status,
                ack_tuple = (header[1], header[0], header[2], 0x80)
                rfm69.send(ack_data, tx_header=ack_tuple)
            time.sleep(1)


def check_file(filename, length):
    """
    check a file for existence and print message

    :param filename: the file name to check
    :param length the number of characters to read
    :return:
    """
    try:
        file_handle = open(filename, "rb")
    except Exception as error:
        print('file {} found our accessible, error=error={}'.format(filename, error))
        exit(-1)

    return file_handle.read(length)


def run():
    """
    run the main program
    :return: none
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('--level', choices=['info', 'debug'], default='debug', help='The debug log level (default: %(default)s)')
    parser.add_argument('--log_fn', type=str, default='/tmp/rfm_radio', help='Default log file name - (default: %(default)s)')
    parser.add_argument('--call_sign', type=str, default='./call_sign', help='Binary file that contains the '
                                                                             'call sign and network default:  %(default)s)')
    args = parser.parse_args()
    debug_level = args.level
    # log_file = args.log_fn
    print('args = {}'.format(debug_level))

    if not os.path.exists('font5x8.bin'):
        print('the file font5x8.bin is not present in the current directory.')
        print('use the command wget -O font5x8.bin \
                https://github.com/adafruit/Adafruit_CircuitPython_framebuf/blob/master/examples/font5x8.bin?raw=true to download')
        exit(-1)
    if not os.path.exists(args.call_sign):
        print('the file {} is not present'.format(args.call_sign))
        exit(-1)
    mac_address = check_file('mac_address', radio_constants.BLUETOOTH_MAC_LENGTH)
    callsign_network = check_file(args.call_sign, radio_constants.CALLSIGN_LENGTH)

    network = callsign_network[6:]
    dictionary_args = {'MacAddress': mac_address, 'TimeOut': 30}
    # set up an event for exit and make sure it is clear
    event = threading.Event()
    event.clear()
    # create the gps_loc_and location class
    gps_lock_and_location = lock_and_data.LockAndData()

    # create and run the threads
    radio_args = (gps_lock_and_location, event, network)
    run_radio = ReceiveRFM69Data('rfm_radio', *radio_args)
    run_display = DisplayLocation('display data', *radio_args)

    bluetooth_args = (gps_lock_and_location, event, dictionary_args)
    connect_bluetooth = bluetooth_thread.BluetoothTransmitThread('Bluetooth connection', *bluetooth_args, **dictionary_args)

    run_radio.start()
    run_display.start()
    connect_bluetooth.start()

    connect_bluetooth.join()
    run_radio.join()
    run_display.join()


if __name__ == "__main__":
    run()
