#TODO: Delete logs on SystemExit? maybe? maybe after 24 hrs or a set period of time?

#USAGE: "python chat_stats.py" or "python chat_stats.py <channel>"

#NOTE: Some special characters don't interact well with sockets and python, so those won't be logged (like some of them here: http://www.umingo.de/doku.php?id=misc:chat_smileys)
#NOTE: This is meant to be done a few times per stream approximately (not like 100 times per stream). So if you start recording the chat, then restart 5 mins later, the old version will be overwritten, but if you start recording the chat then restart the program 2 hours later, it will start recording new logs. The filename represents when the chat recordings were started.

# Imports (can I remove any of these?)
from thread import start_new_thread, exit
import os
import sys
import time
import string
import datetime
import threading
import requests
import json
import re
from get_settings import getSettings
from pass_info import get_password, get_username, get_client_id
import socket
import time
import datetime


settingsDict = getSettings()

# Define functions


# Checks whether channel is online using the twitch API.
def isTwitchChannel(channel):
    response = requests.get('https://api.twitch.tv/kraken/streams/'+channel+'?oauth_token={0}&client_id={1}'.format(get_password(),
        get_client_id())).json()    
    return 'error' not in response.keys()


#thanks to http://twitchemotes.com/ :-)
def getEmotes():
    """ Gets emote list from twitchemotes"""
    emotelist = [':)',':(',':o',':z','B)',':/',';)',';p',':p',';P',':P','R)','o_O','O_O','o_o','O_o',':D','>(','<3']
    print "loading emotes..."
    normal = requests.get('https://twitchemotes.com/api_cache/v2/global.json').json()
    emotelist.extend(normal['emotes'].keys())
    print "loading sub emotes..."
    subs = requests.get('https://twitchemotes.com/api_cache/v2/subscriber.json').json()
    for channel in subs['channels'].keys():
        for emote in subs['channels'][channel]['emotes']:
            emotelist.extend([emote['code']])
    return emotelist


def open_file(kind, extension='log'):
    filename = ""
    filename += kind+'.'+extension
    file_path = os.path.relpath(directory + '/' + filename)
    return open(file_path, 'a')

def isMessage(data):
    return prog.match(data) != None
    #return len(data.split('tmi.twitch.tv PRIVMSG #')) > 1

def formatMessage(message):
    #TODO: remove the "action" stuff for "/me"s
    return message.strip().split('\n')[0].split('\r')[0]

def log(author, message, elapsed_time):
    message = formatMessage(message)
    global emotelist
    
    #try:
            
            #AUTHORS
    authors.write('{0} : {1}\n'.format(elapsed_time.seconds, author))
            #MESSAGES
    messages.write('{0} : {1}\n'.format(elapsed_time.seconds, message))
            #WORDS
    try:
        for word in message.split(' '):
            if word.isalnum() and (word not in emotelist):
                if word != 'ACTION':
                    words.write(word)
                    words.write(' ')
            #EMOTES
        for word in message.split(' '):
            if word in emotelist:
                emotes.write(str(elapsed_time.seconds)+' : '+word.split('/')[0].split('7')[0] + '\n') 
                    
    except ValueError: #happens if the program closes in the middle of writing to the files
        print "Closing program..."
        pass
        

def get(URL):
    ''' Get URL function using requests. Prints requests error and retries if
    fails'''
    val = None
    while True:
        try:
            val = requests.get(URL)
            val.raise_for_status()
            break
        except requests.exceptions.RequestException as e:
            print e
            print "Connection timed out. Retrying."
            time.sleep(5)
    return val
            

def interpret(data, elapsed_time):
    
    if isMessage(data):
        try:
            try:
                author = data.split('@')[1].split('.tmi.twitch.tv',1)[0]
            except IndexError:
                author = data.split('.tmi.twitch.tv',1)[0]
            s = channel + ' :'
            message = s.join(data.split(s)[1:])
            message = filter(lambda x: x in string.printable, message)
            log(author, message, elapsed_time)
        except IndexError:
            print
            print 'MALFORMED DATA - ' + data
            print 'MALFORMED DATA - ' + data
            print 'MALFORMED DATA - ' + data
            print
            return

def setStop(duration=1):
    """ Sets time for thread to automatically stop at to collect segments of
    defined length
    duration defaults to 1 hr (60 minutes)
    """
    now = datetime.datetime.now()
    end = now + datetime.timedelta(hours=duration)
    return end

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



def listen(channel, nick, PASS, interpret, start_time, end_time, files):
    
    # Connect to socket
    sock = connect(channel, nick, PASS)
    sock.settimeout(6) #so we can frequently check for endFunc
    while datetime.datetime.now() < end_time:
        data = ''
        while datetime.datetime.now() < end_time:
        # Repeat indefinitely until end of duration is reached        
            try:
                data = sock.recv(1024)
                break
            except socket.timeout:
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
        elapsed_time = datetime.datetime.now() - start_time
        for line in data.split('\n'):
            if line != '':
                interpret(line, elapsed_time)
                for f in files:
                    f.flush()


# Program Information Flow
# Main

# Join channel if not given a channel during call
if len(sys.argv) == 1:
    channel = raw_input("Chat to join: ")
else:
    channel = sys.argv[1]

count = 0
while isTwitchChannel(channel) == False:
    print 'Error: "' + channel + '" does not appear to be a valid Twitch channel.'
    channel = raw_input("Chat to join: ")


#words in the twitchemotes API that should not actually be counted as emotes 
    #AKA, not used as emotes >90% of the time
not_emotes = ['GG', 'Gg', 'double', 'triple']
emotelist = getEmotes()
for emote in not_emotes:
    try:
        emotelist.remove(emote)
    except:
        pass

# Making directory for logs based on current time
dt = datetime.datetime.now()
d = dt.strftime('%b-%d-%Y')
t = dt.strftime('%H_%M')
dt = dt.strftime('%Y-%m-%d-%I%p') #2014-08-23-02PM
directory = "logs/" + channel + '/' + dt
print "Writing to " + directory
if not os.path.exists(directory):
    os.makedirs(directory)


# opening files for writing.
authors = open_file('authors') #to get the most active users
messages = open_file('messages') #literal log of the messages - for average message length, etc.
words = open_file('words') #to get word cloud
emotes = open_file('emotes') #for emote stats
files = [authors, messages, words, emotes]

#init
prog = re.compile('^.*[a-z0-9_.-]+\.tmi\.twitch\.tv PRIVMSG #')
num_messages = 0
cur_game = get('https://api.twitch.tv/kraken/channels/{0}?oauth_token={1}&client_id={2}'.format(channel, get_password(), get_client_id())).json()['game']


endtime = setStop(1) # not used right now
start_time = datetime.datetime.now()
nick = get_username()
PASS = get_password()

print
print "===============================STARTING CHAT INPUT=============================="
listen(channel, nick, PASS, interpret, start_time, endtime, files)
print "==================================ENDING_PROGRAM================================"


# currently ->
# program order is:
# listen calls connect.
# listen calls interpret.
# interpret ultimately calls log.
