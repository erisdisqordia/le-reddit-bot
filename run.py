import logging
import time
import requests
import mimetypes

import requests
from mastodon import Mastodon

import config

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def _do_res(last_posts):
    cur_t = time.time()
    return cur_t, cur_t + config.TOOT_PERIOD, last_posts


def is_image(child):
    child_data = child['data']
    child_url = child_data['url']
    return child_url.endswith(('.jpg', '.jpeg', '.png', '.gif'))

def not_posted(child, last_posts):
    child_data = child['data']
    child_id = child_data['id']
    return child_id not in last_posts


def poll_toot(mastodon, last_posts: list):
    """Query reddit and toot if possible."""
    log.info('calling reddit...')

    resp = requests.get(config.REDDIT_URL, headers={
        # reddit blocks me when I have a requests useragent
        # lol.
        'User-Agent': 'eunvr/0.1'
    })

    if resp.status_code != 200:
        log.error(f'Status code is not 200: {resp.status}')
        log.error(resp)
        return _do_res(last_posts)

    try:
        log.info('requesting json...')
        data = resp.json()
        assert isinstance(data, dict)
    except:
        log.exception('Failed to parse json.')
        return _do_res(last_posts)

    data = data['data']

    useful_children = (child for child in data['children']
                       if is_image(child) and not_posted(child, last_posts))

    try:
        child = next(useful_children)
    except StopIteration:
        log.error('no useful children found')
        return _do_res(last_posts)

    child_data = child['data']
    child_id = child_data['id']

    log.info(f'id to post: {child_id}, last ids: {last_posts}')

    if child_id in last_posts:
        log.warning('last posted == current child, ignoring')
        return _do_res(last_posts)

    # this has the image
    child_url = child_data['url']
    image = requests.get(child_url)

    # upload image
    mimetype, _encoding = mimetypes.guess_type(child_url)
    log.info(f'sending image (mimetype: {mimetype})...')

    media = mastodon.media_post(image.content, mimetype)

    log.info('sending toot...')
    toot = mastodon.status_post(f'{child_data["title"]} '
                                f'https://redd.it/{child_data["id"]}',
                                media_ids=[media['id']], sensitive=True)

    log.info(f'sent! toot id: {toot["id"]}, post id: {child_id!r}')

    last_posts.append(child_id)
    return _do_res(last_posts)


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
        data = fd.read().split(',')

        # unpack
        next_tstamp, current_tstamp = map(float, data[:2])
        last_posts = data[2:]

        fd.close()
    except FileNotFoundError:
        next_tstamp, current_tstamp, last_posts = None, None, []

    while True:
        # first time running OR .eu_nvr_last_toot is lost
        if current_tstamp is None:
            # poll right now, then schedule the next one
            current_tstamp, next_tstamp, last_posts = poll_toot(mastodon, last_posts)

        current_tstamp = time.time()

        # we have current_tstamp, good, is it beyond next_tstamp?
        if current_tstamp > next_tstamp:
            current_tstamp, next_tstamp, last_posts = poll_toot(mastodon, last_posts)

        # after doing those, update the file!
        with open(config.BOT_STATE, 'w') as statefile:
            statefile.write(f'{next_tstamp},{current_tstamp},{",".join(last_posts)}')

        if int(current_tstamp) % 100 == 0:
            remaining = next_tstamp - current_tstamp
            remaining = round(remaining, 5)
            log.info(f'{remaining}seconds before poll time!')

        # wait a second before checking those again!
        time.sleep(1)


if __name__ == '__main__':
    main()
