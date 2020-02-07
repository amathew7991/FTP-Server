Andrea Mathew
CS 472
Homework 3
Due November 5, 2018

PYTHON FILES:
The following .py files are included in the submission and are required in order to properly run the ftp client
- ftpserver.py
- logger.py

ADDITIONAL FILES:
- authusers.txt is the config file to check if a user is authenticated to login to the server

TO RUN:
python3 ftpserver.py <logfile> <port>
Example: python3 ftpserver.py serverlogs.txt 2121

SIDE NOTES:
- The program was tested and run on tux, and should be able to be executed in tux without issues.
- The program was written in python, to be supported by python3. When running the script, please use python3. Some functionality I used do not work properly with other versions.
- The server is written to be tested against the standard ftp client and should be able to connect granted the ftp client uses the ip and port that the server is on. I used the ftp client on tux when testing my server. The ftp server on my local machine (MAC OSX) is implemented differently, and the server does not work properly with it. It is recommneded to use the ftp client that is on the tux server.
- The program uses file "authusers.txt" as the config file to check if the entered user is authorized. The config file MUST be remain named authusers.txt. Additional users can be added to the file as a new line, so long as it follows the format of <username>:<password>

STEPS TO REPRODUCE:
The program was developed on pycharm, and I am able to run the server on pycharm and connect using the ftp client on tux.
1. Start server via command line
2. Start client  using the ip returned by the server "server listening: ip <use this ip>" ->
3. Login using one of the auth users on the attached text file
4. Protocol will begin


SAMPLE LOG FILE:
A sample log file titled "serverlog.txt" has been included and contains all the logging implemented for the ftp client.

FTP USER COMMANDS:
The following are valid commands the user can enter into the ftp prompt:
ls : LIST
pwd : PWD
cd : CWD
cdup : CDUP
passive : PASV
put : STOR
get : RETR

SAMPLE RUN:
The sample run was done by starting the server, starting a client running commands and then starting a second client to check threading.
There are screenshots attached of the terminal running server with multiple clients titled "terminalrunserver", "terminalclient1" and "terminalclient2"
