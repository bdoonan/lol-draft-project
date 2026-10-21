#pure game logic (no flask) so it can be unit tested on its own
import random
import re
from datetime import date
from urllib.parse import urlparse, parse_qs

MAX_ATTEMPTS = 5
#the first hint unlocks after this many wrong guesses, and each further wrong guess unlocks another
HINT_AFTER = 3
#day 0 of the daily rotation, changing this changes every future match so leave it alone
EPOCH = date(2024, 1, 1)
#international events have no league or split, the whole name is the "season"
INTERNATIONAL = ('Worlds', 'MSI', 'First Stand')

#the daily games on the home page, in display order
#leagues are the word after the year in the tournament name, e.g. '2019 LCK Spring Playoffs' -> 'LCK'
GAMES = [
    {'slug': 'lck', 'name': 'LCK', 'leagues': ('LCK', 'OGN')},
    {'slug': 'lpl', 'name': 'LPL', 'leagues': ('LPL',)},
    {'slug': 'lec', 'name': 'LEC', 'leagues': ('LEC',)},
    {'slug': 'lcs', 'name': 'LCS', 'leagues': ('LCS', 'LTA', 'LTA_North')},
    {'slug': 'international', 'name': 'International', 'leagues': ('Worlds', 'MSI', 'First')},
    {'slug': 'worlds', 'name': 'Worlds', 'leagues': ('Worlds',)},
]
GAMES_BY_SLUG = {g['slug']: g for g in GAMES}
#games whose pools overlap, the first one moves on if both land on the same match
AVOID_SAME = {'international': 'worlds'}


def team_slug(name):
    """file name for a team's logo, 'Anyone's Legend' -> 'anyone-s-legend'"""
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def league_prefix(tournament):
    """'2019 LCK Spring Playoffs' -> 'LCK', '2025 First Stand' -> 'First'"""
    return tournament.split(' ')[1]


def tournament_year(tournament):
    return int(tournament.split(' ')[0])


def _rotation(ids, day, salt):
    """The ids are shuffled once per cycle (seeded by the game and cycle number) and walked in order,
    so every server worker agrees, restarts change nothing, and no match repeats until all have been used."""
    ids = sorted(ids)
    cycle, pos = divmod((day - EPOCH).days, len(ids))
    random.Random(f'{salt}:{cycle}').shuffle(ids)
    return ids, pos


def daily_game_id(ids, day, salt='', avoid=None):
    """Pick a game's match for a day. avoid is another match id it must not equal (overlapping pools)."""
    ids, pos = _rotation(ids, day, salt)
    if ids[pos] == avoid and len(ids) > 1:
        pos = (pos + 1) % len(ids)
    return ids[pos]


def hint_index(day, slug, side):
    """Which player (0-4) the hint button reveals for a side, fixed for the whole day."""
    return random.Random(f'{day.isoformat()}:{slug}:{side}').randrange(5)


def hints_unlocked(misses):
    """how many hints the player has earned: 0 before HINT_AFTER misses, then one more per miss"""
    return max(0, misses - HINT_AFTER + 1)


def parse_tournament(name):
    """'2019 LCK Spring Playoffs' -> (2019, 'LCK', 'Spring Playoffs'), '2019 Worlds' -> (2019, 'International', 'Worlds')"""
    year, _, rest = name.partition(' ')
    if rest in INTERNATIONAL:
        return int(year), 'International', rest
    #underscores join multi word names in the db, e.g. 'LTA_North' or 'Road_to MSI'
    league, _, season = rest.partition(' ')
    return int(year), league.replace('_', ' '), (season or league).replace('_', ' ')


def year_feedback(guess, answer):
    """one history cell, the result values are the css classes in styles.css"""
    if guess == answer:
        result = 'same'
    elif answer < guess:
        result = 'lower'
    else:
        result = 'higher'
    return [{'text': str(guess), 'result': result}]


def event_label(tournament):
    """the tournament name without its year, '2013 OGN Winter Playoffs' -> 'OGN Winter Playoffs'"""
    return tournament.partition(' ')[2].replace('_', ' ')


#rough order events happen in a season, used to sort the event picker
SEASON_ORDER = ('Winter', 'Cup', 'First', 'Spring', 'Road', 'MSI', 'Summer', 'Season', 'Regional', 'Worlds')


def event_order(tournament):
    label = event_label(tournament)
    return next((i for i, word in enumerate(SEASON_ORDER) if word in label), len(SEASON_ORDER)), label


def event_feedback(guess, answer):
    return [{'text': event_label(guess), 'result': 'same' if guess == answer else 'notSame'}]


def side_feedback(team, side, blue, red):
    """one history cell for a blue or red side guess:
    green if it's that side's team, yellow if it played but on the other side, red otherwise"""
    same_side, other_side = (blue, red) if side == 'blue' else (red, blue)
    if team == same_side:
        result = 'same'
    elif team == other_side:
        result = 'inbetween'
    else:
        result = 'notSame'
    return [{'text': team, 'result': result}]


def _timestamp_seconds(value):
    """'1h2m3s' / '3723' -> 3723"""
    if not value:
        return 0
    if value.isdigit():
        return int(value)
    total, num = 0, ''
    for ch in value:
        if ch.isdigit():
            num += ch
        elif ch in 'hms' and num:
            total += int(num) * {'h': 3600, 'm': 60, 's': 1}[ch]
            num = ''
    return total + (int(num) if num else 0)


def youtube_id(url):
    """the video id of a youtube watch/share/live link, or None for anything else (old twitch links, '0')"""
    if not url or url == '0':
        return None
    parsed = urlparse(url)
    host, path = parsed.hostname or '', parsed.path
    if host.endswith('youtu.be'):
        return path.strip('/') or None
    if 'youtube.com' in host:
        if path.startswith('/watch'):
            return parse_qs(parsed.query).get('v', [None])[0]
        if path.startswith(('/live/', '/shorts/', '/embed/')):
            return path.split('/')[2] or None
    return None


def vod_start(url):
    """where in the video the game starts, in seconds"""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    if 'start' in params:
        return _timestamp_seconds(params['start'][0])
    if 't' in params:
        return _timestamp_seconds(params['t'][0])
    if parsed.fragment.startswith('t='):
        return _timestamp_seconds(parsed.fragment[2:])
    return 0
