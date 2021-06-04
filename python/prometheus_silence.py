#!/usr/bin/env python3

"""
To pre-create prometheus alertmanager silences related to a server

Usage:
    prometheus_silence.py set [options] --host HOST...
    prometheus_silence.py delete --host HOST...

Options:
    --createdby=<createdby>         Name of the user
                                    [default: bot]
    --start=<start>                 Start time in UTC
                                    [default: now]
    --duration=<duration>           Silence period in hours
                                    [default: 1]
    --comment=<comment>             Brief desription of the silence
    --channel-name=<channel-name>   Mattermost channel
                                    [default: Alerts]
    --token=<token>                 Mattermost Bot user
                                    [default: 7oknhyjynfna7e71g6afkqmzua]
    --help                          Show this screen
"""

import sys
import time
import requests
from datetime import datetime, timedelta
from docopt import docopt

prometheus_alertmanager_api = 'http://pi-0:9093/api/v1'
mattermost_api = 'http://ubuntu-21:8065/api/v4'

class PromSilence():
    def __init__(self, host, start, duration, createdby,
                 comment, channel, token):

        global prometheus_alertmanager_api
        global mattermost_api
        self.host = host
        self.start = start
        self.duration = int(duration)
        self.comment = comment
        self.createdby = createdby
        self.channel = channel
        self.token = token
        self.seturl = '{}/silences'.format(prometheus_alertmanager_api)
        self.mmosturl = '{}/posts'.format(mattermost_api)

        # mattermost default settings
        self.mmost_channels = {'Alerts':
                               {'channel_id': 'oepnkqx48b8k5j1o9cpmhen5kw',
                                'description': 'Channel for testing'}}

    def set_time_range(self):
        if self.start == 'now':
            start_time = '{}Z'.format(datetime.now().isoformat()[:-3])
            end_time = ('{}Z'.format((datetime.now() +
                        timedelta(hours=self.duration))
                        .isoformat()[:-3]))
            return {'startsAt': start_time, 'endsAt': end_time}
        else:
            try:
                stime = datetime.strptime(self.start, '%Y-%m-%dT%H:%M')
                start_time = '{}.000Z'.format(stime.isoformat())
                end_time = ('{}.000Z'.format((stime +
                            timedelta(hours=self.duration))
                            .isoformat()))
                return {'startsAt': start_time, 'endsAt': end_time}
            except ValueError:
                print('Incorrect time format provided,'
                      ' should be ISO format e.g. 2020-01-01T18:00')
                sys.exit(1)

    def alert_match(self, host):
        match = {'id': '',
                 'createdBy': self.createdby,
                 'comment': self.comment,
                 'startsAt': self.set_time_range()['startsAt'],
                 'endsAt': self.set_time_range()['endsAt'],
                 'matchers': [
                  {'name': 'instance',
                   'value': '{}.*'.format(host),
                   'isRegex': True}]}
        return match

    def send_to_mattermost(self):
        header = {'Content-Type': 'application/json',
                  'Authorization': 'Bearer {}'.format(self.token)}
        startsat = self.set_time_range()['startsAt']
        endsat = self.set_time_range()['endsAt']

        template = '\n'.join(('##### Alerts silence set for {host}',
                              '|Hostname | {host} |',
                              '| :- | :-|',
                              '|Starts At | {starts} UTC|',
                              '|Ends At | {ends} UTC|',
                              '|Comment | {comment} |',
                              '|Created By | {createdby} |'))

        msg = template.format(host=self.host,
                              starts=startsat,
                              ends=endsat,
                              comment=self.comment,
                              createdby=self.createdby)
        try:
            d = {'channel_id':
                 self.mmost_channels.get(self.channel)['channel_id'],
                 'message': msg}
        except Exception as e:
            print("Unable to find channel id for channel {}: {}"
                  .format(self.channel, e))
            sys.exit(1)

        try:
            r = requests.post(self.mmosturl,
                              headers=header,
                              json=d,
                              verify=False)
            if r.status_code == 201:
                print('Notification posted to mattermost successfully')
            else:
                print('Unable to post to mattermost')
        except Exception as e:
            print('Unable to connect to mattermost: {}'.format(e))

    def set_silence(self, d):
        """ To set the silence as per alert type
            Parameters:
                d (dict): data for setting prometheus silence
                t (str): alert types
        """
        try:
            r = requests.post(self.seturl, json=d)
            time.sleep(1)
            if r.status_code == 200:
                print(('{} - silence set from {} to {} UTC'
                       .format(self.host, d['startsAt'], d['endsAt'])))
                return True
            else:
                print('Unable to set silence')
                sys.exit(1)
        except Exception as e:
            print('Unable to set silence: {}'.format(e))
            sys.exit(1)


if __name__ == '__main__':
    opts = docopt(__doc__)
    set_alert = opts['set']
    createdby = opts['--createdby']
    duration = opts['--duration']
    start = opts['--start']
    comment = opts['--comment']
    hosts = opts['HOST']
    mmost_channel = opts['--channel-name']
    token = opts['--token']

    for host in hosts:
        inst = PromSilence(host,
                           start,
                           duration,
                           createdby,
                           comment,
                           mmost_channel,
                           token)

        if set_alert:
            match = inst.alert_match(host)
            inst.set_silence(match)
            inst.send_to_mattermost()
