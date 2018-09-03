# eunvrbot

A bot that mirrors the latest posts from any subreddit to Mastodon.

Naming came off the project originally being for `r/eu_nvr`.


## Installation

Requirements:
 - Python 3.6.5+

```
git clone https://gitlab.com/lnmds/eunvrbot name_of_yr_botte
cd name_of_yr_botte

# some libraries require wheel
pip3 install wheel
pip3 install -Ur requirements.txt

cp config.py.example config.py

# edit config.py as you want
# CLIENT_ID, CLIENT_SECRET and ACCESS_TOKEN
# are acquired by creating an application tied to the bots' account
```

## Running

```
python3 run.py

# or under pm2
pm2 start --name name_of_yr_botte run.py --interpreter python3
```
