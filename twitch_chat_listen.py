#Logs in to a chat and listens to the messages, calling a function each distinct line of message

#NOTE: interactive mode is off. i.e. you can call listen() then call end_program on the next line and it'll go until an exception is caught.

import socket
import time
import datetime

def connect(channel, nick, PASS):
    """
        Connect to Twitch. Seems pretty reliable at this point.
    """
        
        # Do not use non-blocking stream, they are not reliably
        # non-blocking
        # s.setblocking(False)
        # s.settimeout(1.0)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connect_host = "irc.twitch.tv"
    connect_port = 6667
    try:
        s.connect((connect_host, connect_port))
    except (Exception, IOError):
        print("Unable to create a socket to %s:%s" % (
                connect_host,
                connect_port))
        raise  # unexpected, because it is a blocking socket

        # Connected to twitch
        # Sending our details to twitch...
    s.send('PASS %s\r\n' % PASS)
    s.send('NICK %s\r\n' % nick)
    s.send('JOIN #%s\r\n' % channel)
    return s

#f is the function to be called on each line of data
#endFunc is a function that, when called, if it returns true then the loop
#        will stop. By default (without this function being passed in), 
#        this program will loop forever when called
def listen(channel, nick, PASS, interpret, endFunc=None):
    try:
        sock = connect(channel, nick, PASS)
        sock.settimeout(6) #so we can frequently check for endFunc
        while True:
           data = ''
           while True:
               try:
                   data = sock.recv(512)
                   break
               except socket.timeout:
                   if endFunc and endFunc():
                       return
                   continue
               except socket.error: #if the user's connection blips
                   print "connection error, attempting to listen"
                   time.sleep(5)
                   sock = connect(channel, nick, PASS)
                   sock.settimeout(6) #so we can frequently check for endFunc
                   break
           if data[0:4] == "PING":
              sock.send(data.replace("PING", "PONG"))
           #I split the data like this because the sockets sometimes concats the data in a weird way. This ameliorates that problem.
           for line in data.split('\n'):
               if line != '':
                   interpret(line)
                   
    except KeyboardInterrupt, SystemExit:
        print "finishing this"
        raise
        return

