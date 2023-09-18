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

import datetime
import threading


class Logging:
    """
    This is a simple logger for the rfm radio
    """
    def __init__(self, log_level=None):
        """
        The init class for the lock and location
        """
        if log_level is None:
            self.log_level = 'info'
        else:
            self.log_level = log_level
        if self.log_level not in ['info', 'debug']:
            raise ValueError(f'Log level {log_level} is not one of debug or info')
        self.__lock = threading.Lock()


    def log(self,  data: str = None):
        """
        Log the screen to the output

        :param data: string to be logged
        """
        if self.log_level == 'info':
            self._log_data(data)

    def debug(self,  data: str = None):
        """
        Log debug data

        :param data: the data to print
        """
        if self.log_level == 'debug':
            self._log_data(data)

    def _log_data(self, data: str = None):
        """
         common writer

        :param data: the data to print
        """
        data = '' if data is None else data
        self.__lock.acquire()
        current_time = datetime.datetime.now()
        string_time = current_time.strftime("%y:%b:%H:%M:%S")
        print(string_time + " " + data)
        self.__lock.release()