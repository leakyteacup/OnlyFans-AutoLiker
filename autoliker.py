import os
import sys
import json
import argparse
import logging
import time
import random
import math
from threading import Thread

import requests

from autoliker.constants import (
    PROFILE_URL,
    POSTS_URL,
    POSTS_100_URL,
    ARCHIVED_POSTS_URL,
    ARCHIVED_POSTS_100_URL,
    FAVORITE_URL,
    HEADERS,
    ICONS
)


class Logger:
    FORMAT = '%(levelname)s: %(message)s'

    def __init__(self):
        self.log = logging.getLogger(name=__name__)
        self.log.setLevel(level=logging.DEBUG)
        if not self.log.handlers:
            _formatter = logging.Formatter(fmt=self.FORMAT)
            _sh = logging.StreamHandler()
            _sh.setLevel(logging.INFO)
            _sh.setFormatter(fmt=_formatter)
            self.log.addHandler(hdlr=_sh)

    def debug(self, message):
        self.log.debug(message)

    def info(self, message):
        self.log.info(message)

    def error(self, message):
        self.log.error(message)


class OnlyFans(Logger):
    def __init__(self, args):
        super().__init__()
        # Parse args:
        self.timeline = args.timeline
        self.archived = args.archived
        # Create authentication:
        auth_path = os.path.join(sys.path[0], 'auth.json')
        with open(auth_path) as f:
            auth = json.load(f)['auth']
            auth_id = auth['auth_id']
            auth_uid_ = auth['auth_uid_']
            if not auth_uid_:
                del auth['auth_uid_']
            else:
                auth[f"auth_uid_{auth_id}"] = auth.pop('auth_uid_')
            _cookies = [f'{k}={v}' for k, v in auth.items() if k !=
                        'user_agent' and k != 'app_token']
            headers = {
                "user-agent": auth['user_agent'], 'cookie': ";".join(_cookies)}
            for k, v in HEADERS.items():
                headers[k] = v
            self.headers = headers
            self.app_token = auth['app_token']
        # Other constructors:
        self.username = args.username
        self.id = None
        self.has_pinned_posts = None
        self.posts_count = None
        self.archived_posts_count = None
        self.ids = None
        self.archived_ids = None
        self.stop = False

    def scrape_user(self):
        with requests.Session() as s:
            r = s.get(PROFILE_URL.format(
                self.username, self.app_token), headers=self.headers)
        self.log.debug(r.status_code)
        if r.ok:
            user = r.json()
            self.id = user['id']
            self.has_pinned_posts = user['hasPinnedPosts']
            self.posts_count = user['postsCount']
            self.archived_posts_count = user['archivedPostsCount']
        else:
            self.set_stop_true()
            self.log.error(
                f"Unable to scrape user profile -- Received {r.status_code} STATUS CODE")

    def scrape_posts(self, pinned=0, array=[], count=0, cycles=0, time=0):
        if not array:
            if self.archived:
                return None
            if self.has_pinned_posts:
                with requests.Session() as s:
                    r = s.get(
                        POSTS_URL.format(
                            self.id, self.posts_count, 1, self.app_token), headers=self.headers)
                if r.ok:
                    array = r.json()
                else:
                    self.set_stop_true()
                    self.log.error(
                        f'Unable to scrape pinned posts -- Received {r.status_code} STATUS CODE')
            if self.posts_count > 100:
                cycles = math.floor(self.posts_count / 100)
        url = POSTS_URL if not time else POSTS_100_URL
        slot = pinned if not time else time
        with requests.Session() as s:
            r = s.get(url.format(
                self.id, self.posts_count, slot, self.app_token),
                headers=self.headers)
        if r.ok:
            posts = r.json()
            if cycles:
                if count < cycles:
                    count += 1
                    list_posts = array + posts
                    posted_at_precise = posts[-1]['postedAtPrecise']
                    posts = self.scrape_posts(
                        array=list_posts, count=count, cycles=cycles, time=posted_at_precise)
                    if time:
                        return posts
                else:
                    return array + posts
            else:
                posts += array
            unfavorited_posts = [
                post for post in posts if not post['isFavorite']]
            self.ids = [
                post['id'] for post in unfavorited_posts if post['isOpened']]
        else:
            self.set_stop_true()
            self.log.error(
                f'Unable to scrape posts -- Received {r.status_code} STATUS CODE')

    def scrape_archived_posts(self, array=[], count=0, cycles=0, time=0):
        if not array:
            if self.timeline:
                return None
            if self.archived_posts_count > 100:
                cycles = math.floor(self.archived_posts_count / 100)
        url = ARCHIVED_POSTS_URL if not time else ARCHIVED_POSTS_100_URL
        with requests.Session() as s:
            if time:
                r = s.get(url.format(
                    self.id, self.archived_posts_count, time, self.app_token), headers=self.headers)
            else:
                r = s.get(url.format(
                    self.id, self.archived_posts_count, self.app_token), headers=self.headers)
        if r.ok:
            posts = r.json()
            if cycles:
                if count < cycles:
                    count += 1
                    list_posts = array + posts
                    posted_at_precise = posts[-1]['postedAtPrecise']
                    posts = self.scrape_archived_posts(
                        array=list_posts, count=count, cycles=cycles, time=posted_at_precise)
                    if time:
                        return posts
                else:
                    return array + posts
            else:
                posts += array
            unfavorited_posts = [
                post for post in posts if not post['isFavorite']]
            self.archived_ids = [
                post['id'] for post in unfavorited_posts if post['isOpened']]
        else:
            self.set_stop_true()
            self.log.error(
                f'Unable to scrape posts -- Received {r.status_code} STATUS CODE')

    def like_posts(self, array, message='post'):
        if not array:
            return None
        length = len(array)
        enum = enumerate(array, 1)
        for c, post_id in enum:
            time.sleep(random.uniform(1, 2.25))
            with requests.Session() as s:
                r = s.post(FAVORITE_URL.format(
                    post_id, self.id, self.app_token), headers=self.headers)
            if r.ok:
                print(
                    f'Successfully liked {message} ({c}/{length})', end='\r', flush=True)
            else:
                self.log.error(
                    f'Unable to like post -- Received {r.status_code} STATUS CODE')

    def set_stop_true(self):
        self.stop = True

    def spinner(self):
        while True:
            for icon in ICONS:
                print(icon, end='\r', flush=True)
                if self.stop:
                    return None
                time.sleep(0.1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('username', type=str,
                        help="username of an OnlyFans content creator (that you're subscribed to)")
    parser.add_argument('-t', '--timeline',
                        help='only like timeline posts', action='store_true')
    parser.add_argument('-a', '--archived',
                        help='only like archived posts', action='store_true')
    args = parser.parse_args()
    onlyfans = OnlyFans(args)
    t1 = Thread(target=onlyfans.spinner)
    t1.start()
    onlyfans.scrape_user()
    onlyfans.scrape_posts()
    if onlyfans.archived_posts_count:
        onlyfans.scrape_archived_posts()
    onlyfans.set_stop_true()
    onlyfans.like_posts(onlyfans.ids)
    if onlyfans.archived_posts_count:
        onlyfans.like_posts(onlyfans.archived_ids, 'archived post')


if __name__ == '__main__':
    main()
