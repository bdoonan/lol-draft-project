import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from flaskr.db import get_db

bp = Blueprint('answer', __name__)

global tries
tries = 0
global id
id = 2
@bp.route('/', methods=('GET','POST'))
def check():
    global tries
    global id
    blue = get_db().execute(
            'SELECT * from blueTeam WHERE gameId = ?', (id,)
        ).fetchone()
    red =  get_db().execute(
            'SELECT * from redTeam WHERE gameId = ?', (id,)
        ).fetchone()
    tourney = get_db().execute(
            'SELECT * from game WHERE id = ?', (id,)
        ).fetchone()
    if request.method == 'POST':
        tournament = request.form['tournament']
        tournament = tournament.lower()
        error = None
        if not tournament:
            error = "Please input a team"
        if error is None:
            if tournament == str(tourney[1]).lower():
                return redirect(url_for("answer.check2"))
            else:
                tries +=1
        if tries >= 1:
            tries = 0
            return render_template('incorrect.html', tourney = tourney, blue = blue, red = red)
        #flash(error)

    return render_template('input.html', tourney = tourney, blue = blue, red = red)
@bp.route('/answer.html', methods=('GET','POST'))
def check2():
    global tries
    global id
    blue = get_db().execute(
            'SELECT * from blueTeam WHERE gameId = ?', (id,)
        ).fetchone()
    red =  get_db().execute(
            'SELECT * from redTeam WHERE gameId = ?', (id,)
        ).fetchone()
    tourney = get_db().execute(
            'SELECT * from game WHERE id = ?', (id,)
        ).fetchone()
    if request.method == 'POST':
        teams = request.form['teams']
        redTeam = str(tourney[3]).lower()
        blueTeam = str(tourney[4]).lower()
        error = None
        if not teams:
            error = "Please input a team"
        if error is None:
            if teams.lower() == blueTeam + " vs " + redTeam or redTeam + " vs " + blueTeam:
                return redirect(url_for("answer.check3"))
            else:
                tries +=1
        if tries >= 5:
            tries = 0
            return render_template('incorrect.html', tourney = tourney, blue = blue, red = red)
        #flash(error)

    return render_template('answer.html', tourney = tourney, blue = blue, red = red)
@bp.route('/answer2.html', methods=('GET','POST'))
def check3():
    global tries
    global id
    blue = get_db().execute(
            'SELECT * from blueTeam WHERE gameId = ?', (id,)
        ).fetchone()
    red =  get_db().execute(
            'SELECT * from redTeam WHERE gameId = ?', (id,)
        ).fetchone()
    tourney = get_db().execute(
            'SELECT * from game WHERE id = ?', (id,)
        ).fetchone()
    if request.method == 'POST':
        game = request.form['game']
        error = None
        if not game:
            error = "Please input a team"
        if error is None:
            if game == tourney[2]:
                return render_template('answer3.html', tourney = tourney, blue = blue, red = red)
            else:
                tries +=1
        if tries >= 5:
            tries = 0
            return render_template('incorrect.html', tourney = tourney, blue = blue, red = red)
        #flash(error)

    return render_template('answer2.html', tourney = tourney, blue = blue, red= red)


