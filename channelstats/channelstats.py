# This module will automatically record twitch channelstats once an hour until canceled.

# Imports
import datetime
import json
import time
import schedule
import requests


# Functions
def get_top_channels():
    # Use twitch API to get JSON object with stream info
    response = requests.get('https://api.twitch.tv/kraken/streams/?limit=100&languge=`en`?oauth_token=tpx328c5rfguvbjnka0b6skqpypf69&client_id=jz5smvmzkuwtpcsk5sq1p7ov6ytrbpm').json()
    return response

def get_stream_summary():
    # Get json object with stream summary from twitch API
    response = requests.get('https://api.twitch.tv/kraken/streams/summary?oauth_token=tpx328c5rfguvbjnka0b6skqpypf69&client_id=jz5smvmzkuwtpcsk5sq1p7ov6ytrbpm').json()
    return response

def parse_top_channels():
# Get data for top 100 English streams currenly online

    streams = get_top_channels()['streams']
    summary = get_stream_summary()

    stream_dict = {}
    stream_dict['summary'] = summary
    for i in streams:
        channel_dict = { 
            'viewers' : i['viewers'],
            'game' : i['game'],
            'mature' : i['channel']['mature']
            }
            
        stream_dict[i['channel']['name']] = channel_dict
    return stream_dict

def write_output(directory, stream_dict):
    # Writing stream_dict to file with an date based name.

    dt_now = datetime.datetime.now()
    str_now = datetime.datetime.strftime(dt_now, '%m_%d_%Y_%H%M')
    filename = directory + str_now + '_top_channels.json'

    with open(filename, 'w') as f:
        json.dump(stream_dict, f, sort_keys=True, indent=4)
    return

def scheduled_job():
    """Calls function to fetch and write"""
    print 'time:{0}, doin stuff'.format(datetime.datetime.now())
    directory = '/Users/jimbo/Documents/FUN/chatstats/channelstats/'
    channels = parse_top_channels()
    write_output(directory, channels)


def main():
    # Fetches data once an hour
    schedule.every().hour.do(scheduled_job)
    end = datetime.datetime.now() + datetime.timedelta(days=7)

    while datetime.datetime.now() < end:
        schedule.run_pending()
        time.sleep(10)
        
# Main
if __name__ == "__main__":
    main()

#todo
# Switch the API calls to use a function rather than store my twitch authentication ID in plaintext in the script
# replace fixed 7 day period with sys.argv call for duration



