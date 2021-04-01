#!/usr/bin/env python3

import requests

url = "http://ubuntu-2:8065/mattermost/api/v4/users/me"
post_url = "http://ubuntu-2:8065/mattermost/api/v4/posts"

hosts = ['host1', 'host2', 'host3', 'host4', 'host5']

template = """
## Server alerts silenced
| Alert types   | consul, node_exporter |
|------------	|---------------------	|
| Hostnames  	| {}                    |
| Starts At  	| 29 June 2020        	|
| Ends At    	| 30 June 2020        	|
| Comment    	| Maintenance         	|
| Created By 	| Ramon               	|"""

msg = (template.format(', '.join(hosts)))

access_token = '9yqxqn8r738r58abugiu7ihauh'
data = {"channel_id": "pze4wagkfp8bjxpqwt4x7pa6de",
        "message": msg}

header = {'Content-Type':'application/json',
          'Authorization': 'Bearer {}'.format(access_token)}

r = requests.post(post_url, headers=header, json=data)

print(r.text)
print(r.status_code)



if __name__ == "__main__":
    pass
