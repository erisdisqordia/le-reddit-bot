import logging
import time
import requests

import requests
from mastodon import Mastodon

import config

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def poll_toot(mastodon):
    mastodon.toot(f'testing! timestamp {time.time()}')

    cur_t = time.time()
    return cur_t, cur_t + config.TOOT_PERIOD


def main():
    mastodon = Mastodon(
        client_id=config.CLIENT_ID,
        client_secret=config.CLIENT_SECRET,
        access_token=config.ACCESS_TOKEN,
        api_base_url=config.API_BASE_URL,
    )

    # load the next timestamp to send a toot
    # and load the last timestamp the app was running at
    try:
        fd = open(config.BOT_STATE, 'r')
        next_tstamp, current_tstamp = map(float, fd.read().split(','))
        fd.close()
    except FileNotFoundError:
        next_tstamp, current_tstamp = None, None

    while True:
        log.debug(f'next: {next_tstamp}, current: {current_tstamp}')

        # first time running OR .eu_nvr_last_toot is lost
        if current_tstamp is None:
            # poll right now, then schedule the next one
            current_tstamp, next_tstamp = poll_toot(mastodon)

        current_tstamp = time.time()

        # we have current_tstamp, good, is it beyond next_tstamp?
        if current_tstamp > next_tstamp:
            current_tstamp, next_tstamp = poll_toot(mastodon)

        # after doing those, update the file!
        with open(config.BOT_STATE, 'w') as f:
            f.write(f'{next_tstamp},{current_tstamp}')

        # wait a second before checking those again!
        time.sleep(1)


if __name__ == '__main__':
    main()
