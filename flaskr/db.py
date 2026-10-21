#database access, one connection per request instead of a module level connection shared by every thread
import sqlite3
from flask import current_app, g
from .game import GAMES_BY_SLUG, event_order, league_prefix, tournament_year

ROLES = ('top', 'jg', 'mid', 'adc', 'sup')
#the game data only changes when the scraper runs, so the lists below are cached per database file
_cache = {}


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)


def _cached(key, load):
    key = (current_app.config['DATABASE'], key)
    if key not in _cache:
        _cache[key] = load()
    return _cache[key]


def all_games():
    """(id, tournament, blue, red) for games that have both team rows, so a daily pick never lands on a half scraped game"""
    return _cached('all', lambda: [tuple(r) for r in get_db().execute(
        'SELECT g.id, g.tournament, g.blue, g.red FROM game g '
        'JOIN blueTeam b ON b.id = g.id JOIN redTeam r ON r.id = g.id ORDER BY g.id'
    )])


def game_row(game_id):
    return _cached('by_id', lambda: {r[0]: r for r in all_games()})[game_id]


def _pool_rows(slug):
    leagues = GAMES_BY_SLUG[slug]['leagues']
    return _cached(('pool', slug), lambda: [r for r in all_games() if league_prefix(r[1]) in leagues])


def pool(slug):
    """ids of every match a daily game can pick from"""
    return [r[0] for r in _pool_rows(slug)]


def years(slug):
    return _cached(('years', slug), lambda: sorted({tournament_year(r[1]) for r in _pool_rows(slug)}))


def tournaments(slug, year):
    """the events in this game's pool that year, the options for the event step"""
    return _cached(('tournaments', slug, year), lambda: sorted(
        {r[1] for r in _pool_rows(slug) if tournament_year(r[1]) == year}, key=event_order
    ))


def tournament_teams(tournament):
    """every team that played in a tournament, the options for the team picker"""
    return _cached(('teams', tournament), lambda: sorted(
        {team for r in all_games() if r[1] == tournament for team in r[2:]}
    ))


def _team(table, game_id):
    row = get_db().execute(f'SELECT * FROM {table} WHERE id = ?', (game_id,)).fetchone()
    return {
        'picks': [row[role] for role in ROLES],
        'bans': [row[f'ban{i}'] for i in range(1, 6)],
        'players': [row[f'{role}Player'] for role in ROLES],
    }


def _pick_order(game_id):
    """{'blue': [role indexes in pick order], 'red': [...]}, or None for games without draft order data"""
    try:
        row = get_db().execute('SELECT blue, red FROM pickOrder WHERE id = ?', (game_id,)).fetchone()
    except sqlite3.OperationalError:  # table not created yet, run python -m flaskr.draftorder
        return None
    if not row:
        return None
    return {side: [int(i) for i in row[side].split(',')] for side in ('blue', 'red')}


def get_game(game_id):
    row = get_db().execute('SELECT * FROM game WHERE id = ?', (game_id,)).fetchone()
    return {
        'id': row['id'],
        'tournament': row['tournament'],
        'year': tournament_year(row['tournament']),
        'blue_team': row['blue'],
        'red_team': row['red'],
        'vod': str(row['vod'] or ''),
        'blue': _team('blueTeam', game_id),
        'red': _team('redTeam', game_id),
        'pick_order': _pick_order(game_id),
    }
