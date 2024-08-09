import functools
import random
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
#we need to access the database to generate the question and get the answer values
import sqlite3
#connect it to the init file
bp = Blueprint('answer', __name__)
#connect to the database created in startdata and populated in scraper
conn = sqlite3.connect("test.db")
cur = conn.cursor()
#set tries variable so that user is given incorrect answer when it equals 5
global tries
tries = 0

#select all and then randomly select a number from 0 to the max id in the table to get a random game and sets the id variable equal to that random number
entries = cur.execute(
            'SELECT * from game'
            ).fetchall()
id = random.randint(0,len(entries))
#get the values for the game table at the random id
tourney = cur.execute(
            'SELECT * from game WHERE id = ?', (id,)
        ).fetchone()
#get the values for the blueTeam table at the random id
blue = cur.execute(
            'SELECT * from blueTeam WHERE id = ?', (id,)
        ).fetchone()
#get the values for the redTeam table at the random id
red = cur.execute(
            'SELECT * from redTeam WHERE id = ?', (id,)
        ).fetchone()
#set the tournament value for the game at the random id so that we can look at games only from that tournament
tourneyid = tourney[1]

#For the select field for the tournament we don't want duplicate values so we make a list of the tournaments and convert it into a set and back into a list so that duplicates are removed
listoftourney = []
for i in range(len(entries)):
    listoftourney.append(entries[i][1]) 
listoftourney = list(set(listoftourney)) 

#This select is so that after the user selects the correct tournament the select field for the game is only games from that tournament and not every game in the database
team1 = cur.execute(
            'SELECT * from game WHERE tournament = ?', (tourneyid,)
            ).fetchall()
listofteams = []
for i in range(len(team1)):
    listofteams.append(team1[i][3]+ " vs " +team1[i][2]) 
listofteams = list(set(listofteams))
#this is the redirect for the tournament entry
@bp.route('/', methods=('GET','POST'))
def check():
    #get the tries global variable set earlier
    global tries
    if request.method == 'POST':
        #get the selected value from input.html
        tournament = request.form['tournament']
        #set error variable equal to none at first for flash
        error = None
        #if user does not select a value output error message
        if not tournament:
            error = "Please input a team"
        #if no error do the check
        if error is None:
            #if it is selected correctly redirect to the rendered page in the next function
            if tournament == str(tourney[1]):
                return redirect(url_for("answer.check2"))
            #if it is not correct diplay how many attempts the user has left and add one to the tries variable
            else:
                error = ("Tries left: "+ str(4-tries))
                flash(error)
                tries +=1
        #if the user used all of their attempts redirect to the incorrect page
        if tries >= 5:
            tries = 0
            return render_template('incorrect.html', tourney = tourney, blue = blue, red = red)
    #this is the template used for this function and the variables used for the page
    return render_template('input.html', tourney = tourney, blue = blue, red = red, listoftourney = listoftourney)
@bp.route('/answer.html', methods=('GET','POST'))
def check2():
    global tries

    if request.method == 'POST':
        #get the selected input from answer.html
        teams = request.form.get('game')
        #set the redTeam and blueTeam values to the correct teams in the game
        redTeam = tourney[2]
        blueTeam = tourney[3]
        #if the selected input is correct redirect to the correct answer page
        if teams == blueTeam + " vs " + redTeam:
            return render_template('answer2.html', tourney = tourney, blue = blue, red= red)
        #if it's not correct display attempts left and add to the tries variable
        else:
            error = ("Tries left: " + str(4-tries))
            flash(error)
            tries +=1
        #if teh user used all of their attempts redirect to the incorrect page
        if tries >= 5:
            tries = 0
            return render_template('incorrect.html', tourney = tourney, blue = blue, red = red)
    #this is the template and variables needed for the page for this function
    return render_template('answer.html', tourney = tourney, blue = blue, red = red, listofteams=listofteams)


