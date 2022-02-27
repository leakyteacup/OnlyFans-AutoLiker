PROFILE_URL = 'https://onlyfans.com/api2/v2/users/'
POSTS_URL = 'https://onlyfans.com/api2/v2/users/{}/posts?limit={}&order=publish_date_desc&skip_users=all&skip_users_dups=1&pinned={}'
POSTS_50_URL = 'https://onlyfans.com/api2/v2/users/{}/posts?limit={}&order=publish_date_desc&skip_users=all&skip_users_dups=1&beforePublishTime={}&pinned=0'
ARCHIVED_POSTS_URL = 'https://onlyfans.com/api2/v2/users/{}/posts/archived?limit={}&order=publish_date_desc&skip_users=all&skip_users_dups=1'
ARCHIVED_POSTS_50_URL = 'https://onlyfans.com/api2/v2/users/{}/posts/archived?limit={}&order=publish_date_desc&skip_users=all&skip_users_dups=1&beforePublishTime={}'
FAVORITE_URL = 'https://onlyfans.com/api2/v2/posts/{}/favorites/{}'

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