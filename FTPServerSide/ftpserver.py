#!/usr/bin/env python3
"""
Author: Andrea Mathew
Created: 10/24/19
CS472 Homework 3
ftpserver.py
Description : FTP server
"""
# Import libraries
import socket
import sys
import re
import os
import threading
import os
# import logging
from logger import Logger


class ServerSocket:
    """
    Set up a listening socket to client
    Accept a client, listen for requests, close connection
    """

    def __init__(self, logfile, port=2121):
        """
        Initialize ServerSocket with logfile and portnumber
        :param logfile: logfile from client
        :param port: opened port server is listening on
        """
        self.port = port
        # Create listening socket
        try:
            self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except self.serversocket.error as e:
            print("Socket creation failed with error: " + e)

        # Bind socket to port and ip
        self.serversocket.bind((socket.gethostname(), self.port))
        self.serversocket.listen(5)
        print("server listening: ip %s, port %s" % (socket.gethostbyname(socket.gethostname()), self.port))

    # Returns client socket and address of client connection
    def accept(self):
        return self.serversocket.accept()

    def close(self):
        self.serversocket.close()


class FTPServer(threading.Thread):
    """
    Concurrent FTP server
    """

    def __init__(self, clientsocket, address, logfile):
        """
        Create FTP server using client socker connection
        :param clientsocket: client socket to connect to
        :param address: address returned from .accept()
        :param logfile: log file passed into Logger object
        """
        self.clientsocket = clientsocket
        self.address = address
        self.username = ""
        self.password = ""
        self.addressip = address[0]
        self.addressport = address[1]
        self.datasocket = None
        self.passivemode = False
        self.passivemodesocket = None
        self.logger = Logger(logfile)
        self.portdata = None
        self.passivedata = None
        self.loggedin = False

    def threading(function):
        """
        Create thread for multiple clients
        :param function: function that needs to use threading
        :return: none
        """
        def threadwrapper(self, *args):
            thread = threading.Thread(target=function, args=(self,))
            thread.start()
        return threadwrapper

    @threading
    def runprotocol(self):
        """
        Handles beginning the protocol from the server side by looping until the client closes connection
        :return: none
        """
        self.logger.serverstarted(self.addressip)
        self.serviceready()
        newclientrequest = self.receive()
        self.user(newclientrequest)
        self.passwd()
        # get SYST command from client
        if (self.receive()[:4] == "SYST"):
            opsys = sys.platform
            response = "215 System: " + opsys
            self.send(response)
        else:
            pass
        while True:
            # If the client quits close the connection
            clientrequest = self.receive()
            self.parseclientrequest(clientrequest)
            if clientrequest[:4] == "QUIT":
                print("Client closed connection")
                break

    def parseclientrequest(self, clientrequest):
        """
        Helper function to parse through commands send from client and call respective built response function
        :param clientrequest: full request line from client
        :return: none
        """
        command = (clientrequest.split())[0]
        if command == "QUIT":
            self.quit()
        if self.loggedin == True:
            if command == "PWD":
                self.pwd()
            elif command == "CWD":
                path = (clientrequest.split())[1]
                self.cwd(path)
            elif command == "CDUP":
                self.cdup()
            elif command == "PORT":
                # pass in connection data
                self.passivemode = False
                connectiondata = (clientrequest.split("PORT ", 1))[1]
                self.portdata = connectiondata
                self.port()
            elif command == "PASV":
                self.passivemode = True
                self.pasv()
            elif command == "LIST":
                self.list()
            elif command == "STOR":
                file = (clientrequest.split())[1]
                self.stor(file)
            elif command == "RETR":
                file = (clientrequest.split())[1]
                self.retr(file)
            elif command == "EPSV":
                self.epsv()
            elif command == "EPRT":
                self.eprt()
        else:
            self.send("500 Not authorized")

    def serviceready(self):
        """
        Send to user that FTP service is ready to use once connecting
        :return:
        """
        # Send 220 service ready message
        self.send("220 Welcome to FTP server")

    def send(self, command):
        """
        Handles sending response commands to client socket and logs message sent
        :param command: command from client to run
        :return:
        """
        command = command + "\r\n"
        self.clientsocket.sendall(command.encode())
        self.logger.sent(command)

    def receive(self):
        """
        Handles receiving commands from the client socket and logs what was received
        :return: none
        """
        try:
            clientdata = self.clientsocket.recv(4096)
            self.logger.received(clientdata.decode())
            return clientdata.decode()
        except socket.error as e:
            print(e)

    def authuser(self, user, password):
        """
        Checks if user and pass are authorized by reading authusers.txt
        :param user: authorized user name
        :param password: authorized password
        :return: True if user and password pair exists in authorized users file
        """
        authusersfile = open("authusers.txt", "r")
        # loop through auth users file
        for line in authusersfile:
            if user in line:
                # get password matched to it and check
                authpassword = (line.split(":"))[1]
                if password.split() == authpassword.split():
                    return True
                else:
                    return False

    def user(self, command):
        """
        Response to client sending USER
        :param command: full command from the client socket
        :return:
        """
        # split user command and get username
        self.username = (command.split())[1]
        self.send("331 Please specify the password.")

    def passwd(self):
        """
        Response to client sending PASS
        :return: none
        """
        # Validate username and password
        usercommand = self.receive()
        self.password = (usercommand.split())[1]
        # check that user pass pair are in auth users file
        if self.authuser(self.username, self.password):
            self.send("230 Login successful.")
            self.loggedin = True
        else:
            self.send("530 Login incorrect")

    def pwd(self):
        """
        Response to client sending PWD
        print the working directory of the server
        :return: none
        """
        currentdir = os.getcwd()
        self.send("257 %s is the current directory" % currentdir)

    def cwd(self, path):
        """
        Response to client sending CWD
        changes to specified directory given that the path exists
        :param path: directory to change to
        :return: none
        """
        # Check if path exists
        if os.path.isdir(path):
            os.chdir(path)
            self.send("250 Directory successfully changed.")
        else:
            self.send("550 Failed to change directory.")

    def cdup(self):
        """
        Response to client sending CDUP
        Changes to parent directory of current directory
        :return: none
        """
        # 250 Directory successfully changed.
        os.chdir("..")
        self.send("250 Directory successfully changed.")

    def datasocketsend(self, data):
        """
        Handles responses that need to send data through second data socket connection
        :param data: data to send through data socket
        :return: none
        """
        response = "425 Failed to open data connection"
        try:
            # open socket connection
            dsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.passivemode:  # use passive socket connection
                (dsocket, self.address) = self.passivemodesocket.accept()

            # send data through connection
            for x in data:
                responsedata = (x + "\r\n").encode()
                dsocket.send(responsedata)

            # close data socket connection
            dsocket.close()
            if self.passivemode:
                self.passivemodesocket.close()

        except socket.error as e:
            print(e)

    def pasv(self):
        """
        Response to client sending PASV
        Uses passive mode for data transfer commands
        :return:
        """
        # get ip address
        hostaddress = socket.gethostbyname(socket.gethostname())
        self.passivemodesocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        iparray = hostaddress.split(".")
        h1 = iparray[0]
        h2 = iparray[1]
        h3 = iparray[2]
        h4 = iparray[3]
        # get port number
        port = self.addressport
        modulo = port % 256
        p1 = int((port - modulo) / 256)
        p2 = modulo
        connectiondata = "(%s,%s,%s,%s,%s,%s)" % (h1, h2, h3, h4, p1, p2)
        self.passivedata = "%s,%s,%s,%s,%s,%s" % (h1, h2, h3, h4, p1, p2)
        self.send("227 Entering Passive Mode. " + connectiondata)

    def port(self):
        """
        Response to client sending PORT
        Uses active mode for data transfer commands
        :return:
        """
        self.send("200 PORT command successful. Consider using PASV")

    def list(self):
        """
        Response to client sending LIST
        Lists the files and directories in current directory
        :return: none
        """
        self.send("150 Here comes the directory listing.")
        # open connection with port data
        if self.passivemode == False:
            portdata = self.portdata.split(",")
            host = "%s.%s.%s.%s" % (portdata[0], portdata[1], portdata[2], portdata[3])
            p1 = int(portdata[4])
            p2 = int(portdata[5])
            port = (p1 * 256) + p2
            dsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dsocket.connect((host, port))
            # send list through dsocket
            dirlist = os.listdir()
            for x in dirlist:
                data = (x + "\r\n").encode()
                dsocket.send(data)

            dsocket.close()
            self.send("226 Directory send Ok.")
        elif self.passivemode:
            dsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            (dsocket, self.address) = self.passivemodesocket.accept()

    def stor(self, filename):
        """
        Response to client sending STOR
        Stores file at the server
        :param filename: name of file to store at server
        :return: none
        """
        if os.path.isfile(filename):
            self.send("150 Ok to send data.")
            portdata = self.portdata.split(",")
            host = "%s.%s.%s.%s" % (portdata[0], portdata[1], portdata[2], portdata[3])
            p1 = int(portdata[4])
            p2 = int(portdata[5])
            port = (p1 * 256) + p2
            dsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dsocket.connect((host, port))
            filedata = dsocket.recv(4096)
            file = open(filename, "w+")
            writedata = filedata.decode()
            file.write(writedata)
            self.send("226 Transfer complete.")

    def retr(self, file):
        """
        Response to client sending RETR
        Gets file at the server and stores it at client
        :param file:
        :return:
        """
        if os.path.isfile(file):
            # Send file to the client through data connection
            self.send("150 Opening BINARY mode data connection")
            portdata = self.portdata.split(",")
            host = "%s.%s.%s.%s" % (portdata[0], portdata[1], portdata[2], portdata[3])
            p1 = int(portdata[4])
            p2 = int(portdata[5])
            port = (p1 * 256) + p2
            dsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dsocket.connect((host, port))
            # send file through socket
            filedata = open(file, "r")
            dsocket.send(file.encode())
            dsocket.close()
            self.send("226 Transfer complete.")
        else:
            self.send("500 No such file or directory")

    def epsv(self):
        """
        Response to client sending EPSV
        :return: none
        """
        # get ip address
        self.passivemode = True
        # open data connection before client does
        self.passivemodesocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.passivemodesocket.bind((self.addressip, 0))
        self.passivemodesocket.listen(5)

        hostaddress = self.addressip
        iparray = hostaddress.split(".")
        h1 = iparray[0]
        h2 = iparray[1]
        h3 = iparray[2]
        h4 = iparray[3]
        # get port number
        port = self.passivemodesocket.getsockname()[1]
        modulo = port % 256
        p1 = int((port - modulo) / 256)
        p2 = modulo
        connectiondata = "(%s,%s,%s,%s,%s,%s)" % (h1, h2, h3, h4, p1, p2)
        self.send("227 Entering Passive Mode. " + connectiondata)  # (h1, h2, h3, h4, p1, p2)
        # add what header and port to use

    def eprt(self):
        """
        Response to client sending EPRT
        :return:
        """
        self.send("200 EPRT command successful. Consider using EPSV")

    def quit(self):
        """
        Response to client sending QUIT
        closes connection between client and server and stops ftp prompt at client
        :return:
        """
        self.send("221 Goodbye.")
        # close connection with server
        self.clientsocket.close()

    # Disconnecting from server
    def close(self):
        """
        Disconnects client from server
        :return:
        """
        print("Close connection")


def main():
    """
    Parses user input and makes sure that all required arguments are passed in.
    Creates a server socket using port number passed in and then creates FTP server object to handle protocol
    :return:
    """
    if len(sys.argv) == 3:
        logfile = sys.argv[1]
        # pass logfile into FTPserver
        port = sys.argv[2]
        serversocket = ServerSocket(logfile, int(port))
        ftpserver = None
        #Loop for threading
        while True:
            try:
            # call accept on server socket to get client socket and address
                (clientsocket, connaddress) = serversocket.accept()
                # Pass in clientsocket to FTP server
                ftpserver = FTPServer(clientsocket, connaddress, logfile)
                ftpserver.runprotocol()
            except KeyboardInterrupt as error:
                print("Shutting down server")
                sys.exit()
    else:
        print("TO RUN: ftpserver.py <logfile> <port>")


if __name__ == "__main__":
    main()
