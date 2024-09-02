import random
from flask import (
    Blueprint, flash, redirect, render_template, request, url_for, g
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

global correctyear
global correct_league
global correct_season
global inputyear
global inputleague
global inputseason
global inputteams
checkid = cur.execute(
            'SELECT * from checkid'
            ).fetchone()
#select all and then randomly select a number from 0 to the max id in the table to get a random game and sets the id variable equal to that random number
entries = cur.execute(
            'SELECT * from game'
            ).fetchall()
id = random.randint(0,len(entries)-1)
while id == checkid:
    id = random.randint(0,len(entries)-1)
cur.execute(
    'DELETE FROM checkid'
)
conn.commit()
cur.execute(
    'INSERT INTO checkid(id) VALUES (?)', (id,)
)
conn.commit()
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
#select a random number for our hint button
randomselect = random.randint(1,5)
randomblue = str(randomselect)
randomselect = random.randint(6,10)
randomred = str(randomselect)
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
    
    global correctyear
    global correct_league
    global correct_season
    global inputyear
    global inputleague
    global inputseason
    
    correctyear=""
    correct_league=""
    correct_season=""
    inputyear=""
    inputleague=""
    inputseason =""
    if request.method == 'POST':
        #get the selected value from input.html
        tournament = request.form.get('tournament')

        
            
        
            
        #set error variable equal to none at first for flash
        error = None
        #if user does not select a value output error message
        if not tournament:
            error = "Please input a team"
        else:
        #if no error do the check
                tournament_items =tournament.split(" ")
                inputyear = int(tournament_items[0])
                inputleague = tournament_items[1]
                correct_items = tourney[1].split(" ")
                correctyear = int(correct_items[0])
                correct_league=correct_items[1]
                if (correct_items[-1] != "Playoffs" and tournament[-1] != "Playoffs"):
                    inputseason = tournament_items[-1]
                    correct_season=correct_items[-1]
                else:
                    #season = tournament_items[-2]
                    correct_season=correct_items[-2] + ' ' + correct_items[-1]
                    inputseason = tournament_items[-2] + ' ' + tournament_items[-1]
                    #if it is selected correctly redirect to the rendered page in the next function
                if tournament == str(tourney[1]):
                        return redirect(url_for("answer.check2"))
                    #if it is not correct diplay how many attempts the user has left and add one to the tries variable
                else:
                    tries +=1
                    
                #if the user used all of their attempts redirect to the incorrect page
                if tries >= 5:
                    tries = 0
                    return redirect(url_for("answer.incorrect"))
                #return render_template('incorrect.html', tourney = tourney, blue = blue, red = red)
    #this is the template used for this function and the variables used for the page
    return render_template('input.html', tourney = tourney, blue = blue, red = red, listoftourney = listoftourney, randomblue = randomblue, randomred = randomred, attempts = 5-tries, id=id, tries = tries, inputyear=inputyear, inputleague=inputleague, inputseason=inputseason, correctyear = correctyear, correct_league=correct_league, correct_season=correct_season)
@bp.route('/answer.html', methods=('GET','POST'))
def check2():
    global tries
    global inputteams
    inputteams = ''
    if request.method == 'POST':
        #get the selected input from answer.html
        teams = request.form.get('game')
        error = None
        if not teams:
            error = "Please select game"
        else:

            inputteams = teams.split(' vs ')
            #set the redTeam and blueTeam values to the correct teams in the game
            redTeam = tourney[2]
            blueTeam = tourney[3]
            #if the selected input is correct redirect to the correct answer page
            if teams == blueTeam + " vs " + redTeam:
                return redirect(url_for("answer.correct"))
                #return render_template('correct.html', tourney = tourney, blue = blue, red= red, attempts = tries+1)
            #if it's not correct display attempts left and add to the tries variable
            else:
                error = ("Tries left: " + str(4-tries))
                flash(error)
                tries +=1
            #if the user used all of their attempts redirect to the incorrect page
            if tries >= 5:
                tries = 0
                return redirect(url_for("answer.incorrect"))
            
            #return render_template('incorrect.html', tourney = tourney, blue = blue, red = red)
    #this is the template and variables needed for the page for this function
    return render_template('answer.html', tourney = tourney, blue = blue, red = red, listofteams=listofteams, randomblue = randomblue, randomred = randomred, attempts = 5-tries, inputteams = inputteams, tries = tries)
@bp.route('/correct')
def correct():
    global tries
    return render_template('correct.html', tourney = tourney, blue = blue, red= red, attempts = tries+1, id=id)
@bp.route('/incorrect')
def incorrect():
    return render_template('incorrect.html', tourney = tourney, blue = blue, red = red, id=id)