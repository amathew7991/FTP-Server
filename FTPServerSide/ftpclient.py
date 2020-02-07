#!/usr/bin/env python3

# IMPORTS
import socket
import sys
import re
from logger import Logger

"""
Author: Andrea Mathew
Created: 10/06/19
ftpclient.py
Description: FTP client that can login and send valid commands to existing FTP server
"""


class ClientSocketConnection:
    """
    ClientSocketConnection handles sending and receiving data from the client
    """

    def __init__(self, host, logfilename="logs.txt", port=21):
        self.host = host
        self.logfilename = logfilename
        self.port = port
        self.datasocket = None
        self.logger = Logger(logfilename)
        self.ipv4 = False
        self.ipv6 = False
        try:
            self.clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as e:
            print ("Socket creation failed with error %" % (e))
        # Resolve Host for IPv4
        if (re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", host)):
            host_ip = host
            self.ipv4 = True
            try:
                host_ip = socket.gethostbyname(host)
            except socket.gaierror:
                print ("There was an error resolving the host")
                sys.exit()
            # Connect to server
            try:
                self.clientsocket.connect((host_ip, port))
                self.logger.connecting(host)
            except socket.error as e:
                print(e)
                sys.exit(0)

        # Resolve Host for IPv6
        elif (re.match(
                r"(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))",
                host)):
            host_ip = host
            self.ipv6 = True
            try:
                # Switch to IPv6 INET
                self.clientsocket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
            except socket.error as e:
                print ("Socket creation failed with error %" % (e))
            # Connect to server with IPv6
            try:
                self.clientsocket.connect((host_ip, port))
                self.logger.connecting(host)
            except socket.error as e:
                print(e)
                sys.exit(0)
        else:
            # FIX GET HOST NAME
            '''
            #Hostname passed in
            try:
                host_ip = socket.gethostbyname(host)
                print(host_ip)
            except socket.gaierror:
                print("There was an error resolving the host name")
                sys.exit()
            '''
            try:
                self.clientsocket.connect((self.host, 2121))
                self.logger.connecting(host)
                self.ipv4 = True
            except socket.error as e:
                print(e)


    def connected(self):
        """
        Check that socket is connected before starting protocol
        :return: True if socket is connected
        """
        if (self.clientsocket):
            # Client socket was successfully created
            return True
        else:
            return False

    def close(self):
        """
        Close client socket
        :return: none
        """
        self.clientsocket.close()

    def send(self, command):
        """
        Send parsed user command through client socket
        :param command: command sent to server
        :return: none
        """
        try:
            self.clientsocket.sendall(command.encode())
            self.logger.sent(command)
        except socket.error as e:
            print(e)
            sys.exit(0)

    def receive(self):
        """
        Receive data from the server, decode, and log message
        :return: decoded server response
        """
        try:
            serverdata = self.clientsocket.recv(4096)
            self.logger.received(serverdata.decode())
            print(serverdata.decode()[:-1])
            return serverdata.decode()
        except socket.error as e:
            print(e)


class ServerStream:
    """
    ServerStream handles sending and receiving messages and data from the FTP server
    """

    def __init__(self, clientsocket):
        self.socket = clientsocket
        self.datasocket = None
        self.username = "username"
        self.password = "password"
        self.commands = ["user", "pass", "pwd", "cd", "ls", "exit", "stor", "retr", "pasv", "port"]

    def runprotocol(self):
        """
        Begins and keeps protocol running until user quits
        :return: none
        """
        print("Connected to " + self.socket.host)
        self.enterusername()
        self.enterpassword()
        #add getting system response
        self.runsyst()
        self.ftpprompt()

    def ftpprompt(self):
        """
        Reads in raw user input from ftp prompt
        :return:
        """
        while True:
            # entire input from user
            usercommand = input("ftp>")  # Loop back when user has empty input
            if usercommand == "":
                pass
            elif usercommand == "quit" or usercommand == "exit":
                self.runquit()
                self.socket.logger.quit()
                break
            else:
                self.handleusercommand(usercommand)


    def handleusercommand(self, usercommand):
        """
        Helper function to determine which command to run
        :param usercommand: user input string
        :return:none
        """
        # cmd is the command to send to server
        cmd = (usercommand.split())[0]
        # commands with no args
        cmds = ["pwd", "passive"]
        if cmd in cmds:
            self.parsecommand(cmd)
        # commands that use args
        cmdargs = ["cd", "put", "get"]
        if cmd in cmdargs:
            if len(usercommand.split()) < 2:
                print("usage:  <cmd> <arg>")
                self.ftpprompt()
            arg = (usercommand.split())[1]
            self.parsecommandargs(cmd, arg)
        # commands that could be either
        cmdor = ["ls"]
        if cmd in cmdor:
            if len(usercommand.split()) == 1:
                # no path
                self.parsecommand(cmd)
            else:
                arg = (usercommand.split())[1]
                self.parsecommandargs(cmd, arg)
        if cmd not in ["pwd", "passive", "cd", "put", "get", "ls"]:
            print("?Invalid command")

    def parsecommand(self, cmd):
        """
        Helper function to run respective method depending on the users command
        :param cmd: user input string
        :return:
        """
        if cmd == "pwd":
            self.runpwd()
        elif cmd == "ls":
            self.runlist()
        elif cmd == "passive":
            self.runpasv()
        else:
            print("Invalid argument passed in")


    def parsecommandargs(self, cmd, arg):
        """
        Helper function to run respective method with correct argument
        :param cmd: user command string
        :param arg: command argument string
        :return: none
        """
        if cmd == "cd":
            path = arg
            self.runcwd(path)
        elif cmd == "put":
            filename = arg
            self.runstor(filename)
        elif cmd == "get":
            filename = arg
            self.runretr(filename)

    def enterusername(self):
        """
        Prompts user to enter username to login, sends USER command to server
        :return: none
        """
        # Read in username and send to server
        self.socket.receive()
        user = "USER " + input("Enter user: ") + "\r\n"
        self.username = user
        self.socket.send(self.username)
        self.socket.receive()

    def enterpassword(self):
        """
        Prompts user to enter password to login, sends PASS command to server
        :return: none
        """
        password = "PASS " + input("Enter password: ") + "\r\n"
        self.password = password
        self.socket.send(self.password)
        if (self.socket.receive())[:3] == "530":
            print("Incorrect Credentials")
            sys.exit(0)

    def runsyst(self):
        self.socket.send("SYST")
        self.socket.receive()

    def runcwd(self, path):
        """
        Sends CWD command to server
        :param path: path to change
        :return:
        """
        self.socket.send("CWD " + path + "\r\n")
        self.socket.receive()


    def runpwd(self):
        """
        Sends PWD command to server
        :return: none
        """
        self.socket.send("PWD" + "\r\n")
        self.socket.receive()


    def runlist(self, path=None):
        """
        Sends LIST command to server
        :param path: path to list if passed in
        :return: none
        """
        if self.socket.ipv4 == True:
            # Send PASV
            response227 = self.runpasv()
            # Parse out IP address and host to use
            # 227 Entering Passive Mode (10,246,251,93,133,171).
            rawdata = response227[response227.find("(") + 1:response227.find(")")]
            ip = self.parseip(rawdata)
            port = self.parseport(rawdata)
            # Send list through connection
            # Open data socket with info from pasv response
            if path is None:
                self.socket.send("LIST" + "\r\n")
            else:
                self.socket.send("LIST " + path + "\r\n")
            self.datasocket = ClientSocketConnection(ip, "ds.txt", port)
            self.socket.receive()
            self.datasocket.receive()
            self.datasocket.close()
            self.socket.receive()
        else:
            response229 = self.runepsv()
            # Parse port number from response
            port = response229[response229.find("(|||") + 4:response229.find("|)")]
            # Open data socket with port number and same ip
            self.socket.send("LIST " + "\r\n")
            self.datasocket = ClientSocketConnection(self.socket.host, "ds.txt", int(port))
            self.socket.receive()
            self.datasocket.receive()
            self.datasocket.close()
            self.socket.receive()

    def parseip(self, rawdata):
        """
        Helper function to parse ip address from PASV
        :param rawdata: pasv returned values
        :return: formatted ip address string
        """
        iplist = rawdata.split(",")
        ip = ("%s.%s.%s.%s" % (iplist[0], iplist[1], iplist[2], iplist[3]))
        return ip

    def parseport(self, rawdata):
        """
        Helper function to parse port number from PASV
        :param rawdata: pasv returned values
        :return: calcualted port number
        """
        portslist = rawdata.split(",")
        # p1 * 256 + p2, then connect to this port
        port = (int(portslist[4]) * 256) + int(portslist[5])
        return port

    def runpasv(self):
        """
        Sends PASV command to server
        :return: 227 response message
        """
        # Send PASV to server
        self.socket.send("PASV" + "\r\n")
        response = self.socket.receive()
        if response[:3] == "227":
            return response  # 227 Entering Passive Mode. A1,A2,A3,A4,P1,P2

    def runport(self):
        """
        Sends PORT command to server
        :return: none
        """
        # Send PORT to server
        print("Run port method")
        # portargs = "%s,%s,%s,%s,%s,%s" % (h1,h2,h3,h4,p1,p2)
        # print(portargs)
        # Use default port 20
        responsedata = "10,246,251,93,0,1025"
        self.socket.send("PORT " + responsedata + "\r\n")
        self.datasocket = ClientSocketConnection("10.246.251.93", "ds.txt", 20)
        self.datasocket.receive()
        self.socket.receive()

    def runepsv(self):
        """
        Runs extended passive mode for IPv6 connections
        :return: none
        """
        if self.socket.ipv6 == True:
            self.socket.send("EPSV " + "\r\n")
            response = self.socket.receive()
            if response[:3] == "229":
                return response  # 229 Entering Extended Passive Mode (|||15068|)
        else:
            print("Using ipv4 host")

    def runeprt(self):
        """
        Runs extended active mode for IPv6 connections
        :return: none
        """
        if self.socket.ipv6 == True:
            self.socket.send("EPRT " + "\r\n")
            self.socket.receive()

    def togglepasv(self):
        """
        Allows user to toggle between passive and active mode
        :return: none
        """
        # Send PASV to server
        self.socket.send("PASV" + "\r\n")
        self.socket.receive()
        print("Passive mode on.")

    def runstor(self, filename):
        """
        Sends STOR command to server
        :param filename: string file name of file to send to server
        :return: none
        """
        # Send PASV
        response227 = self.runpasv()
        # Parse out IP address and host to use
        # 227 Entering Passive Mode (10,246,251,93,133,171).
        rawdata = response227[response227.find("(") + 1:response227.find(")")]
        ip = self.parseip(rawdata)
        port = self.parseport(rawdata)
        # Send STOR through connection
        # Open data socket with info from pasv response
        self.socket.send("STOR " + filename + "\r\n")
        # Send contents of file, opposite of how retr is working
        # open file, get file data, send file data through data socket
        self.datasocket = ClientSocketConnection(ip, "ds.txt", port)
        self.socket.receive()
        self.datasocket.close()
        self.socket.receive()

    def runretr(self, filename):
        """
        Sends RETR command to server
        :param filename: string file name of file to get from server
        :return:
        """
        response227 = self.runpasv()
        rawdata = response227[response227.find("(") + 1:response227.find(")")]
        ip = self.parseip(rawdata)
        port = self.parseport(rawdata)
        # Send STOR through connection
        # Open data socket with info from pasv response
        self.socket.send("RETR " + filename + "\r\n")
        self.datasocket = ClientSocketConnection(ip, "ds.txt", port)
        # Data socket returns file data
        filedata = self.datasocket.receive()
        # open file and write data
        receivedfile = open(filename, "w+")
        receivedfile.write(filedata)
        self.datasocket.close()
        self.socket.receive()  # 150 response
        self.socket.receive()

    def runquit(self):
        '''
        Sends QUIT command to server, disconnects and exits ftp prompt
        :return:
        '''
        self.socket.send("QUIT" + "\r\n")
        self.socket.receive()


def main():
    """
    Parses user input and created client socket to start FTP protocol
    :return:
    """
    # Create SocketConnection
    if (len(sys.argv) < 3):
        print("TO RUN: ftpclient.py <host> <logfile> <port>")
    # All arguments passed in
    elif (len(sys.argv) == 4):
        clientsocketconnection = ClientSocketConnection(sys.argv[1], sys.argv[2], int(sys.argv[3]))
    else:
        clientsocketconnection = ClientSocketConnection(sys.argv[1], sys.argv[2])

    if (clientsocketconnection.connected):
        # Start FTP protocol
        serverStream = ServerStream(clientsocketconnection)
        serverStream.runprotocol()


if __name__ == "__main__":
    main()
