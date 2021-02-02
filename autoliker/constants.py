PROFILE_URL = 'https://onlyfans.com/api2/v2/users/{}?app-token={}'
POSTS_URL = 'https://onlyfans.com/api2/v2/users/{}/posts?limit={}&order=publish_date_desc&skip_users=all&skip_users_dups=1&pinned={}&app-token={}'
POSTS_100_URL = 'https://onlyfans.com/api2/v2/users/{}/posts?limit={}&order=publish_date_desc&skip_users=all&skip_users_dups=1&beforePublishTime={}&pinned=0&app-token={}'
ARCHIVED_POSTS_URL = 'https://onlyfans.com/api2/v2/users/{}/posts/archived?limit={}&order=publish_date_desc&skip_users=all&skip_users_dups=1&app-token={}'
ARCHIVED_POSTS_100_URL = 'https://onlyfans.com/api2/v2/users/{}/posts/archived?limit={}&order=publish_date_desc&skip_users=all&skip_users_dups=1&beforePublishTime={}&app-token={}'
FAVORITE_URL = 'https://onlyfans.com/api2/v2/posts/{}/favorites/{}?app-token={}'

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br",
    "host": "onlyfans.com",
}

ICONS = [
    '(•    )',
    '( •   )',
    '(  •  )',
    '(   • )',
    '(    •)',
    '(   • )',
    '(  •  )',
    '( •   )',
]
