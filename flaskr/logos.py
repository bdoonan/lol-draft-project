#downloads every team's logo from leaguepedia into static/images/teams/
#run from the project root after scraping: python -m flaskr.logos
#files that already exist are skipped, so it is safe to run again after adding tournaments
import json
import os
import sqlite3
import sys
import time
import urllib.parse
import urllib.request

from .game import team_slug

API = 'https://lol.fandom.com/api.php'
HEADERS = {'User-Agent': 'lol-draftle logo downloader (fan project)'}
ROOT = os.path.dirname(os.path.abspath(__file__))
TEAMS_DIR = os.path.join(ROOT, 'static', 'images', 'teams')
DATABASE = os.environ.get('DATABASE', os.path.join(os.path.dirname(ROOT), 'test.db'))
BATCH = 50  # the most titles the mediawiki api accepts per query
LOGO_SIZE = 128  # px, about 3x the size shown on the page so it stays sharp on high dpi screens


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as res:
        return res.read()


def extension(image):
    """fandom serves resized images as webp whatever the original was"""
    if image[:4] == b'RIFF' and image[8:12] == b'WEBP':
        return '.webp'
    if image[:3] == b'\xff\xd8\xff':
        return '.jpg'
    if image.lstrip()[:4] in (b'<svg', b'<?xm'):
        return '.svg'
    return '.png'


def downloaded():
    """slugs of the logos already on disk, whatever their extension"""
    return {name.rsplit('.', 1)[0] for name in os.listdir(TEAMS_DIR)}


def team_names():
    conn = sqlite3.connect(DATABASE)
    names = {n for row in conn.execute('SELECT blue, red FROM game') for n in row if n}
    conn.close()
    return sorted(names)


def logo_urls(teams):
    """team name -> image url, for the teams leaguepedia has a 'logo square' file for"""
    found = {}
    for i in range(0, len(teams), BATCH):
        batch = teams[i:i + BATCH]
        titles = {f'File:{team}logo square.png': team for team in batch}
        query = urllib.parse.urlencode({
            #iiurlwidth asks for a resized copy, the originals can be several MB and are shown at 40px
            'action': 'query', 'prop': 'imageinfo', 'iiprop': 'url', 'iiurlwidth': LOGO_SIZE,
            'redirects': 1, 'format': 'json',
            'titles': '|'.join(titles),
        })
        data = json.loads(get(f'{API}?{query}'))['query']
        #the api normalizes titles (spaces/underscores, first letter) and follows redirects,
        #so follow each of our titles forward to the page it ends up on (several teams can share one logo)
        forward = {s['from']: s['to'] for s in data.get('normalized', []) + data.get('redirects', [])}
        images = {p['title']: p['imageinfo'][0].get('thumburl') or p['imageinfo'][0]['url']
                  for p in data['pages'].values() if 'imageinfo' in p}
        for title, team in titles.items():
            seen = set()
            while title in forward and title not in seen:
                seen.add(title)
                title = forward[title]
            if title in images:
                found[team] = images[title]
        time.sleep(1)
    return found


def main():
    os.makedirs(TEAMS_DIR, exist_ok=True)
    teams = team_names()
    have = downloaded()
    todo = [t for t in teams if team_slug(t) not in have]
    print(f'{len(teams)} teams, {len(teams) - len(todo)} logos already downloaded')
    if not todo:
        return
    urls = logo_urls(todo)
    for n, team in enumerate(sorted(urls), 1):
        try:
            image = get(urls[team])
            with open(os.path.join(TEAMS_DIR, team_slug(team) + extension(image)), 'wb') as f:
                f.write(image)
        except OSError as e:
            print(f'  failed {team}: {e}', file=sys.stderr)
        if n % 25 == 0:
            print(f'  {n}/{len(urls)}')
        time.sleep(0.2)
    missing = sorted(set(todo) - set(urls))
    print(f'downloaded {len(urls)}, no logo found for {len(missing)}')
    for team in missing:
        print('  ' + team)


if __name__ == '__main__':
    main()
