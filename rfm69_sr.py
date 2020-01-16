"""
This is a program to read data sent by the Arduino program sketch_apr11a

Learn Guide: https://learn.adafruit.com/lora-and-lorawan-for-raspberry-pi
Author: Brent Rubell for Adafruit Industries
Autonr: Ralph Blach reworked for my purposes
you will need to download font5x8.bin from https://github.com/adafruit/Adafruit_CircuitPython_framebuf/raw/master/examples/font5x8.bin

 valid packet minus the 4 byte header will look like ['kf4wbk', 'A', '4009.6037', 'N', '10503.7000', 'W']
 an invalid packet minus the 4 byte header will look like ['kf4wbk', 'V']
"""
# Import Python System Libraries
import time
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

CALLSIGN = 0
VALID = 1
LATITUDE = 2
LATITUDE_NS = 3
LONGITUDE = 4
LONGITUDE_EW = 5
# Button A
btnA = DigitalInOut(board.D5)
btnA.direction = Direction.INPUT
btnA.pull = Pull.UP

# Button B
btnB = DigitalInOut(board.D6)
btnB.direction = Direction.INPUT
btnB.pull = Pull.UP

# Button C
btnC = DigitalInOut(board.D12)
btnC.direction = Direction.INPUT
btnC.pull = Pull.UP

# board interrupt ping gpio 22
gpio22 = DigitalInOut(board.D22)
gpio22.direction = Direction.INPUT
gpio22.pull = Pull.UP


# Create the I2C interface.
i2c = busio.I2C(board.SCL, board.SDA)

# 128x32 OLED Display
display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, addr=0x3c)

# Clear the display.
display.fill(0)
display.show()
width = display.width
height = display.height

# Configure Packet Radio
CS = DigitalInOut(board.CE1)
RESET = DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
#rfm69 = adafruit_rfm69.RFM69(spi, CS, RESET, 434.0, sync_word=b'\x2d\xd4')
rfm69 = adafruit_rfm69.RFM69(spi, CS, RESET, 433.0)
prev_packet = None
# Optionally set an encryption key (16 byte AES key). MUST match both
# on the transmitter and receiver (or be set to None to disable/the default).
#rfm69.encryption_key = b'\x01\x02\x03\x04\x05\x06\x07\x08\x01\x02\x03\x04\x05\x06\x07\x08'

display.fill(0)
display.text('Remote Location', 0, 0, 1)
display.show()
counter = 0
while True:

    packet = None
    # draw a box to clear the image
    # check for packet rx
    packet = rfm69.receive(with_header=True, rx_filter=1)
    # print('packet={}'.format(packet))
    if packet is not None:
        display.fill(0)
        display.text('Remote Location', 0, 0, 1)
        display.show()
        # Display the packet text
        header = packet[0:4]
        processed_packet = packet[4:]
        packet_text = str(processed_packet, "utf-8")
        packet_list = packet_text.split(",")
        callsign = packet_list[CALLSIGN]
        if packet_list[VALID] != 'A':
            display.text('not valid {}'.format(callsign), 0, 8, 1)
            continue

        # latitude has the form of Latitude (DDmm.mm)
        lat_degrees = packet_list[LATITUDE][:2]
        lat_minutes_seconds = packet_list[LATITUDE][2:]
        north_south = '' if packet_list[LATITUDE_NS] == 'N' else '-'
        latitude = 'lat = ' + north_south + lat_degrees + " " +lat_minutes_seconds
        # longitude has teh form Longitude (DDDmm.mm)
        long_degrees = packet_list[LONGITUDE][:3]
        long_minutes_seconds = packet_list[LONGITUDE][3:]

        # print('long_list={}'.format(long_list))

        east_west = '' if packet_list[LONGITUDE_EW] == 'E' else '-'
        longitude = 'log = ' + east_west + long_degrees + " " + long_minutes_seconds
        display.text(latitude, 0, 8, 1)
        display.text(longitude, 0, 16, 1)
        display.text('valid, {}'.format(callsign),0, 24, 1)
        ack_data = bytes('a','utf-8')
        # create of tuple of to, from, id, status,
        send_tuple=(header[1], header[0], header[2], 0x80)

        rfm69.send(ack_data, tx_header=send_tuple)
        time.sleep(1)

    if not btnA.value:
        # Send Button A
        display.fill(0)
        button_a_data = bytes("Button A!\r\n","utf-8")
        rfm69.send(button_a_data)
        display.text('Sent Button A!', 25, 15, 1)
    elif not btnB.value:
        # Send Button B
        display.fill(0)
        button_b_data = bytes("Button B!\r\n","utf-8")
        rfm69.send(button_b_data)
        display.text('Sent Button B!', 25, 15, 1)
    elif not btnC.value:
        # Send Button C
        display.fill(0)
        button_c_data = bytes("Button C!\r\n","utf-8")
        rfm69.send(button_c_data)
        display.text('Sent Button C!', 25, 15, 1)

    display.show()
    time.sleep(1)

