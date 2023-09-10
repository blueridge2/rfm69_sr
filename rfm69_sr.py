#!/usr/bin/env python
####################################################################################################################################
# Copyright 2020, 2023 Ralph Carl Blach III
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
# the bluetooth mac address is the Mac address of the local bluetooth device and this is gotten by using hci tool.
#
# The header is 4 bytes
# byte 0 is the target address,( this machine as the receiver)
# byte 1 is the source address( the sender/transmitter)
# byte 2 not used by this program( a counter set by the sender/transmitter)
# byte 3 status 0 = Data 0x80 is an ack


# valid packet minus the 4 byte header will look like ['kf4wbk', '2', '4009.6037', 'N', '10503.7000', 'W']
# an invalid packet minus the 4 byte header will look like ['kf4wbk', 'V']
# the program depends on GGA nema sentence position fix indicator from the GGA sentence
# Position Fix Indicator table
#        | Value | Description |
#        |:------:|:---------------------------------------------:|
#        | 0 | Fix not available or not valid|
#        | 1 | GPS SPS Mode, fix Valid |
#        | 2 | Differential GPS, SPS Mode, fix valid |
#        | 3 - 5| Not supported |
#        | 6 | Dead Reckoning Mode, fix valid |

# Import Python System Libraries
import argparse
import os
import time
import threading
import re
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
import logging
import bluetooth_thread
import radio_constants
import subprocess


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
        self.log = self.args[2]

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
                if packet_list[radio_constants.POSITION_FIX_INDICATOR] == '0':
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
            display.text('vld={}, {} {:01x}'.format(packet_list[radio_constants.POSITION_FIX_INDICATOR], callsign, counter & 0xf), 0, 24, 1)
            display.show()
            counter = counter + 1 if counter < 16 else 0
            # test to see if is time to exit
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
        self.log = self.args[3]

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
            packet = rfm69.receive(with_header=True)
            if packet is not None:
                # send the data to data class
                header = packet[0:4]
                processed_packet = packet[4:]
                packet_text = str(processed_packet, "utf-8")
                self.log(f'packet.txt={packet_text}')
                packet_list = packet_text.split(',')
                self.log(f'packet_list={packet_list}')
                self.lock_location_class.data = packet_list
                if packet_list[radio_constants.POSITION_FIX_INDICATOR] == '0':
                    # the packet does not have a valid gps location
                    self.lock_location_class.data = 'not valid'
                    time.sleep(1)
                    continue
                # longitude has the form Longitude (DDDmm.mm)
                ack_data = bytes('a', 'utf-8')
                # create of tuple of to, from, id, status,
                # ack_tuple = (header[1], header[0], header[2], 0x80)
                self.log('got a valid packet send ack')
                rfm69.send(ack_data, destination=header[1], node=header[0], identifier=header[2], flags=0x80)
            time.sleep(1)


def check_file(filename, length):
    """
    check a file for existence and print message

    :param filename: the file name to check
    :param length the number of characters to read
    :return:
    """
    log = logging.log()
    try:
        file_handle = open(filename, "rb")
    except Exception as error:
        log.log('file {} found our accessible, error=error={}'.format(filename, error))
        exit(-1)

    return file_handle.read(length)


def get_local_bluetooth_mac_address():
    """
    get the local bluetooth mack address by suing the hcitool
    @returns the local bluetooth mac address, or the return code
    """
    log = logging.Logging()
    result = subprocess.run(['hcitool', 'dev'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    log.log(f'result return code={result.returncode}')
    if result.returncode:
        log.log(f'{result.args} command did not execute successfully')
        return result.returncode, False
    standard_out = result.stdout.decode('utf-8').splitlines()
    mac_address_line = standard_out[1].split()
    mac_address = mac_address_line[1]
    log.log(f'using mac_address={mac_address}')
    return result.returncode, mac_address


def run():
    """
    run the main program
    :return: none
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('--level', choices=['info', 'debug'], default='debug', help='The debug log level (default: %(default)s)')
    parser.add_argument('--log_fn', type=str, default='/tmp/rfm_radio', help='Default log file name - (default: %(default)s)')
    parser.add_argument('--call_sign', type=str, default='./call_sign', help='Binary file that contains the call sign:  %(default)s)')
    parser.add_argument('--sync_word', type=int, default=0x2dd4, help='Binary file that contains the network default:  %(default)s)')
    parser.add_argument('--mac_address', type=str, default=None, help='Siring that has the Mac address fo the bluetooth device,:  %(default)s)')
    parser.add_argument('--rfcomm_port', type=int, default=4, help='The rfcomm port:  %(default)s)')
    args = parser.parse_args()
    debug_level = args.level
    # log_file = args.log_fn
    log = logging.Logging()
    log.log('args = {}'.format(debug_level))

    if not os.path.exists('font5x8.bin'):
        log.log('the file font5x8.bin is not present in the current directory.')
        log.log('use the command wget -O font5x8.bin \
                https://github.com/adafruit/Adafruit_CircuitPython_framebuf/blob/master/examples/font5x8.bin?raw=true to download')
        exit(-1)
    if not os.path.exists(args.call_sign):
        log.log('the file {} is not present'.format(args.call_sign))
        exit(-1)
    if args.mac_address:
        mac_address = args.mac_address.upper()
        log.log(f"mac address = {mac_address}")
        mac_reg_expression = r'[A-F0-9]{2}:[A-F0-9]{2}:[A-F0-9]{2}:[A-F0-9]{2}:[A-F0-9]{2}:[A-F0-9]{2}'
        re_match = re.match( mac_reg_expression, mac_address)
        if re_match is None:
            raise ValueError('The bluetooth Mac address did not match the form xx:xx:xx:xx')
        mac_address = re_match.group()
    else:
        got_mac, mac_address = get_local_bluetooth_mac_address()
        if got_mac:
            raise ValueError('Failed to get the mac address from the device')
    log.log(f'bluetooth mac address = {mac_address}')
    # callsign_network = check_file(args.call_sign, radio_constants.CALLSIGN_LENGTH)
    network = args.sync_word.to_bytes(length=2, byteorder='big')

    dictionary_args = {'MacAddress': mac_address, 'TimeOut': 30, 'RfcommPort': args.rfcomm_port}
    # set up an event for exit and make sure it is clear
    event = threading.Event()
    event.clear()
    # create the gps_loc_and location class
    gps_lock_and_location = lock_and_data.LockAndData()

    # create and run the threads
    radio_args = (gps_lock_and_location, event, network, log.log)
    run_radio = ReceiveRFM69Data('rfm_radio', *radio_args)
    run_display = DisplayLocation('display data', *radio_args, log.log)

    bluetooth_args = (gps_lock_and_location, event, dictionary_args, log.log)
    connect_bluetooth = bluetooth_thread.BluetoothTransmitThread('Bluetooth connection', *bluetooth_args, **dictionary_args)

    run_radio.start()
    run_display.start()
    connect_bluetooth.start()

    connect_bluetooth.join()
    run_radio.join()
    run_display.join()


if __name__ == "__main__":
    run()
