#looks up the order champions were picked in, for every game in the database
#run from the project root after scraping: python -m flaskr.draftorder
#the scraped match history only lists picks by role, leaguepedia's PicksAndBansS7 table has the draft order
#(it starts in 2017, older games keep the role layout). games already done are skipped, so it is safe to re-run
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from .tournaments import overview_page, tournament_urls

EXPORT = 'https://lol.fandom.com/wiki/Special:CargoExport'
HEADERS = {'User-Agent': 'lol-draftle draft order lookup (fan project)'}
ROOT = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.environ.get('DATABASE', os.path.join(os.path.dirname(ROOT), 'test.db'))
FIRST_YEAR = 2017  # leaguepedia has no pick order data before this
PICK_FIELDS = [f'Team{t}Pick{n}' for t in (1, 2) for n in range(1, 6)]


def normalize(champ):
    """the same clean up scraper.makemaps does: 'Kai'Sa' -> 'kaisa', 'Nunu & Willump' -> 'nunu&willump'"""
    return champ.replace(' ', '').replace('.', '').replace("'", '').lower()


def fetch_draft_rows(page):
    """every game's picks in draft order for one leaguepedia tournament page"""
    params = urllib.parse.urlencode({
        'tables': 'PicksAndBansS7', 'fields': ','.join(PICK_FIELDS), 'format': 'json', 'limit': 500,
        'where': f'OverviewPage="{page}"',
    })
    for attempt in range(5):
        try:
            req = urllib.request.Request(f'{EXPORT}?{params}', headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as res:
                return json.loads(res.read())
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
            wait = 10 * (attempt + 1)
            print(f'  {page}: {e}, retrying in {wait}s', file=sys.stderr)
            time.sleep(wait)
    return None


def match_orders(games, rows):
    """games: [(id, blue picks by role, red picks by role)], rows: leaguepedia rows for the same tournament.
    Returns {id: (blue order, red order)}, each order being role indexes in pick order.
    There is no shared id, so games are matched on the five champions each side picked."""
    unmatched = {}
    for gid, blue, red in games:
        key = (frozenset(map(normalize, blue)), frozenset(map(normalize, red)))
        unmatched.setdefault(key, []).append((gid, [normalize(c) for c in blue], [normalize(c) for c in red]))
    found = {}
    for row in rows:
        team1 = [normalize(row.get(f'Team1Pick{n}') or '') for n in range(1, 6)]
        team2 = [normalize(row.get(f'Team2Pick{n}') or '') for n in range(1, 6)]
        #team1 is normally blue side, but check both ways in case the wiki has them swapped
        for blue_picks, red_picks in ((team1, team2), (team2, team1)):
            candidates = unmatched.get((frozenset(blue_picks), frozenset(red_picks)))
            if candidates:
                gid, blue_roles, red_roles = candidates.pop(0)
                found[gid] = ([blue_roles.index(c) for c in blue_picks], [red_roles.index(c) for c in red_picks])
                break
    return found


def main():
    conn = sqlite3.connect(DATABASE)
    conn.execute('CREATE TABLE IF NOT EXISTS pickOrder(id INT PRIMARY KEY, blue TEXT, red TEXT)')
    done = {r[0] for r in conn.execute('SELECT id FROM pickOrder')}
    pages = {name: overview_page(url) for name, url in tournament_urls(FIRST_YEAR, 2100).items()}
    tournaments = [r[0] for r in conn.execute('SELECT DISTINCT tournament FROM game ORDER BY tournament')]
    total_found = total_missing = 0
    for tournament in tournaments:
        if int(tournament[:4]) < FIRST_YEAR:
            continue
        games = [(r[0], r[1:6], r[6:11]) for r in conn.execute(
            'SELECT g.id, b.top, b.jg, b.mid, b.adc, b.sup, r.top, r.jg, r.mid, r.adc, r.sup FROM game g '
            'JOIN blueTeam b ON b.id = g.id JOIN redTeam r ON r.id = g.id WHERE g.tournament = ?', (tournament,))
            if r[0] not in done]
        page = pages.get(tournament)
        if not games or not page:
            continue
        rows = fetch_draft_rows(page)
        if rows is None:
            print(f'{tournament}: could not reach leaguepedia, skipped')
            continue
        found = match_orders(games, rows)
        conn.executemany('INSERT OR REPLACE INTO pickOrder(id, blue, red) VALUES (?, ?, ?)', [
            (gid, ','.join(map(str, blue)), ','.join(map(str, red))) for gid, (blue, red) in found.items()])
        conn.commit()
        total_found += len(found)
        total_missing += len(games) - len(found)
        print(f'{tournament}: {len(found)}/{len(games)} matched')
        time.sleep(2)
    conn.close()
    print(f'done: {total_found} games got a pick order, {total_missing} could not be matched')


if __name__ == '__main__':
    main()
