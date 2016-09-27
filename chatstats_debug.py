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
s        sock = connect(channel, nick, PASS)
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


def interpret(data):
    global done
    if isMessage(data):
        if done:
            return
        try:
            try:
                author = data.split('@')[1].split('.tmi.twitch.tv',1)[0]
            except IndexError:
                author = data.split('.tmi.twitch.tv',1)[0]
            s = channel + ' :'
            message = s.join(data.split(s)[1:])
            message = filter(lambda x: x in string.printable, message)
            log(author, message)
            if verbose:
                print (author + ' - ' + message).strip()
        except IndexError:
            print
            print 'MALFORMED DATA - ' + data
            print 'MALFORMED DATA - ' + data
            print 'MALFORMED DATA - ' + data
            print
            return



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
files = []
authors = open_file('authors') #to get the most active users
messages = open_file('messages') #literal log of the messages - for average message length, etc.
words = open_file('words') #to get word cloud
emotes = open_file('emotes') #for emote stats
rate = open_file('rate', 'csv') #how fast chat is going
files = [authors, messages, words, emotes, rate]


prog = re.compile('^.*[a-z0-9_.-]+\.tmi\.twitch\.tv PRIVMSG #')
num_messages = 0

#http://stackoverflow.com/questions/5179467

#init
if not debug:
    rate.write('TIME_START='+t+'\n')


nick = get_username()
PASS = get_password()

listen(channel, nick, PASS, interpret, endFunc)


