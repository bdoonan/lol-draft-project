import functools
import random
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

import sqlite3

bp = Blueprint('answer', __name__)
conn = sqlite3.connect("test.db")
cur = conn.cursor()
global tries
tries = 0
global id
id = random.randint(0,77)
team1 = cur.execute(
            'SELECT * from game'
        ).fetchall()
team2 = cur.execute(
            'SELECT * from game'
        ).fetchall()
tourney = cur.execute(
            'SELECT * from game WHERE id = ?', (id,)
        ).fetchone()
blue = cur.execute(
            'SELECT * from blueTeam WHERE id = ?', (id,)
        ).fetchone()
red = cur.execute(
            'SELECT * from redTeam WHERE id = ?', (id,)
        ).fetchone()
@bp.route('/', methods=('GET','POST'))
def check():
    global tries
    global id
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
        if tries >= 5:
            tries = 0
            return render_template('incorrect.html', tourney = tourney, blue = blue, red = red)
        #flash(error)

    return render_template('input.html', tourney = tourney, blue = blue, red = red)
@bp.route('/answer.html', methods=('GET','POST'))
def check2():
    global tries
    global id
    if request.method == 'POST':
        teams = request.form.get('game')
        redTeam = tourney[2]
        blueTeam = tourney[3]

        if teams == blueTeam + " vs " + redTeam or teams == redTeam + " vs " + blueTeam:
            return render_template('answer2.html', tourney = tourney, blue = blue, red= red)
        else:
            tries +=1
        if tries >= 5:
            tries = 0
            return render_template('incorrect.html', tourney = tourney, blue = blue, red = red)

    return render_template('answer.html', tourney = tourney, blue = blue, red = red, team1 = team1, team2 = team2)


