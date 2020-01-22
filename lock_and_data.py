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


class LockAndData():
    """
    A class to contain common data for the lock class and location
    """
    def __init__(self):
        """
        The init class for the lock and location
        """
        self._lock = threading.Lock()
        self.data = None

    @property
    def data(self):
        """
        A function to lock the data, read it unlock the data and return with the location
        :return a string with the gps location
        """
        self._lock.acquire()
        location = self.__data
        self._lock.release()
        return location

    @data.setter
    def data(self, data):
        """
        A function to set the gps location

        :param data: the to saved in the class
        :return: None
        """
        self._lock.acquire()
        self.__data = data
        self._lock.release()
