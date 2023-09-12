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
from typing import Final
CALLSIGN: Final[int] = 0
TIME_OF_FIX: Final[int] = 1
POSITION_VALID: Final[int] = 2
LATITUDE: Final[int] = 3
LATITUDE_NS: Final[int] = 4
LONGITUDE: Final[int] = 5
LONGITUDE_EW: Final[int] = 6
FIX_DATE: Final[int] = 7
BLUETOOTH_MAC_LENGTH: Final[int] = 17
CALLSIGN_LENGTH: Final[int] = 8     # 6 CHARACTERS + 2 FOR NETWORK
