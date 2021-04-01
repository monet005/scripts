#!/usr/bin/env python3

class Greeting:
    """
    This class is to greet you

    world.
    """

    def __init__(self, m, channel):
        self.m = m
        self.channels = {'ch1': {'name': 'Devops Issues', 'id': '8sfsxsf83fr'},
                         'ch2': {'name': 'Devops Alerts', 'id': '2sfsfsfxxfo'}}

    def hello(self):
        '''
        hello method will print the greeting for you
        '''
        print('Hello {}'.format(self.m))
        return False

    def summarize(self, msg: list) -> str:
        print('Greetings sent to {}'.format(msg))
 
    def show_channels(self):
        x = [x.keys() for x in self.channels.items()]
        return x


if __name__ == "__main__":
    x = Greeting('hello', 'ch1')
    print(x.show_channels())
