# le-reddit-bot

Bot that checks for new images on a subreddit (i.e. reddit.com/r/Megaten) and posts to an account on the Fediverse (Mastodon, Pleroma, etc)

Fork of [luna/eunvrbot](https://gitlab.com/luna/eunvrbot/-/tree/master) with many new options and rewrites to make it customizable

### Differences include:
- Status visibility option (previously only posted publicly)
- NSFW post marking configuration
  - Options to match reddit's NSFW tag, always mark NSFW on fedi, or never mark NSFW
- Ability to search posts from `New`, `Top` or `Hot` or `Rising` etc, instead of only `New`
- Option to include or disable adding the post title as status text
- Option to include or disable credit to the original submitter
- Option to include or disable the source URL
- Option to replace URL links with an alternative such as libreddit or teddit for privacy

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

- I provided a systemd service file. Copy reddit-bot.service.example to reddit-bot.service and modify it as needed   
- Then move to /etc/systemd/system/  
- Reload systemd with `sudo systemctl daemon-reload`   
- Enable the service `sudo systemctl enable reddit-bot && sudo systemctl start reddit-bot`   
- If you change your config and want to reload the service: `sudo systemctl restart reddit-bot`
