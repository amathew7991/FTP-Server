#!/usr/bin/env python

import sys
import os
from datetime import datetime

"""
Author: Andrea Mathew
Created: 10/06/19
logger.py
Description: Logger class to handle logging for ftp client
"""


class Logger:
    def __init__(self, filename="logs.txt"):
        self.file = open(filename, "a+")

    def received(self, message):
        # Logs received messages from server
        self.file.write("\n" + str(self.time()) + " Received:  " + message[:-1])

    def connecting(self, hostname):
        # Logs that the client is connecting to specified host
        self.file.write("\n" + str(self.time()) + " Connecting to " + hostname)

    def sent(self, message):
        # Logs message sent to the server
        message.replace("\r\n", "")
        self.file.write("\n" + str(self.time()) + " Sent: " + message[:-1])

    def error(self, message):
        # Logs an error message
        self.file.write("\n" + str(self.time()) + " ERROR " + message)

    def quit(self):
        # Logs the user quitting the ftp prompt
        self.file.write("\n" + str(self.time()) + " Client quit, connection closed")

    def time(self):
        timestamp = datetime.now()
        return timestamp

    # Added logging for server
    def serverstarted(self, hostname):
        self.file.write("\n" + str(self.time()) + " Server listening at " + hostname)

