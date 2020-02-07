Andrea Mathew
CS 471
Homework 2
Due October 22nd, 2018

PYTHON FILES:
The following .py files are included in the submission and are required in order to properly run the ftp client
- ftpclient.py
- logger.py

TO RUN:
python3 ftpclient.py <hostname> <logfilename> <port>
Example: python3 ftpclient.py 10.246.251.93 clientlogs.txt 21

SIDE NOTES:
- The program was tested and run on tux, and should be able to be executed in tux without issues.
- The program was written in python, to be supported by python3. When running the script, please use python3. Some functionality I used do not work properly with other versions.
- When logging in, if incorrect credentials are entered the reponse does take a few seconds to respond. However it should not hang, and the "530 Login Incorrect" should be displayed.

SAMPLE LOG FILE:
A sample log file titled "clientlogs.txt" has been included and contains all the logging implemented for the ftp server.

FTP USER COMMANDS:
The following are valid commands the user can enter into the ftp prompt:
ls : LIST
pwd : PWD
cd : CWD
passive : PASV
put : STOR
get : RETR

SAMPLE RUN:
A sample run file titled "samplerun.txt" of what the console outputs has been included. It was copied from the command line and put in a text file. It includes a run with ipv4 and ipv6.
