import logging
import time
import mimetypes
import sqlite3

import requests
from mastodon import Mastodon

import config

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


TSTAMP_CUR = 0
TSTAMP_NEXT = 1


def _update_timestamp(cur, ttype, tstamp):
    cur.execute('delete from timestamps where ttype=?', (ttype,))
    cur.execute('insert into timestamps (ttype, timestamp) values (?, ?)', (ttype, tstamp))


def _do_res(conn):
    cur = conn.cursor()
    cur_t = time.time()

    # update timestamps for current and next
    _update_timestamp(cur, TSTAMP_CUR, cur_t)
    _update_timestamp(cur, TSTAMP_NEXT, cur_t + config.TOOT_PERIOD)

    # i really dont like data loss you see
    # another type of loss i like: | || || |_
    conn.commit()


def _fetch_tstamp(conn, ttype) -> int:
    cur = conn.cursor()
    cur.execute('select timestamp from timestamps where ttype=?', (ttype,))
    return cur.fetchone()

def fetch_next_timestamp(conn) -> int:
    """Fetch the next timestamp to check for posts."""
    try:
        return _fetch_tstamp(conn, TSTAMP_NEXT)[0]
    except TypeError:
        return None

def fetch_cur_tstamp(conn) -> int:
    """Fetch the current timestamp, if any."""
    try:
        return _fetch_tstamp(conn, TSTAMP_CUR)[0]
    except TypeError:
        return None


def fetch_last_posts(conn) -> list:
    """Fetch tooted posts from db"""
    cur = conn.cursor()
    cur.execute('select postid from posts')
    last_posts = cur.fetchall()
    return [e[0] for e in last_posts]


def is_image(child) -> bool:
    """Check if a post object has an image attached."""
    child_data = child['data']
    child_url = child_data['url']
    return child_url.endswith(('.jpg', '.jpeg', '.png', '.gif'))


def not_posted(child, conn) -> bool:
    """Check if a post has been already tooted."""
    child_data = child['data']
    child_id = child_data['id']

    last_posts = fetch_last_posts(conn)

    return child_id not in last_posts


def poll_toot(mastodon, conn):
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
        _do_res(conn)
        return

    try:
        log.info('requesting json...')
        data = resp.json()
        assert isinstance(data, dict)
    except Exception:
        log.exception('Failed to parse json.')
        _do_res(conn)
        return

    data = data['data']

    last_posts = fetch_last_posts(conn)
    useful_children = (child for child in data['children']
                       if is_image(child) and not_posted(child, conn))

    try:
        child = next(useful_children)
    except StopIteration:
        log.error('no useful children found')
        _do_res(conn)
        return

    child_data = child['data']
    child_id = child_data['id']

    log.info(f'id to post: {child_id}, last ids: {last_posts}')

    if child_id in last_posts:
        log.warning('last posted == current child, ignoring')
        _do_res(conn)
        return

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

    conn.execute('insert into posts (postid) values (?)', (child_id,))
    conn.commit()

    _do_res(conn)


def main():
    mastodon = Mastodon(
        client_id=config.CLIENT_ID,
        client_secret=config.CLIENT_SECRET,
        access_token=config.ACCESS_TOKEN,
        api_base_url=config.API_BASE_URL,
    )

    db = sqlite3.connect(config.BOT_STATE)
    db.executescript("""
    create table if not exists posts (
        postid text not null
    );

    create table if not exists timestamps (
        ttype int,
        timestamp bigint
    );
    """)

    while True:
        current_tstamp = fetch_cur_tstamp(db)

        # first time running OR .eu_nvr_last_toot is lost
        if not current_tstamp:
            poll_toot(mastodon, db)

        current_tstamp = time.time()
        next_tstamp = fetch_next_timestamp(db)

        # is the current time beyond the time where we should do a check?
        if current_tstamp > next_tstamp:
            poll_toot(mastodon, db)

        # commit etc
        db.commit()

        next_tstamp = fetch_next_timestamp(db)

        if int(current_tstamp) % 100 == 0:
            remaining = next_tstamp - current_tstamp
            remaining = round(remaining, 5)
            log.info(f'{remaining} seconds before poll time')

        # wait a second before doing it all again
        time.sleep(1)


if __name__ == '__main__':
    main()
