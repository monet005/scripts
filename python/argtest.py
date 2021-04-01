#!/usr/bin/env python

"""
Usage:
    argtest.py set --bankid BANKID [--start-time=<start-time>] --duration=<duration>  --hostname HOSTNAME...	
    argtest.py delete --bankid BANKID [--start-time=<start-time>] --duration=<duration>  --hostname HOSTNAME...	

Options:
    -h --help                      Show this screen.
    --version                      Show version. 
    --start-time=<start-time>      Time in 24-hour based format [default: now].    
    --duration=<duration>          Silence duration in hours    
    --bankid BANKID                Bankid of the user triggering the job.    

"""

from docopt import docopt
from datetime import datetime, timedelta
import sys

args = docopt(__doc__)
print(args)

bankid = args['--bankid']
duration = args['--duration']
start_time = args['--start-time']


if start_time == 'now':
    start_time_obj = datetime.now()
    time_delta = str(start_time_obj + timedelta(hours=int(duration)))    
    time_delta_obj = datetime.strptime(time_delta, '%Y-%m-%d %H:%M:%S.%f')
    start_time_iso = start_time_obj.isoformat()
    end_time_iso = time_delta_obj.isoformat()
    start_time = start_time_iso[:-3] + 'Z'
    end_time = end_time_iso[:-3]+ 'Z' 
else:
        try:
            start_time_obj = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
            time_delta = str(start_time_obj + timedelta(hours=int(duration)))    
            time_delta_obj = datetime.strptime(time_delta, '%Y-%m-%d %H:%M:%S')
            start_time_iso = start_time_obj.isoformat()
            end_time_iso = time_delta_obj.isoformat()
            start_time = start_time_iso[:-3] + '.000Z'
            end_time = end_time_iso[:-3]+ '.000Z' 
        except ValueError:
            print('incorrect time format provided')
            sys.exit(1)

for i in args['HOSTNAME']:
    print('{} is silenced from {} to {} by {}'.format(i, start_time, end_time, bankid)) 


if __name__ == "__main__":
    pass