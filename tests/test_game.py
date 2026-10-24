import re
import sqlite3
from datetime import date, timedelta

import pytest

from flaskr import create_app
from flaskr.game import (
    EPOCH, GAMES, daily_game_id, parse_tournament, side_feedback, team_slug, vod_start, year_feedback,
    youtube_id
)

ROLES = ('top', 'jg', 'mid', 'adc', 'sup')
DAY = '2025-01-01'
YEARS = range(2013, 2021)
TOURNAMENT_NAMES = {
    'LCK': 'LCK Spring Playoffs', 'OGN': 'OGN Summer Playoffs', 'LPL': 'LPL Spring Playoffs',
    'LEC': 'LEC Summer Playoffs', 'LCS': 'LCS Spring Playoffs', 'LTA_North': 'LTA_North Spring Playoffs',
    'Worlds': 'Worlds', 'MSI': 'MSI', 'First': 'First Stand',
}


def fixture_games():
    """(id, tournament, red, blue): two games per league per year, three teams per league per year"""
    rows = []
    for league, name in TOURNAMENT_NAMES.items():
        for year in YEARS:
            a, b, c = (f'{league}{year}Team{i}' for i in 'ABC')
            rows.append((len(rows), f'{year} {name}', b, a))
            rows.append((len(rows), f'{year} {name}', a, c))
    #a year with worlds but no msi, like 2013, 2014 and 2020 in the real data
    rows.append((len(rows), '2012 Worlds', 'Worlds2012TeamB', 'Worlds2012TeamA'))
    return rows


GAME_ROWS = fixture_games()


@pytest.fixture
def app(tmp_path):
    path = tmp_path / 'test.db'
    conn = sqlite3.connect(path)
    conn.execute('CREATE TABLE game(id INT PRIMARY KEY, tournament TEXT, red TEXT, blue TEXT, vod TEXT)')
    cols = ', '.join([f'{r} TEXT' for r in ROLES] + [f'ban{i} TEXT' for i in range(1, 6)] +
                     [f'{r}Player TEXT' for r in ROLES])
    for table in ('blueTeam', 'redTeam'):
        conn.execute(f'CREATE TABLE {table}(id INT, {cols})')
    for gid, tourney, red, blue in GAME_ROWS:
        conn.execute('INSERT INTO game VALUES (?,?,?,?,?)', (gid, tourney, red, blue, '0'))
        for table in ('blueTeam', 'redTeam'):
            conn.execute(f'INSERT INTO {table} VALUES ({",".join("?" * 16)})',
                         (gid, *['ahri'] * 10, *[f'{table}Player{gid}x{i}' for i in range(5)]))
    conn.commit()
    conn.close()
    return create_app({'TESTING': True, 'SECRET_KEY': 'test', 'DATABASE': str(path), 'FORCE_DAY': DAY})


@pytest.fixture
def client(app):
    return app.test_client()


def answer(app, slug):
    from flaskr.answer import todays_id
    with app.test_request_context():
        gid = todays_id(slug)
    _, tournament, red, blue = GAME_ROWS[gid]
    return {'tournament': tournament, 'year': int(tournament[:4]), 'blue': blue, 'red': red}


def win(client, app, slug):
    a = answer(app, slug)
    if client.post(f'/api/{slug}/guess', json={'year': a['year']}).json['stage'] == 'event':
        client.post(f'/api/{slug}/guess', json={'event': a['tournament']})
    client.post(f'/api/{slug}/guess', json={'team': a['blue']})
    return client.post(f'/api/{slug}/guess', json={'team': a['red']})


#---------- pure logic ----------
def test_daily_pick_is_deterministic_and_cycles_without_repeats():
    ids = list(range(10))
    day = date(2025, 3, 1)
    assert daily_game_id(ids, day, 'lck') == daily_game_id(list(reversed(ids)), day, 'lck')
    cycle_start = EPOCH + timedelta(days=10 * 7)
    picks = [daily_game_id(ids, cycle_start + timedelta(days=i), 'lck') for i in range(10)]
    assert sorted(picks) == ids
    assert daily_game_id([1, 2], day, 'x', avoid=daily_game_id([1, 2], day, 'x')) != daily_game_id([1, 2], day, 'x')


def test_parse_tournament():
    assert parse_tournament('2019 LCK Spring Playoffs') == (2019, 'LCK', 'Spring Playoffs')
    assert parse_tournament('2019 Worlds') == (2019, 'International', 'Worlds')
    assert parse_tournament('2025 LTA_North Spring Playoffs') == (2025, 'LTA North', 'Spring Playoffs')


def test_feedback():
    assert year_feedback(2020, 2019)[0]['result'] == 'lower'
    assert year_feedback(2018, 2019)[0]['result'] == 'higher'
    assert year_feedback(2019, 2019)[0]['result'] == 'same'
    assert side_feedback('A', 'blue', 'A', 'B')[0]['result'] == 'same'
    assert side_feedback('B', 'blue', 'A', 'B')[0]['result'] == 'inbetween'
    assert side_feedback('C', 'red', 'A', 'B')[0]['result'] == 'notSame'


def test_youtube_links():
    #the url shapes found in the scraped data
    assert youtube_id('https://youtu.be/C8aOmmu9BLQ?si=-Dwz9M2t&t=186') == 'C8aOmmu9BLQ'
    assert vod_start('https://youtu.be/C8aOmmu9BLQ?si=-Dwz9M2t&t=186') == 186
    assert youtube_id('https://www.youtube.com/live/-tucUfEwqpg?feature=share&t=3024') == '-tucUfEwqpg'
    assert vod_start('http://www.youtube.com/watch?v=4I20u64ULxg&t=2m20s') == 140
    assert vod_start('http://www.youtube.com/watch?v=MMbuK7Oq7_c#t=4m52s') == 292
    assert youtube_id('http://www.youtube.com/watch?v=Y_Uq022i2bQ&list=UUvq') == 'Y_Uq022i2bQ'
    assert youtube_id('http://www.twitch.tv/ongamenet/b/1?t=2h') is None
    assert youtube_id('0') is None and youtube_id('') is None


def test_vod_info_checks_youtube_once(app, monkeypatch):
    from flaskr import answer as views
    calls = []

    def fake_status(video_id):
        calls.append(video_id)
        return {'alive': 200, 'dead': 404, 'offline': None}[video_id]

    monkeypatch.setattr(views, '_oembed_status', fake_status)
    monkeypatch.setattr(views, '_vod_alive', {})
    with app.test_request_context():
        vod = views.vod_info('https://youtu.be/alive?t=90')
        assert vod['watch'] == 'https://www.youtube.com/watch?v=alive&t=90s' and vod['start'] == 90
        assert 'youtube-nocookie.com/embed/alive' in vod['embed'] and vod['thumb'].endswith('/alive/hqdefault.jpg')
        views.vod_info('https://youtu.be/alive')
        assert views.vod_info('https://youtu.be/dead') is None
        #youtube unreachable: still shown, and asked again next time
        assert views.vod_info('https://youtu.be/offline') is not None
        views.vod_info('https://youtu.be/offline')
        assert views.vod_info('http://www.twitch.tv/x/b/1') is None and views.vod_info('0') is None
    assert calls == ['alive', 'dead', 'offline', 'offline']


#---------- pools ----------
def test_pools(app):
    from flaskr import db
    with app.test_request_context():
        lck = {GAME_ROWS[i][1].split(' ')[1] for i in db.pool('lck')}
        assert lck == {'LCK', 'OGN'}
        assert {GAME_ROWS[i][1].split(' ')[1] for i in db.pool('lcs')} == {'LCS', 'LTA_North'}
        assert set(db.pool('worlds')) < set(db.pool('international'))
        assert db.tournaments('lck', 2015) == ['2015 LCK Spring Playoffs', '2015 OGN Summer Playoffs']
        assert db.tournaments('international', 2015) == ['2015 First Stand', '2015 MSI', '2015 Worlds']
        assert db.tournaments('lcs', 2015) == ['2015 LCS Spring Playoffs', '2015 LTA_North Spring Playoffs']
        assert db.tournaments('worlds', 2015) == ['2015 Worlds']
        assert db.tournament_teams('2015 OGN Summer Playoffs') == [f'OGN2015Team{i}' for i in 'ABC']


def test_international_never_matches_worlds(app):
    for offset in range(60):
        app.config['FORCE_DAY'] = (date(2025, 1, 1) + timedelta(days=offset)).isoformat()
        assert answer(app, 'international') != answer(app, 'worlds')


#---------- pages and api ----------
def test_home_lists_every_game(client):
    html = client.get('/').get_data(as_text=True)
    for g in GAMES:
        assert f'/play/{g["slug"]}' in html
    assert client.get('/play/nope').status_code == 404


def test_play_page_does_not_leak_answer(client, app):
    a = answer(app, 'lck')
    html = client.get('/play/lck').get_data(as_text=True)
    assert 'TeamPlayer' not in html
    assert a['blue'] not in html and a['red'] not in html and a['tournament'] not in html


def test_win_flow_lock_and_other_games_untouched(client, app):
    a = answer(app, 'lpl')
    wrong_year = 2013 if a['year'] != 2013 else 2014
    r = client.post('/api/lpl/guess', json={'year': wrong_year})
    assert r.json['attemptsLeft'] == 4 and 'teams' not in r.json
    #a team guess is rejected while still on the year stage
    assert client.post('/api/lpl/guess', json={'team': a['blue']}).status_code == 400
    r = client.post('/api/lpl/guess', json={'year': a['year']})
    assert r.json['stage'] == 'blue' and r.json['year'] == a['year'] and 'blueTeam' not in r.json
    assert all(t.startswith(f'LPL{a["year"]}') for t in r.json['teams'])
    #the red team guessed for blue is yellow and costs an attempt
    r = client.post('/api/lpl/guess', json={'team': a['red']})
    assert r.json['guesses'][-1] == {'kind': 'blue', 'cells': [{'text': a['red'], 'result': 'inbetween'}]}
    assert r.json['stage'] == 'blue' and r.json['attemptsLeft'] == 3
    r = client.post('/api/lpl/guess', json={'team': a['blue']})
    assert r.json['stage'] == 'red' and r.json['blueTeam'] == a['blue'] and r.json['attemptsLeft'] == 3
    #the blue team can't be guessed again for red
    assert client.post('/api/lpl/guess', json={'team': a['blue']}).status_code == 400
    r = client.post('/api/lpl/guess', json={'team': a['red']})
    assert r.json['stage'] == 'won' and r.json['result']['attempts'] == 3
    assert r.json['result']['tournament'] == a['tournament']
    assert client.post('/api/lpl/guess', json={'year': a['year']}).status_code == 409
    #the other games are still open
    assert client.post('/api/lec/guess', json={'year': answer(app, 'lec')['year']}).json['stage'] == 'blue'
    home = client.get('/').get_data(as_text=True)
    assert 'Won in 3' in home and 'In progress' in home


def test_invalid_team_guesses(client, app):
    a = answer(app, 'lck')
    assert client.post('/api/lck/guess', json={'year': 'abc'}).status_code == 400
    client.post('/api/lck/guess', json={'year': a['year']})
    assert client.post('/api/lck/guess', json={'team': a['blue']}).status_code == 400  # still on the event step
    assert client.post('/api/lck/guess', json={'event': '2015 LPL Spring Playoffs'}).status_code == 400
    client.post('/api/lck/guess', json={'event': a['tournament']})
    assert client.post('/api/lck/guess', json={'team': 'LPL2015TeamA'}).status_code == 400
    assert client.post('/api/lck/guess', json={'team': None}).status_code == 400


def test_event_step(client, app):
    a = answer(app, 'international')
    r = client.post('/api/international/guess', json={'year': a['year']})
    assert r.json['stage'] == 'event' and 'teams' not in r.json
    assert {e['text'] for e in r.json['events']} == {'Worlds', 'MSI', 'First Stand'}
    wrong = next(e['value'] for e in r.json['events'] if e['value'] != a['tournament'])
    r = client.post('/api/international/guess', json={'event': wrong})
    assert r.json['guesses'][-1]['cells'][0]['result'] == 'notSame' and r.json['attemptsLeft'] == 4
    r = client.post('/api/international/guess', json={'event': a['tournament']})
    assert r.json['stage'] == 'blue' and r.json['event'] == a['tournament'][5:]
    #teams are narrowed to that one tournament
    assert len(r.json['teams']) == 3 and a['blue'] in r.json['teams']
    #the worlds tab only has one event per year, so it goes straight to the teams
    assert client.post('/api/worlds/guess', json={'year': answer(app, 'worlds')['year']}).json['stage'] == 'blue'


def test_international_asks_the_event_in_worlds_only_years(app):
    from flaskr import db
    from flaskr import answer as views
    with app.test_request_context():
        #msi is offered even though only worlds happened, so the step isn't skipped
        assert db.tournaments('international', 2012) == ['2012 MSI', '2012 Worlds']
        assert views.next_stage('international', 'year', {'year': 2012}) == 'event'
        #the worlds tab still goes straight to the teams
        assert db.tournaments('worlds', 2012) == ['2012 Worlds']
        assert views.next_stage('worlds', 'year', {'year': 2012}) == 'blue'
        #region tabs don't get extra options
        assert db.tournaments('lck', 2015) == ['2015 LCK Spring Playoffs', '2015 OGN Summer Playoffs']


def test_loss_spread_across_steps(client, app):
    a = answer(app, 'lcs')
    wrong_years = [y for y in YEARS if y != a['year']][:2]
    for y in wrong_years:
        client.post('/api/lcs/guess', json={'year': y})
    r = client.post('/api/lcs/guess', json={'year': a['year']})
    wrong_event = next(e['value'] for e in r.json['events'] if e['value'] != a['tournament'])
    client.post('/api/lcs/guess', json={'event': wrong_event})
    r = client.post('/api/lcs/guess', json={'event': a['tournament']})
    other = next(t for t in r.json['teams'] if t not in (a['blue'], a['red']))
    client.post('/api/lcs/guess', json={'team': other})
    client.post('/api/lcs/guess', json={'team': a['blue']})
    r = client.post('/api/lcs/guess', json={'team': other})
    assert r.json['stage'] == 'lost' and r.json['attemptsLeft'] == 0


def test_old_both_teams_session_is_restarted(client, app):
    with client.session_transaction() as s:
        s['games'] = {'day': DAY, 'lck': {'stage': 'teams', 'guesses': [2015, ['A', 'B']], 'hints': []}}
    assert '"stage": "year"' in client.get('/play/lck').get_data(as_text=True)


def test_loss_after_five_misses(client, app):
    a = answer(app, 'worlds')
    wrong = [y for y in YEARS if y != a['year']]
    client.post('/api/worlds/guess', json={'year': wrong[0]})
    assert client.post('/api/worlds/guess', json={'year': wrong[0]}).status_code == 400  # repeat is free
    for y in wrong[1:5]:
        r = client.post('/api/worlds/guess', json={'year': y})
    assert r.json['stage'] == 'lost' and r.json['result']['blueTeam'] == a['blue']


def test_hints_unlock_per_game(client, app):
    wrong = [y for y in YEARS if y != answer(app, 'lec')['year']]
    assert client.post('/api/lec/hint', json={'side': 'blue'}).status_code == 403
    for y in wrong[:3]:
        r = client.post('/api/lec/guess', json={'year': y})
    assert r.json['hintsAvailable'] == 1
    r = client.post('/api/lec/hint', json={'side': 'blue'})
    assert set(r.json['hints']) == {'blue'} and r.json['hints']['blue']['name'].startswith('blueTeamPlayer')
    assert client.post('/api/lec/hint', json={'side': 'red'}).status_code == 403
    #misses in one game don't unlock hints in another
    assert client.post('/api/lcs/hint', json={'side': 'blue'}).status_code == 403


def test_new_day_resets_every_game(client, app):
    win(client, app, 'lck')
    app.config['FORCE_DAY'] = '2025-01-02'
    assert '"guesses": []' in client.get('/play/lck').get_data(as_text=True)


def test_session_cookie_stays_small(client, app):
    for g in GAMES:
        wrong = [y for y in YEARS if y != answer(app, g['slug'])['year']]
        for y in wrong[:4]:
            client.post(f'/api/{g["slug"]}/guess', json={'year': y})
        win(client, app, g['slug'])
    cookie = client.get_cookie('session')
    assert len(cookie.value) < 4000


def test_logos(client, app, tmp_path, monkeypatch):
    from flaskr import answer as views
    assert team_slug("Anyone's Legend") == 'anyone-s-legend'
    #point the static folder at a temp copy holding one team logo and one league logo
    static = tmp_path / 'static'
    (static / 'images' / 'teams').mkdir(parents=True)
    (static / 'images' / 'leagues').mkdir(parents=True)
    monkeypatch.setattr(views, '_oembed_status', lambda video_id: 404)
    a = answer(app, 'lpl')
    (static / 'images' / 'teams' / f'{team_slug(a["blue"])}.webp').write_bytes(b'x')
    (static / 'images' / 'leagues' / 'lck.png').write_bytes(b'x')
    app.static_folder = str(static)

    home = client.get('/').get_data(as_text=True)
    assert home.count('game-card-logo') == 1 and '/static/images/leagues/lck.png' in home

    client.post('/api/lpl/guess', json={'year': a['year']})
    r = client.post('/api/lpl/guess', json={'team': a['blue']})
    assert r.json['blueLogo'].endswith(f'{team_slug(a["blue"])}.webp')
    r = client.post('/api/lpl/guess', json={'team': a['red']})
    assert r.json['result']['blueLogo'] and r.json['result']['redLogo'] is None
    assert r.json['result']['vod'] is None  # fixture vods are '0'


def test_draft_order_matching():
    from flaskr.draftorder import match_orders, normalize
    assert normalize("Kai'Sa") == 'kaisa' and normalize('Nunu & Willump') == 'nunu&willump'
    assert normalize('Dr. Mundo') == 'drmundo'
    blue = ['renekton', 'sejuani', 'azir', 'kaisa', 'rakan']  # top, jg, mid, adc, sup
    red = ['aatrox', 'maokai', 'jayce', 'xayah', 'alistar']
    games = [(7, blue, red), (8, ['a', 'b', 'c', 'd', 'e'], ['f', 'g', 'h', 'i', 'j'])]
    row = {'Team1Pick1': 'Sejuani', 'Team1Pick2': "Kai'Sa", 'Team1Pick3': 'Rakan', 'Team1Pick4': 'Azir',
           'Team1Pick5': 'Renekton', 'Team2Pick1': 'Jayce', 'Team2Pick2': 'Xayah', 'Team2Pick3': 'Maokai',
           'Team2Pick4': 'Aatrox', 'Team2Pick5': 'Alistar'}
    assert match_orders(games, [row]) == {7: ([1, 3, 4, 2, 0], [2, 3, 1, 0, 4])}
    #sides swapped on the wiki still match, the right way round
    swapped = {f'Team{3 - t}Pick{n}': row[f'Team{t}Pick{n}'] for t in (1, 2) for n in range(1, 6)}
    assert match_orders(games, [swapped]) == {7: ([1, 3, 4, 2, 0], [2, 3, 1, 0, 4])}
    #a different champion means no match
    assert match_orders(games, [dict(row, Team1Pick5='Gnar')]) == {}


def test_draft_order_on_the_board(client, app):
    from flaskr.answer import todays_id
    with app.test_request_context():
        gid = todays_id('lck')
    html = client.get('/play/lck').get_data(as_text=True)
    assert 'id="view-toggle" class="view-toggle" hidden' in html and 'pick-badge' not in html
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.execute('CREATE TABLE pickOrder(id INT PRIMARY KEY, blue TEXT, red TEXT)')
    conn.execute('INSERT INTO pickOrder VALUES (?, ?, ?)', (gid, '1,3,4,2,0', '2,3,1,0,4'))
    conn.commit()
    conn.close()
    html = client.get('/play/lck').get_data(as_text=True)
    assert 'id="view-toggle" class="view-toggle" hidden' not in html
    #the jungler was blue's first pick and the top laner their last
    assert 'data-role="1" data-pick="1"' in html and 'data-role="0" data-pick="5"' in html
    assert '>B1<' in html and '>R5<' in html


def test_production_settings(app, monkeypatch):
    monkeypatch.delenv('SECRET_KEY', raising=False)
    monkeypatch.delenv('FLASK_DEBUG', raising=False)
    database = app.config['DATABASE']
    with pytest.raises(RuntimeError):
        create_app({'DATABASE': database})
    prod = create_app({'SECRET_KEY': 'long-random-value', 'DATABASE': database, 'FORCE_DAY': DAY})
    c = prod.test_client()
    r = c.post('/api/lck/guess', json={'year': 2013})
    cookie = r.headers['Set-Cookie']
    assert 'Secure' in cookie and 'SameSite=Lax' in cookie and 'HttpOnly' in cookie
    assert c.get('/static/styles.css').headers['Cache-Control'] == 'public, max-age=604800'


def test_splash_fallback_uses_data_dragon_capitals(app, tmp_path):
    from flaskr import answer as views
    app.static_folder = str(tmp_path)  # no local images at all, like the server was
    with app.test_request_context():
        assert views.splash_url('leesin').endswith('/centered/LeeSin_0.jpg')
        assert views.splash_url('ksante').endswith('/centered/KSante_0.jpg')
        assert views.splash_url('wukong').endswith('/centered/MonkeyKing_0.jpg')
        assert views.splash_url('nunu&willump').endswith('/centered/Nunu_0.jpg')
        assert views.splash_url('ahri').endswith('/centered/Ahri_0.jpg')


def test_css_and_js_urls_are_versioned(client):
    html = client.get('/').get_data(as_text=True)
    assert re.search(r'/static/styles\.css\?v=\d{9,}', html) and re.search(r'/static/scripts\.js\?v=\d{9,}', html)


def test_analytics_script_only_when_configured(client, app):
    assert 'goatcounter' not in client.get('/').get_data(as_text=True)
    app.config['GOATCOUNTER_CODE'] = 'loldraftle'
    for url in ('/', '/play/lck'):
        assert 'data-goatcounter="https://loldraftle.goatcounter.com/count"' in client.get(url).get_data(as_text=True)


def test_referrer_policy_header(client):
    assert client.get('/').headers['Referrer-Policy'] == 'strict-origin-when-cross-origin'


def test_old_urls_redirect(client):
    for url in ('/correct', '/incorrect', '/answer.html'):
        assert client.get(url).status_code == 302
