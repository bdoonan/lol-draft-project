import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from flaskr.db import get_db

bp = Blueprint('answer', __name__)

global tries
tries = 0
@bp.route('/', methods=('GET','POST'))
def check():
    global tries
    if request.method == 'POST':
        id = 1
        tourney = get_db().execute(
            'SELECT * from game WHERE number = ?', (id,)
        ).fetchone()
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
            return render_template('incorrect.html', tourney = tourney)
        #flash(error)

    return render_template('input.html')
@bp.route('/answer.html', methods=('GET','POST'))
def check2():
    global tries
    if request.method == 'POST':
        teams = request.form['teams']
        error = None
        if not teams:
            error = "Please input a team"
        if error is None:
            if teams == "SKT vs ROX" or teams== "ROX vs SKT":
                return redirect(url_for("answer.check3"))
            else:
                tries +=1
        if tries >= 5:
            tries = 0
            return render_template('incorrect.html')
        #flash(error)

    return render_template('answer.html')
@bp.route('/answer2.html', methods=('GET','POST'))
def check3():
    global tries
    if request.method == 'POST':
        game = request.form['game']
        error = None
        if not game:
            error = "Please input a team"
        if error is None:
            if game == "2":
                return render_template('answer3.html')
            else:
                tries +=1
        if tries >= 5:
            tries = 0
            return render_template('incorrect.html')
        #flash(error)

    return render_template('answer2.html')


