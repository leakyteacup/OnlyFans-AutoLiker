import argparse
import logging
import time
import random
import math
from threading import Thread
import hashlib
from urllib.parse import urlparse

import requests

from autoliker.constants import (
    PROFILE_URL,
    POSTS_URL,
    POSTS_50_URL,
    ARCHIVED_POSTS_URL,
    ARCHIVED_POSTS_50_URL,
    FAVORITE_URL,
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
        self.auth_id = "your user auth ID"
        self.cookies = "put your cookies here...fp=; sess=; csrf=; ref_src=; auth_id=; st=;"
        self.user_agent = "Mozilla/5.0...this is your user agent"
        self.app_token = "whatever app token is at the moment"
        self.x_bc ="your x-bc"

        # Other constructors:
        self.username = args.username
        self.unlike = args.unlike
        self.id = None
        self.has_pinned_posts = None
        self.posts_count = None
        self.archived_posts_count = None
        self.ids = None
        self.archived_ids = None
        self.stop = False

    def get_dynamic_rules(self):
        r = requests.get("https://raw.githubusercontent.com/DATAHOARDERS/dynamic-rules/main/onlyfans.json")
        return r.json()

    def create_signed_headers(self, link: str, auth_id: int, dynamic_rules: dict):
        final_time = str(int(round(time.time()*1000.0)))
        path = urlparse(link).path
        query = urlparse(link).query
        path = path if not query else f"{path}?{query}"
        # print(path)
        a = [dynamic_rules["static_param"], final_time, path, str(auth_id)]
        msg = "\n".join(a)
        message = msg.encode("utf-8")
        hash_object = hashlib.sha1(message)
        sha_1_sign = hash_object.hexdigest()
        sha_1_b = sha_1_sign.encode("ascii")
        checksum = (
                sum([sha_1_b[number] for number in dynamic_rules["checksum_indexes"]])
                + dynamic_rules["checksum_constant"]
        )
        headers = {}
        headers["sign"] = dynamic_rules["format"].format(sha_1_sign, abs(checksum))
        headers["time"] = final_time
        headers["x-bc"] = self.x_bc
        headers["user-agent"] = self.user_agent
        headers["cookie"] = self.cookies
        headers["app-token"] = self.app_token
        headers["accept"] = "application/json, text/plain, */*"
        headers["accept-encoding"] = "gzip, deflate, br"
        # print(headers)
        return headers

    def scrape_user(self):
        with requests.Session() as s:
            link = PROFILE_URL + self.username
            r = s.get(link, headers=self.create_signed_headers(link, 0, self.get_dynamic_rules()))
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
                    link = POSTS_URL.format(self.id, self.posts_count, 1)
                    temp_headers = self.create_signed_headers(link, self.auth_id, self.get_dynamic_rules())
                    temp_headers["user-id"] = self.auth_id
                    r = s.get(link, headers=temp_headers)
                if r.ok:
                    array = r.json()
                else:
                    self.set_stop_true()
                    self.log.error(
                        f'Unable to scrape pinned posts -- Received {r.status_code} STATUS CODE')
            if self.posts_count > 50:
                cycles = math.floor(self.posts_count / 50)
        url = POSTS_URL if not time else POSTS_50_URL
        slot = pinned if not time else time
        with requests.Session() as s:
            link = url.format(self.id, self.posts_count, slot)
            temp_headers = self.create_signed_headers(link, self.auth_id, self.get_dynamic_rules())
            temp_headers["user-id"] = self.auth_id
            r = s.get(link, headers=temp_headers)
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
            if self.unlike:
                posts = [post for post in posts if post['isFavorite']]
            else:
                posts = [post for post in posts if not post['isFavorite']]
            self.ids = [post['id'] for post in posts if post['isOpened']]
        else:
            self.set_stop_true()
            self.log.error(
                f'Unable to scrape posts -- Received {r.status_code} STATUS CODE')

    def scrape_archived_posts(self, array=[], count=0, cycles=0, time=0):
        if not array:
            if self.timeline:
                return None
            if self.archived_posts_count > 50:
                cycles = math.floor(self.archived_posts_count / 50)
        url = ARCHIVED_POSTS_URL if not time else ARCHIVED_POSTS_50_URL
        with requests.Session() as s:
            if time:
                link = url.format(self.id, self.archived_posts_count, time)
                temp_headers = self.create_signed_headers(link, self.auth_id, self.get_dynamic_rules())
                temp_headers["user-id"] = self.auth_id
                r = s.get(link, headers=temp_headers)
            else:
                link = url.format(self.id, self.archived_posts_count)
                temp_headers = self.create_signed_headers(link, self.auth_id, self.get_dynamic_rules())
                temp_headers["user-id"] = self.auth_id
                r = s.get(link, headers=temp_headers)
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
            if self.unlike:
                posts = [post for post in posts if post['isFavorite']]
            else:
                posts = [post for post in posts if not post['isFavorite']]
            self.archived_ids = [post['id']
                                 for post in posts if post['isOpened']]
        else:
            self.set_stop_true()
            self.log.error(
                f'Unable to scrape posts -- Received {r.status_code} STATUS CODE')

    def handle_posts(self, array, message='post'):
        if not array:
            return None
        length = len(array)
        enum = enumerate(array, 1)
        for c, post_id in enum:
            time.sleep(random.uniform(1, 2.25))
            with requests.Session() as s:
                link = FAVORITE_URL.format(post_id, self.id)
                temp_headers = self.create_signed_headers(link, self.auth_id, self.get_dynamic_rules())
                temp_headers["user-id"] = self.auth_id
                r = s.post(link, headers=temp_headers)
            if r.ok:
                if self.unlike:
                    print(
                        f'Successfully unliked {message} ({c}/{length})')
                else:
                    print(
                        f'Successfully liked {message} ({c}/{length})')
            else:
                self.log.error(
                    f"Unable to like post at 'onlyfans.com/{post_id}/{self.username}' -- Received {r.status_code} STATUS CODE")

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
    parser.add_argument('-u', '--unlike',
                        help='removes your likes from posts', action='store_true')
    args = parser.parse_args()
    onlyfans = OnlyFans(args)
    t1 = Thread(target=onlyfans.spinner)
    t1.start()
    onlyfans.scrape_user()
    onlyfans.scrape_posts()
    if onlyfans.archived_posts_count:
        onlyfans.scrape_archived_posts()
    onlyfans.set_stop_true()
    print(f"Found {len(onlyfans.ids)} posts to process.")
    onlyfans.handle_posts(onlyfans.ids)
    if onlyfans.archived_posts_count:
        onlyfans.handle_posts(onlyfans.archived_ids, 'archived post')


if __name__ == '__main__':
    main()