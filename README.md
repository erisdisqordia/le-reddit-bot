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
- Option to schedule the post via Mastodon API's post scheduler queue instead of posting immediately
  - Can be tweaked to hand-curate your own scheduled posts with posts you choose, especially good for fast subreddits

### Todo

- [ ] Support for pulling from multiple subreddits
- [ ] Support for text posts
- [ ] Support for calling Mastodon.py to generate our own access token 

## Installation

Requirements:
 - python3 and python-pip3
 - A fediverse account that the bot will post to
 - `CLIENT_ID`, `CLIENT_SECRET`, and `ACCESS_TOKEN` to authorize posting to your fedi account   
   - Generate these here https://tinysubversions.com/notes/mastodon-bot/

```
git clone https://github.com/erisdisqordia/le-reddit-bot
cd le-reddit-bot

# install dependencies
pip3 install -r requiements.txt

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

## Starting with a systemd service (optional)

- I provided a systemd service file named `reddit-bot.service.example`
- Make sure systemd can execute the script: `chmod u+x run.py`  
- Copy the service file: `cp reddit-bot.service.example reddit-bot.service`
- Modify file as needed (ie your home directory, your user, etc)  
- Move to the systemd folder: `sudo mv reddit-bot.service /etc/systemd/system/reddit-bot.service`
- Reload systemd services: `sudo systemctl daemon-reload`   
- Enable the service `sudo systemctl enable reddit-bot && sudo systemctl start reddit-bot`   
- If you change your config and want to reload the service: `sudo systemctl restart reddit-bot`
