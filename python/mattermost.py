#!/usr/bin/env python3

import requests


class Mattermost():
    """
    hello world
    """
    def __init__(self):
        self.posturl = 'http://ubuntu-2:8065/mattermost/api/v4/posts'
        self.token = '9yqxqn8r738r58abugiu7ihauh'
        self.channels = {'default': {'name': 'Alerts',
                         'channel_id': 'z1pjc9u787dg7xidisoy7w5cwy'},
                         'test': {'name': 'Changes',
                                  'channel_id': 'pze4wagkfp8bjxpqwt4x7pa6de'}}
        self.channelsurl = 'http://ubuntu-2:8065/mattermost/api/v4/channels'

    def send_to_mmost(self, m, ch):
        try:
            header = {'Content-Type': 'application/json',
                      'Authorization': 'Bearer {}'.format(self.token)}

            data = {'channel_id': self.channels.get(ch)['channel_id'],
                    'message': m}
            
            r = requests.post(self.posturl, headers=header, json=data)
            if r.status_code == 201:
                print('message sent to {} channel'.format(self.channels.get(ch)['name']))
            else:
                print('unable to send message')
        except Exception as e:
            print('Unable to connect to mattermost: {}'.format(e))

    def show_channels(self):
        ch = [x for x in self.channels.items()]
        print('Available channels')
        for i in ch:
            print('{} : {}'.format(i[0], i[1]['name']))
 
m = Mattermost()
m.show_channels()
m.send_to_mmost('hello ramon', 'default')
