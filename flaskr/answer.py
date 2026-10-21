import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache
from flask import (
    Blueprint, abort, current_app, jsonify, redirect, render_template, request, session, url_for
)
from . import db
from .game import (
    AVOID_SAME, GAMES, GAMES_BY_SLUG, HINT_AFTER, MAX_ATTEMPTS, daily_game_id, hint_index, hints_unlocked,
    event_feedback, event_label, side_feedback, team_slug, tournament_year, vod_start, year_feedback,
    youtube_id
)

bp = Blueprint('answer', __name__)

SIDES = ('blue', 'red')
FINISHED = ('won', 'lost')
#year -> event -> blue side team -> red side team, each a separate guess
#the event step is skipped when the year only has one tournament in the pool (always the case for worlds)
NEXT_STAGE = {'year': 'event', 'event': 'blue', 'blue': 'red', 'red': 'won'}
#short labels for the role tag on each pick, in the db's column order
ROLE_NAMES = ('TOP', 'JNG', 'MID', 'BOT', 'SUP')
#db champion names that don't match the image file names
SPLASH_ALIASES = {'wukong': 'MonkeyKing', 'nunu&willump': 'Nunu', 'renataglasc': 'Renata'}
#data dragon ids are case sensitive, these are the ones that aren't just a capitalized first letter
#(checked against data dragon 16.21.1, new champions so far have all been single words)
#FiddleSticks is his old id, the centered splash images still use it
DDRAGON_IDS = {i.lower(): i for i in (
    'AurelionSol', 'DrMundo', 'FiddleSticks', 'JarvanIV', 'KSante', 'KogMaw', 'LeeSin', 'MasterYi',
    'MissFortune', 'MonkeyKing', 'RekSai', 'TahmKench', 'TwistedFate', 'XinZhao',
)}
ICON_ALIASES = {'anivia': 'anivi', 'nunu&willump': 'nunu'}


#---------- images ----------
def _scan(folder):
    """lowercase file stem -> real file name, so lookups work on case sensitive hosts (linux) too"""
    if not os.path.isdir(folder):
        return {}
    return {name.rsplit('.', 1)[0].lower(): name for name in os.listdir(folder)}


_scan_cached = lru_cache(maxsize=None)(_scan)


def _files(folder):
    #rescan every time in debug so newly added logos show up without a restart
    return _scan(folder) if current_app.debug else _scan_cached(folder)


def _static_image(subfolder, stem):
    """url of static/images/<subfolder>/<stem>.<any extension>, or None if there is no such file"""
    name = _files(os.path.join(current_app.static_folder, 'images', subfolder)).get(stem.lower())
    return url_for('static', filename=f'images/{subfolder}/{name}') if name else None


def team_logo_url(team):
    """downloaded by python -m flaskr.logos"""
    return _static_image('teams', team_slug(team))


def league_logo_url(slug):
    """added by hand to static/images/leagues/"""
    return _static_image('leagues', slug)


def splash_url(champ):
    key = SPLASH_ALIASES.get(champ, champ)
    name = _files(os.path.join(current_app.static_folder, 'images', 'centered')).get(f'{key}_0'.lower())
    if name:
        return url_for('static', filename=f'images/centered/{name}')
    #champions released after the images were downloaded, or the images missing on the server
    ddragon_id = DDRAGON_IDS.get(key.lower(), key[:1].upper() + key[1:])
    return f'https://ddragon.leagueoflegends.com/cdn/img/champion/centered/{ddragon_id}_0.jpg'


def icon_url(champ):
    key = ICON_ALIASES.get(champ, champ)
    name = _files(os.path.join(current_app.static_folder, 'images')).get(key.lower())
    if name:
        return url_for('static', filename=f'images/{name}')
    return f'https://cdn.communitydragon.org/latest/champion/{key}/square'


#---------- vods ----------
#video id -> still on youtube, checked at most once per video while the server runs
_vod_alive = {}


def _oembed_status(video_id):
    """youtube's oembed answers 404/401 for deleted, private or non-embeddable videos"""
    url = 'https://www.youtube.com/oembed?format=json&url=' + urllib.parse.quote(
        f'https://www.youtube.com/watch?v={video_id}', safe='')
    try:
        with urllib.request.urlopen(url, timeout=3) as res:
            return res.status
    except urllib.error.HTTPError as e:
        return e.code
    except (urllib.error.URLError, TimeoutError, OSError):
        return None


def vod_info(url):
    """what the result screen needs to show a vod, or None if it isn't on youtube or is gone"""
    video_id = youtube_id(url)
    if not video_id:
        return None
    if video_id not in _vod_alive:
        status = _oembed_status(video_id)
        if status is None:
            return _vod_dict(video_id, url)  # youtube unreachable, show it and don't remember
        _vod_alive[video_id] = status not in (401, 403, 404)
    return _vod_dict(video_id, url) if _vod_alive[video_id] else None


def _vod_dict(video_id, url):
    start = vod_start(url)
    return {
        'thumb': f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg',
        'embed': f'https://www.youtube-nocookie.com/embed/{video_id}?autoplay=1&start={start}',
        'watch': f'https://www.youtube.com/watch?v={video_id}&t={start}s',
        'start': start,
    }


@bp.app_template_global()
def asset_url(filename):
    """static url with ?v=<last modified time>, so the week long browser cache is skipped as soon as the file changes"""
    path = os.path.join(current_app.static_folder, filename)
    version = int(os.path.getmtime(path)) if os.path.exists(path) else 0
    return url_for('static', filename=filename, v=version)


@bp.after_app_request
def referrer_policy(response):
    #youtube's player needs to know which site embeds it, a missing referrer shows "video unavailable"
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    return response


#---------- daily picks ----------
def today():
    forced = current_app.config.get('FORCE_DAY')
    return date.fromisoformat(forced) if forced else datetime.now(timezone.utc).date()


def next_reset():
    return datetime.combine(today() + timedelta(days=1), time(), timezone.utc).isoformat()


def todays_id(slug):
    day = today()
    other = AVOID_SAME.get(slug)
    avoid = daily_game_id(db.pool(other), day, other) if other else None
    return daily_game_id(db.pool(slug), day, slug, avoid)


def answer_summary(slug):
    """just what's needed to score guesses, without loading the whole draft"""
    _, tournament, blue, red = db.game_row(todays_id(slug))
    return {'year': tournament_year(tournament), 'tournament': tournament, 'blue_team': blue, 'red_team': red}


def get_slug_or_404(slug):
    if slug not in GAMES_BY_SLUG:
        abort(404)
    return GAMES_BY_SLUG[slug]


#---------- player state ----------
#session['games'] = {'day': 'YYYY-MM-DD', '<slug>': {'stage', 'guesses', 'hints'}}
#guesses are stored raw (a year int, or ['event', tournament] / ['blue', team] / ['red', team])
#and scored when sent, which keeps the cookie under 4KB
def load_games():
    session.pop('game', None)  # the single game state from the first version
    day = today().isoformat()
    games = session.get('games')
    if not games or games.get('day') != day:
        games = {'day': day}
    #restart any game saved by the version that guessed both teams at once
    for slug, state in list(games.items()):
        if slug != 'day' and (state['stage'] == 'teams' or any(
                isinstance(g, list) and g[0] not in ('event',) + SIDES for g in state['guesses'])):
            del games[slug]
    return games


def new_state():
    return {'stage': 'year', 'guesses': [], 'hints': []}


def is_correct(guess, answer):
    if isinstance(guess, int):
        return guess == answer['year']
    kind, value = guess
    if kind == 'event':
        return value == answer['tournament']
    return value == answer[f'{kind}_team']


def next_stage(slug, stage, answer):
    stage = NEXT_STAGE[stage]
    if stage == 'event' and len(db.tournaments(slug, answer['year'])) < 2:
        stage = 'blue'
    return stage


def misses(state, answer):
    return sum(not is_correct(g, answer) for g in state['guesses'])


def hints_available(state, answer):
    return max(0, hints_unlocked(misses(state, answer)) - len(state['hints']))


def public_state(slug, state, game):
    """everything the page is allowed to know, the answer is only included once the game is over"""
    def scored(guess):
        if isinstance(guess, int):
            return {'kind': 'year', 'cells': year_feedback(guess, game['year'])}
        kind, value = guess
        if kind == 'event':
            return {'kind': kind, 'cells': event_feedback(value, game['tournament'])}
        return {'kind': kind, 'cells': side_feedback(value, kind, game['blue_team'], game['red_team'])}

    out = {
        'slug': slug,
        'name': GAMES_BY_SLUG[slug]['name'],
        'day': today().isoformat(),
        'stage': state['stage'],
        'guesses': [scored(g) for g in state['guesses']],
        'maxAttempts': MAX_ATTEMPTS,
        'attemptsLeft': MAX_ATTEMPTS - misses(state, game),
        'hints': {side: {'index': hint_index(today(), slug, side),
                         'name': game[side]['players'][hint_index(today(), slug, side)]}
                  for side in state['hints']},
        'hintsAvailable': hints_available(state, game),
        'hintAfter': HINT_AFTER,
        'nextReset': next_reset(),
    }
    if state['stage'] != 'year':
        out['year'] = game['year']
        out['events'] = [{'value': t, 'text': event_label(t)} for t in db.tournaments(slug, game['year'])]
    if state['stage'] not in ('year', 'event'):
        out['event'] = event_label(game['tournament'])
        out['teams'] = db.tournament_teams(game['tournament'])
    if state['stage'] not in ('year', 'event', 'blue'):
        out['blueTeam'] = game['blue_team']
        out['blueLogo'] = team_logo_url(game['blue_team'])
    if state['stage'] in FINISHED:
        out['result'] = {
            'tournament': game['tournament'],
            'blueTeam': game['blue_team'],
            'redTeam': game['red_team'],
            'blueLogo': team_logo_url(game['blue_team']),
            'redLogo': team_logo_url(game['red_team']),
            'players': {side: game[side]['players'] for side in SIDES},
            'attempts': misses(state, game) + 1,
            'vod': vod_info(game['vod']),
        }
    return out


def draft(game):
    """the board: picks in role order, each with its role and (when known) its place in the draft"""
    order = game['pick_order']
    out = {'has_order': bool(order)}
    for side in SIDES:
        place = {role: n for n, role in enumerate(order[side], 1)} if order else {}
        out[side] = {
            'picks': [{'url': splash_url(champ), 'role': i, 'role_name': ROLE_NAMES[i], 'pick': place.get(i)}
                      for i, champ in enumerate(game[side]['picks'])],
            'bans': [icon_url(c) for c in game[side]['bans']],
        }
    return out


#---------- pages ----------
@bp.route('/')
def home():
    games = load_games()
    cards = []
    for g in GAMES:
        state = games.get(g['slug']) or new_state()
        answer = answer_summary(g['slug'])
        cards.append({**g, 'stage': state['stage'], 'started': bool(state['guesses']),
                      'logo': league_logo_url(g['slug']),
                      'attemptsLeft': MAX_ATTEMPTS - misses(state, answer),
                      'attempts': misses(state, answer) + 1})
    return render_template('home.html', cards=cards, next_reset=next_reset())


@bp.route('/play/<slug>')
def play(slug):
    info = get_slug_or_404(slug)
    game = db.get_game(todays_id(slug))
    state = load_games().get(slug) or new_state()
    return render_template('play.html', game_name=info['name'], draft=draft(game), years=db.years(slug),
                           state=public_state(slug, state, game))


#---------- api ----------
@bp.post('/api/<slug>/guess')
def guess(slug):
    get_slug_or_404(slug)
    game = db.get_game(todays_id(slug))
    games = load_games()
    state = games.setdefault(slug, new_state())
    if state['stage'] in FINISHED:
        return jsonify(error="This game is already finished for today."), 409
    data = request.get_json(silent=True) or {}

    if state['stage'] == 'year':
        try:
            value = int(data.get('year'))
        except (TypeError, ValueError):
            value = None
        if value not in db.years(slug):
            return jsonify(error='Pick a year from the list.'), 400
    elif state['stage'] == 'event':
        event = data.get('event')
        if event not in db.tournaments(slug, game['year']):
            return jsonify(error='Pick an event from the list.'), 400
        value = ['event', event]
    else:
        side, team = state['stage'], data.get('team')
        if team not in db.tournament_teams(game['tournament']):
            return jsonify(error='Pick a team from the list.'), 400
        if side == 'red' and team == game['blue_team']:
            return jsonify(error="That's the blue side team, pick the red side team."), 400
        value = [side, team]

    if value in state['guesses']:
        return jsonify(error='You already guessed that.'), 400

    state['guesses'].append(value)
    if is_correct(value, game):
        state['stage'] = next_stage(slug, state['stage'], game)
    elif misses(state, game) >= MAX_ATTEMPTS:
        state['stage'] = 'lost'
    session['games'] = games
    return jsonify(public_state(slug, state, game))


@bp.post('/api/<slug>/hint')
def hint(slug):
    get_slug_or_404(slug)
    side = (request.get_json(silent=True) or {}).get('side')
    if side not in SIDES:
        abort(400)
    game = db.get_game(todays_id(slug))
    games = load_games()
    state = games.setdefault(slug, new_state())
    if side not in state['hints']:
        if state['stage'] in FINISHED or hints_available(state, game) == 0:
            return jsonify(error=f'Hints unlock after {HINT_AFTER} wrong guesses, one per wrong guess.'), 403
        state['hints'].append(side)
        session['games'] = games
    return jsonify(public_state(slug, state, game))


#---------- debug / old urls ----------
@bp.route('/debug/reset')
def debug_reset():
    """only with flask run --debug: ?game=<slug> replays one game (all games without it), stats=1 also wipes its stats"""
    if not current_app.debug:
        abort(404)
    slug = request.args.get('game')
    games = load_games()
    if slug:
        get_slug_or_404(slug)
        games.pop(slug, None)
    else:
        games = {'day': games['day']}
    session['games'] = games
    script = ''
    if request.args.get('stats'):
        script = (f"var s=JSON.parse(localStorage.getItem('lolStats')||'{{}}');delete s[{json.dumps(slug)}];"
                  "localStorage.setItem('lolStats',JSON.stringify(s));" if slug
                  else "localStorage.removeItem('lolStats');")
    target = url_for('answer.play', slug=slug) if slug else url_for('answer.home')
    return f"<script>{script}location.replace('{target}');</script>"


#old multi page urls, kept so bookmarks still land on the site
@bp.route('/answer.html')
@bp.route('/correct')
@bp.route('/incorrect')
def old_pages():
    return redirect(url_for('answer.home'))
