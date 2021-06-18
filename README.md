# le-reddit-bot

Naming came off the project originally being foreunvr`.


## Installation

Requirements:
 - Python 3.6.5+

```
git clone https://github.com/erisdisqordia/le-reddit-bot
cd le-reddit-bot

# install dependencies
pip3 install wheel Mastodon.py humanfriendly

cp config.py.example config.py

# edit config.py as you want
# CLIENT_ID, CLIENT_SECRET and ACCESS_TOKEN
# are acquired by creating an application tied to the bots' account
# create one here: https://tinysubversions.com/notes/mastodon-bot/
```

## Running

```
python3 run.py
```

## Starting with your server startup

I provided a systemd service file. Copy le-reddit.service.example to le-reddit.service and modify it as needed   
Then move to /etc/systemd/system/  
Reload systemd with `sudo systemctl daemon-reload`   
Enable the service `sudo systemctl enable le-reddit && sudo systemctl start le-reddit`   
