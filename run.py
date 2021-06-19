#!/usr/bin/env python3
import logging
import time
import mimetypes
import sqlite3
import math

from humanfriendly import format_timespan
from xml.sax import saxutils as su
from datetime import datetime, timedelta

import requests
from mastodon import Mastodon, MastodonAPIError

import config

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


TSTAMP_CUR = 0
TSTAMP_NEXT = 1


def _update_timestamp(cur, ttype, tstamp):
    cur.execute("delete from timestamps where ttype=?", (ttype,))
    cur.execute(
        "insert into timestamps (ttype, timestamp) values (?, ?)", (ttype, tstamp)
    )


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
    cur.execute("select timestamp from timestamps where ttype=?", (ttype,))
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
    cur.execute("select postid from posts")
    last_posts = cur.fetchall()
    return [e[0] for e in last_posts]


def is_image(child) -> bool:
    """Check if a post object has an image attached."""
    child_data = child["data"]
    child_url = child_data["url"]
    return child_url.endswith((".jpg", ".jpeg", ".png", ".gif"))


def not_posted(child, conn) -> bool:
    """Check if a post has been already tooted."""
    child_data = child["data"]
    child_id = child_data["id"]

    last_posts = fetch_last_posts(conn)

    return child_id not in last_posts


def is_nsfw(child) -> bool:
    """return if a post is set to over 18 (NSFW)."""
    data = child["data"]
    return data.get("over_18", False)


def gen_cw_text(child_data: dict) -> bool:
    """Generate a content warning text for the post
    based on the flair or title of the post."""
    flair = child_data.get("link_flair_text")

    if flair in config.ACCEPTED_FLAIRS:
        return flair

    # match configurable content warnings
    # with the post's title
    for cw_title, keywords in config.CONTENT_WARNINGS.items():
        title = child_data["title"]

        # search for any match
        if any(word in title for word in keywords):
            return cw_title

    # by default, if no matches happen, no CW applies.
    # can be set to a default CW by using an empty keyword


def poll_toot(mastodon, conn, retry_count=0):
    """Query reddit and toot if possible."""
    # log.info("Checking for new posts...")
    subreddit_name = config.SUBREDDIT
    sort = config.SUBREDDIT_SORT
    subreddit_url = "https://www.reddit.com/r/" + subreddit_name + "/" + sort + ".json"

    try:
        resp = requests.get(
            subreddit_url,
            headers={
                "User-Agent": "python:erisdisqordia.fedi-reddit-bot:v1.0.0"
            },
        )
    except:
        log.exception(
            "Failed to request given reddit url. retrying (try %d)", retry_count
        )

        if retry_count > 5:
            log.error("retried too much")
            raise RuntimeError("retried too much")

        time.sleep(1)
        retry_count += 1
        return poll_toot(mastodon, conn, retry_count)

    if resp.status_code != 200:
        log.error("Status code is not 200: %d", resp.status_code)
        log.error(resp)
        _do_res(conn)
        return

    try:
        log.info("Checking for new posts in r/" + subreddit_name + "/" + sort + "/...")
        data = resp.json()
        assert isinstance(data, dict)
    except Exception:
        log.exception("Failed to parse json.")
        _do_res(conn)
        return

    data = data["data"]

    last_posts = fetch_last_posts(conn)

    # find all posts that have images and weren't tooted
    useful_children = (
        child
        for child in data["children"]
        if is_image(child) and not_posted(child, conn)
    )

    try:
        child = next(useful_children)
    except StopIteration:
        log.error("No new posts found. Waiting to retry...")
        _do_res(conn)
        return

    child_data = child["data"]
    child_id = child_data["id"]
    child_author = child_data["author"]

    log.info(f"id to post: {child_id}, last ids: {last_posts}")

    if child_id in last_posts:
        log.warning("last posted == current child, ignoring")
        _do_res(conn)
        return

    child_url = child_data["url"]
    image = requests.get(child_url)

    # upload image since we can't pass the URL
    mimetype, _encoding = mimetypes.guess_type(child_url)
    log.info(f"sending image (mimetype: %r)...", mimetype)
    try:
        media = mastodon.media_post(image.content, mimetype)
    except MastodonAPIError:
        log.exception("error while sending image, ignoring")

        # since media failed to upload, its best we ignore
        # the post altogether by inserting it into db
        conn.execute("insert into posts (postid) values (?)", (child_id,))
        conn.commit()

        _do_res(conn)
        return

    log.info("Posting on the Fediverse...")

    cw_text = gen_cw_text(child_data)
    reddit_title = child_data["title"]
    toot_visibility = config.VISIBILITY
    link_prefix = config.LINK_PREFIX
    text_prefix = config.TEXT_PREFIX

    if config.TITLES_ENABLED == "true":
        toot_text = su.unescape(reddit_title, {'&quot;':'"'})
    else:
        toot_text = ""

    if config.MARK_NSFW == "true":
        toot_sensitivity = is_nsfw(child)
    elif config.MARK_NSFW == "always":
        toot_sensitivity = True
    else:
        toot_sensitivity = False

    if config.AUTHOR_CREDIT == "true":
        author_name = config.AUTHOR_PREFIX + child_author + " "
    else:
        author_name = ""

    if config.LINK_ENABLED == "true":
       if config.ALT_URL_ENABLED == "true":
           alternate_url = config.ALT_URL
           url_type = config.ALT_URL_TYPE
           if url_type == "full":
               source_url = link_prefix + "https://" + alternate_url + "/r/" + subreddit_name + "/" + child_id
           elif url_type == "short":
               source_url = link_prefix + "https://" + alternate_url + "/" + child_id
           else:
               source_url = link_prefix + "https://redd.it" + "/" + child_id
       else:
           source_url = link_prefix + "https://redd.it" + "/" + child_id
    else:
           source_url = ""

    if config.SCHEDULE_POSTS == "true":
        delay = config.SCHEDULE_DELAY
        scheduled_time = datetime.now() + timedelta(delay)
    else:
        scheduled_time = None

    toot = mastodon.status_post(
        status=text_prefix + toot_text + author_name + source_url,
        media_ids=[media["id"]],
        spoiler_text=cw_text,
        sensitive=toot_sensitivity,
        visibility=toot_visibility,
        scheduled_at=scheduled_time
    )

    log.info(f'Success!\n\nTitle: {toot_text}\nURL: {config.API_BASE_URL}/notice/{toot["id"]}\n')

    conn.execute("insert into posts (postid) values (?)", (child_id,))
    conn.commit()

    _do_res(conn)


def main():
    mastodon = Mastodon(
        client_id=config.CLIENT_ID,
        client_secret=config.CLIENT_SECRET,
        access_token=config.ACCESS_TOKEN,
        api_base_url=config.API_BASE_URL
    )

    db = sqlite3.connect(config.BOT_STATE)
    db.executescript(
        """
    create table if not exists posts (
        postid text not null
    );

    create table if not exists timestamps (
        ttype int,
        timestamp bigint
    );
    """
    )

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
            remaining = math.trunc(remaining)
            remaining = format_timespan(remaining)
            log.info(f"Remaining time until next check: {remaining}")

        # wait a second before doing it all again
        time.sleep(1)


if __name__ == "__main__":
    main()
