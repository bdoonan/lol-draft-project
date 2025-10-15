from bs4 import BeautifulSoup
import requests
import sqlite3
import os
import urllib.request 
#Only run this file once to make the databases

def makemaps(url, playermap, picksandbans, squads, vods):   
    response = requests.get(url)
    data = response.text
    #path to save team images to
    image_path = "flaskr/static/images/teams/"
    # Parse the HTML content
    soup = BeautifulSoup(data, 'html.parser')
    index = -1
    fullgame = soup.find_all('tr', class_ = ["mhgame-blue multirow-highlighter", "mhgame-red multirow-highlighter" ])
    for full in fullgame:
        vodFull = full.find_all('a', class_= ["external text"])
        if len(vodFull)>0:
            vods.append(vodFull[0]["href"])
        else:
            vods.append(0)
        players =full.find_all('a', class_ = ["catlink-players pWAG", "catlink-players pWAN", "mw-redirect", "catlink-players pWAG pWAN","catlink-players pWAG pWAN to_hasTooltip","mw-redirect to_hasTooltip","catlink-players pWAN to_hasTooltip","catlink-players pWAG to_hasTooltip"])
        for i in range(len(players)):
            if i%5==0:
                index+=1
                playermap[index] = [players[i]['title']]
            else:
                playermap[index].append(players[i]['title'])
    # Extract the pick and bans and input into a hashmap
    # Every four indexes are a new game so the index for blue_bans%4 == 0, red_bans%4 == 1, blue_picks%4 == 2, red_picks%4 == 3
    #Use this to input in database later
    champdata = soup.find_all('td')
    #picksandbans={}
    index = 0
    index2=0
    for champ in champdata:
        champs =(champ.find_all('span', class_ = "sprite champion-sprite"))
        if len(champs)>=1:
            for i in range(len(champs)):
                value = champs[i]['title']
                value = str(value)
                value = value.replace(" ", "")
                value = value.replace(".","")
                value = value.replace("'","")
                value = value.lower()
                if i ==0:
                    picksandbans[index] = [value]
                else:
                    picksandbans[index].append(value)
            index+=1
    #We now do this for the teams that play
    teams = soup.find_all('td', class_= "mhgame-result")
    #squads = {}
    index = 0
    index2 = 0
    for i in teams:
        images = i.find_all('img')
        team = (i.find_all('a', class_="to_hasTooltip"))
        if not team:
            team = (i.find_all('a'))
        #make sure the component is not empty as there are some in the html file
        if len(team)>0:
            #download team images if the team image file does not exist
            # if len(images)>0:
            #    if not os.path.isfile(image_path+team[0]['title']+'.png'):
            #        if 'https' in images[0]['src']:
            #            urllib.request.urlretrieve(images[0]['src'],image_path+team[0]['title']+'.png')
                       
            #        else:
            #            urllib.request.urlretrieve(images[0]['data-src'],image_path+team[0]['title']+'.png')
                       
                    
                   
            #get rid of the patch objects
            if not "Patch" in team[0]['title']:
                value = team[0]['title']
                #site displays the two teams and the winning team
                #we don't care about winning team, which is every third object so we do not put this in our hashmap
                #we also increment by 1 only after the second team is inputed so we get two teams per index for every game
                if index2%3 !=2:
                    if index2%3 == 0:
                        squads[index]=[value]
                    else:
                        squads[index].append(value)
                        index+=1
                index2+=1

#Now we want to input into our database
#Since we have to update the values at different indexes for the champion picks we want to initliaze all the values first
counter = 0
counter2 = 0
def makedb(tournament, playermap, picksandbans, squads, vods, index, index2):
    top = ""
    jg = ""
    mid = ""
    adc = ""
    sup = ""
    ban1 = ""
    ban2 = ""
    ban3 = ""
    ban4 = ""
    ban5 = ""
    topplayer = ""
    jgplayer = ""
    midplayer = ""
    adcplayer = ""
    supplayer = ""
    #connect to database
    conn = sqlite3.connect("test.db")
    cur = conn.cursor()
    #loop through the teams hashmap and input into the game database the two teams at each index
    playercounter = index
    game_values = []
    blue_values = []
    red_values = []
    for i in range(len(squads)):
        #gameid = i
        tournament = tournament
        #print(tournament)
        red = squads[i][1]
        blue = squads[i][0]
        vod = vods[i]
        game_values.append((index, tournament, red, blue, vod))
        blue_values.append((index, top, jg, mid, adc, sup, ban1, ban2, ban3, ban4, ban5, topplayer, jgplayer, midplayer, adcplayer, supplayer))
        red_values.append((index, top, jg, mid, adc, sup, ban1, ban2, ban3, ban4, ban5, topplayer, jgplayer, midplayer, adcplayer, supplayer))
        # cur.execute('''
        #             INSERT INTO game(id, tournament, red, blue, vod) 
        #             VALUES(?,?,?,?,?) ''', (index, tournament, red, blue, vod))
        # conn.commit()
        # #we also put the id values for the blue and red team tables that will be updated when we go through that hashmap
        # cur.execute('''
        #             INSERT INTO blueTeam(id, top, jg, mid, adc, sup, ban1, ban2, ban3, ban4, ban5, topPlayer, jgPlayer, midPlayer, adcPlayer, supPlayer)
        #             VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ''', (index, top, jg, mid, adc, sup, ban1, ban2, ban3, ban4, ban5, topplayer, jgplayer, midplayer, adcplayer, supplayer))
        # conn.commit()
        # cur.execute('''
        #             INSERT INTO redTeam(id, top, jg, mid, adc, sup, ban1, ban2, ban3, ban4, ban5, topPlayer, jgPlayer, midPlayer, adcPlayer, supPlayer)
        #             VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ''', (index, top, jg, mid, adc, sup, ban1, ban2, ban3, ban4, ban5, topplayer, jgplayer, midplayer, adcplayer, supplayer))
        # conn.commit()
        index+=1
    cur.executemany("INSERT INTO game(id, tournament, red, blue, vod) VALUES (?, ?, ?, ?, ?)", game_values)
    conn.commit()
    cur.executemany('''
                     INSERT INTO blueTeam(id, top, jg, mid, adc, sup, ban1, ban2, ban3, ban4, ban5, topPlayer, jgPlayer, midPlayer, adcPlayer, supPlayer)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ''', blue_values)
    conn.commit()
    cur.executemany('''
                     INSERT INTO redTeam(id, top, jg, mid, adc, sup, ban1, ban2, ban3, ban4, ban5, topPlayer, jgPlayer, midPlayer, adcPlayer, supPlayer)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ''', red_values)
    conn.commit()
    
    
    #now we loop through the champions using the mod rule discussed earlier
    blue_players =[]
    red_players = []
    for i in range(len(playermap)):
        #print (playermap[i])
        if i%2==0:
            topplayer = playermap[i][0]
            jgplayer = playermap[i][1]
            midplayer = playermap[i][2]
            adcplayer = playermap[i][3]
            supplayer = playermap[i][4]

            blue_players.append((topplayer, jgplayer, midplayer, adcplayer, supplayer, playercounter))
            # cur.execute('''
            #         UPDATE blueTeam SET topPlayer= ?, jgPlayer = ?, midPlayer = ?, adcPlayer = ?, supPlayer = ? WHERE id = ?
            #         ''', (topplayer, jgplayer, midplayer, adcplayer, supplayer, playercounter))
            # conn.commit()
        else:
            topplayer = playermap[i][0]
            jgplayer = playermap[i][1]
            midplayer = playermap[i][2]
            adcplayer = playermap[i][3]
            supplayer = playermap[i][4]

            red_players.append((topplayer, jgplayer, midplayer, adcplayer, supplayer, playercounter))
            # cur.execute('''
            #         UPDATE redTeam SET topPlayer= ?, jgPlayer = ?, midPlayer = ?, adcPlayer = ?, supPlayer = ? WHERE id = ?
            #         ''', (topplayer, jgplayer, midplayer, adcplayer, supplayer, playercounter))
            # conn.commit()
            playercounter+=1
    cur.executemany('''
                    UPDATE blueTeam SET topPlayer= ?, jgPlayer = ?, midPlayer = ?, adcPlayer = ?, supPlayer = ? WHERE id = ?
                    ''', blue_players)
    conn.commit()
    cur.executemany('''
                    UPDATE redTeam SET topPlayer= ?, jgPlayer = ?, midPlayer = ?, adcPlayer = ?, supPlayer = ? WHERE id = ?
                    ''', red_players)
    conn.commit()

    blue_bans = []
    red_bans = []
    blue_picks = []
    red_picks =[]
    for i in range(len(picksandbans)):
        
        gameid = index2
        if i%4 == 0:
            #these are the bluebans
            ban1 = picksandbans[i][0]
            ban2 = picksandbans[i][1]
            ban3 = picksandbans[i][2]
            if len(picksandbans[i]) == 3:
                ban4 = "none"
                ban5 = "none"
            else:
                ban4 = picksandbans[i][3]
                ban5 = picksandbans[i][4]
            # cur.execute('''
            #         UPDATE blueTeam SET ban1 = ?, ban2 = ?, ban3 = ?, ban4 = ?, ban5 = ? WHERE id = ?
            #         ''', (ban1, ban2, ban3, ban4, ban5, gameid))
            # conn.commit()
            blue_bans.append((ban1, ban2, ban3, ban4, ban5, gameid))
        elif i%4 == 1:
            #these are the red bans
            ban1 = picksandbans[i][0]
            ban2 = picksandbans[i][1]
            ban3 = picksandbans[i][2]
            if len(picksandbans[i]) == 3:
                ban4 = "none"
                ban5 = "none"
            else:
                ban4 = picksandbans[i][3]
                ban5 = picksandbans[i][4]
            # cur.execute('''
            #         UPDATE redTeam SET ban1 = ?, ban2 = ?, ban3 = ?, ban4 = ?, ban5 = ? WHERE id = ?
            #         ''', (ban1, ban2, ban3, ban4, ban5, gameid))
            # conn.commit()
            red_bans.append((ban1, ban2, ban3, ban4, ban5, gameid))
        elif i%4 == 2:
            #these are the blue picks
            top = picksandbans[i][0]
            jg = picksandbans[i][1]
            mid = picksandbans[i][2]
            adc = picksandbans[i][3]
            sup = picksandbans[i][4]
            # cur.execute('''
            #         UPDATE blueTeam SET top = ?, jg = ?, mid = ?, adc = ?, sup = ? WHERE id = ?
            #         ''', (top, jg, mid, adc, sup, gameid))
            # conn.commit()
            blue_picks.append((top, jg, mid, adc, sup, gameid))
        else:
            #these are the red picks
            top = picksandbans[i][0]
            jg = picksandbans[i][1]
            mid = picksandbans[i][2]
            adc = picksandbans[i][3]
            sup = picksandbans[i][4]
            # cur.execute('''
            #         UPDATE redTeam SET top = ?, jg = ?, mid = ?, adc = ?, sup = ? WHERE id = ?
            #         ''', (top, jg, mid, adc, sup, gameid))
            # conn.commit()
            red_picks.append((top, jg, mid, adc, sup, gameid))
            index2 +=1

    cur.executemany('''
                    UPDATE blueTeam SET ban1 = ?, ban2 = ?, ban3 = ?, ban4 = ?, ban5 = ? WHERE id = ?
                    ''', blue_bans)
    conn.commit()
    cur.executemany('''
                    UPDATE redTeam SET ban1 = ?, ban2 = ?, ban3 = ?, ban4 = ?, ban5 = ? WHERE id = ?
                    ''', red_bans)
    conn.commit()
    cur.executemany('''
                    UPDATE blueTeam SET top = ?, jg = ?, mid = ?, adc = ?, sup = ? WHERE id = ?
                    ''', blue_picks)
    conn.commit()
    cur.executemany('''
                    UPDATE redTeam SET top = ?, jg = ?, mid = ?, adc = ?, sup = ? WHERE id = ?
                    ''', red_picks)
    conn.commit()
    conn.close()
#function used to populate the database with user manually inputting url and tournament name and then incrementing the counter to make sure game id is unique
def popdata(url, tournament, counter, counter2):
    url = url
    picksandbans = {}
    squads = {}
    playermap ={}
    vods = []
    tournament = tournament
    makemaps(url, playermap, picksandbans, squads, vods)
    makedb(tournament, playermap, picksandbans, squads, vods, counter, counter2)
    counter += len(squads)
    counter2 = counter
    return counter, counter2


# Initial database population function (now replaced by add_matches_for_year)
def start_database():
    """
    Initial database population - use add_matches_for_year() instead for better control
    """
    print("Use add_matches_for_year(start_year, end_year) instead of this function")
    print("Example: add_matches_for_year(2013, 2025) to populate all years")


# url = 'https://lol.fandom.com/wiki/2017_Season_World_Championship/Main_Event/Match_History'
# picksandbans = {}
# squads = {}
# playermap ={}
# vods = []
# tournament = '2017 MSI'
# makemaps(url, playermap, picksandbans, squads, vods)
# # makedb(tournament, playermap, picksandbans, squads, counter, counter2)
# print(vods)
print("Databases populated")

def add_matches_for_year(start_year, end_year):
    """
    Add matches for a specific range of years without re-scraping everything.
    Checks for existing matches and only adds new ones.
    """
    conn = sqlite3.connect("test.db")
    cur = conn.cursor()
    
    # Get the current max ID to continue from
    max_id_result = cur.execute("SELECT MAX(id) FROM game").fetchone()
    current_max_id = max_id_result[0] if max_id_result[0] is not None else 0
    counter = current_max_id + 1
    counter2 = counter
    
    # Get existing tournaments to avoid duplicates
    existing_tournaments = set()
    existing_tournaments_result = cur.execute("SELECT DISTINCT tournament FROM game").fetchall()
    for row in existing_tournaments_result:
        existing_tournaments.add(row[0])
    
    print(f"Starting from ID: {counter}")
    print(f"Existing tournaments: {len(existing_tournaments)}")
    
    # Build tournaments for the specified year range
    tournaments_to_add = {}
    tournament_index = 0
    
    for i in range(start_year, end_year + 1):
        # Winter playoffs
        if i > 2024:
            tournament_name = f"{i} LTA Winter Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LTA/{i}_Season/Split_1_Playoffs/Match_History", tournament_name]
                tournament_index += 1
            
            tournament_name = f"{i} LCK Cup Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LCK/{i}_Season/Cup/Match_History", tournament_name]
                tournament_index += 1
            
            tournament_name = f"{i} LPL Winter Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LPL/{i}_Season/Split_1_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        
        # LEC Winter Playoffs
        if i > 2022:
            tournament_name = f"{i} LEC Winter Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LEC/{i}_Season/Winter_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        
        # OGN Winter Playoffs (special cases)
        if i == 2013:
            tournament_name = f"{i} OGN Winter Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = ["https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryGame?MHG%5Btournament%5D=Champions+2013+Winter&MHG%5Bstartdate%5D=2012-12-25&MHG%5Bpreload%5D=Tournament&MHG%5Bspl%5D=yes&_run=", tournament_name]
                tournament_index += 1
        if i == 2014:
            tournament_name = f"{i} OGN Winter Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = ["https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryGame?MHG%5Btournament%5D=Champions+2014+Winter&MHG%5Bstartdate%5D=2013-12-25&MHG%5Bpreload%5D=Tournament&MHG%5Bspl%5D=yes&_run=", tournament_name]
                tournament_index += 1
        
        # First Stand
        if i > 2024:
            tournament_name = f"{i} First Stand"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/{i}_First_Stand/Match_History", tournament_name]
                tournament_index += 1
        
        # Spring playoffs
        # LCS Spring
        if i == 2013:
            tournament_name = f"{i} LCS Spring Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/NA_LCS/Season_{i%10}/Spring_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        elif i < 2019:
            tournament_name = f"{i} LCS Spring Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/NA_LCS/{i}_Season/Spring_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        elif i == 2021:
            tournament_name = f"{i} LCS Spring Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LCS/{i}_Season/Mid-Season_Showdown/Match_History", tournament_name]
                tournament_index += 1
        elif i < 2025:
            tournament_name = f"{i} LCS Spring Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LCS/{i}_Season/Spring_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        else:
            tournament_name = f"{i} LTA_North Spring Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LTA_North/{i}_Season/Split_2_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        
        # LEC Spring
        if i == 2013:
            tournament_name = f"{i} LEC Spring Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/EU_LCS/Season_{i%10}/Spring_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        elif i < 2019:
            tournament_name = f"{i} LEC Spring Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/EU_LCS/{i}_Season/Spring_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        else:
            tournament_name = f"{i} LEC Spring Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LEC/{i}_Season/Spring_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        
        # LCK/OGN Spring
        if i == 2013:
            tournament_name = f"{i} OGN Spring Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = ["https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryGame?MHG%5Btournament%5D=Champions+2013+Spring&MHG%5Bstartdate%5D=2013-05-08&MHG%5Bpreload%5D=Tournament&MHG%5Bspl%5D=yes&_run=", tournament_name]
                tournament_index += 1
        elif i == 2014:
            tournament_name = f"{i} OGN Spring Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = ["https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryGame?MHG%5Btournament%5D=Champions+2014+Spring&MHG%5Bstartdate%5D=2014-04-16&MHG%5Bpreload%5D=Tournament&MHG%5Bspl%5D=yes&_run=", tournament_name]
                tournament_index += 1
        elif i < 2016:
            tournament_name = f"{i} LCK Spring Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/Champions/{i}_Season/Spring_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        elif i < 2025:
            tournament_name = f"{i} LCK Spring Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LCK/{i}_Season/Spring_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        else:
            tournament_name = f"{i} LCK Road_to MSI"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LCK/{i}_Season/Road_to_MSI/Match_History", tournament_name]
                tournament_index += 1
        
        # LPL Spring
        if i < 2025:
            tournament_name = f"{i} LPL Spring Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LPL/{i}_Season/Spring_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        else:
            tournament_name = f"{i} LPL Spring Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LPL/{i}_Season/Split_2_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        
        # MSI
        if 2016 < i < 2020:
            tournament_name = f"{i} MSI"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/{i}_Mid-Season_Invitational/Main_Event/Match_History", tournament_name]
                tournament_index += 1
        else:
            tournament_name = f"{i} MSI"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/{i}_Mid-Season_Invitational/Match_History", tournament_name]
                tournament_index += 1
        
        # Summer playoffs
        # LCS Summer
        if i == 2013:
            tournament_name = f"{i} LCS Summer Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/NA_LCS/Season_{i%10}/Summer_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        elif i < 2019:
            tournament_name = f"{i} LCS Summer Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/NA_LCS/{i}_Season/Summer_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        elif i < 2021:
            tournament_name = f"{i} LCS Summer Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LCS/{i}_Season/Summer_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        else:
            tournament_name = f"{i} LCS Summer Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LCS/{i}_Season/Championship/Match_History", tournament_name]
                tournament_index += 1
        
        # LEC Summer
        if i == 2013:
            tournament_name = f"{i} LEC Summer Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/EU_LCS/Season_{i%10}/Summer_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        elif i < 2019:
            tournament_name = f"{i} LEC Summer Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/EU_LCS/{i}_Season/Summer_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        else:
            tournament_name = f"{i} LEC Summer Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LEC/{i}_Season/Summer_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        
        # LCK/OGN Summer
        if i == 2013:
            tournament_name = f"{i} OGN Summer Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = ["https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryGame?MHG%5Btournament%5D=Champions+2013+Summer&MHG%5Bstartdate%5D=2013-08-07&MHG%5Bpreload%5D=Tournament&MHG%5Bspl%5D=yes&_run=", tournament_name]
                tournament_index += 1
        elif i == 2014:
            tournament_name = f"{i} OGN Summer Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = ["https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryGame?MHG%5Btournament%5D=Champions+2014+Summer&MHG%5Bstartdate%5D=2014-07-16&MHG%5Bpreload%5D=Tournament&MHG%5Bspl%5D=yes&_run=", tournament_name]
                tournament_index += 1
        elif i < 2016:
            tournament_name = f"{i} LCK Summer Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/Champions/{i}_Season/Summer_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        elif i < 2025:
            tournament_name = f"{i} LCK Summer Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LCK/{i}_Season/Summer_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        else:
            tournament_name = f"{i} LCK Summer Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LCK/{i}_Season/Season_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        
        # LPL Summer
        if i < 2025:
            tournament_name = f"{i} LPL Summer Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LPL/{i}_Season/Summer_Playoffs/Match_History", tournament_name]
                tournament_index += 1
        else:
            tournament_name = f"{i} LPL Summer Playoffs"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LPL/{i}_Season/Grand_Finals/Match_History", tournament_name]
                tournament_index += 1
        
        # LEC Season Finals
        tournament_name = f"{i} LEC Season Finals"
        if tournament_name not in existing_tournaments:
            tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LEC/{i}_Season/Season_Finals/Match_History", tournament_name]
            tournament_index += 1
        
        # Regional Finals
        # LCS Regional
        if i < 2019:
            tournament_name = f"{i} LCS Regional Finals"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/NA_LCS/{i}_Season/Regional_Finals/Match_History", tournament_name]
                tournament_index += 1
        else:
            tournament_name = f"{i} LCS Regional Finals"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LCS/{i}_Season/Regional_Finals/Match_History", tournament_name]
                tournament_index += 1
        
        # LEC Regional
        if i < 2019:
            tournament_name = f"{i} LEC Regional Finals"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/EU_LCS/{i}_Season/Regional_Finals/Match_History", tournament_name]
                tournament_index += 1
        else:
            tournament_name = f"{i} LEC Regional Finals"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LEC/{i}_Season/Regional_Finals/Match_History", tournament_name]
                tournament_index += 1
        
        # LPL Regional
        tournament_name = f"{i} LPL Regional Finals"
        if tournament_name not in existing_tournaments:
            tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LPL/{i}_Season/Regional_Finals/Match_History", tournament_name]
            tournament_index += 1
        
        # LCK/OGN Regional
        if i == 2013:
            tournament_name = f"{i} OGN Regional Finals"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/Season_{i%10}_Korea_Regional_Finals/Match_History", tournament_name]
                tournament_index += 1
        elif i < 2015:
            tournament_name = f"{i} OGN Regional Finals"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/{i}_Season_Korea_Regional_Finals/Match_History", tournament_name]
                tournament_index += 1
        elif i < 2016:
            tournament_name = f"{i} LCK Regional Finals"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/{i}_Season_Korea_Regional_Finals/Match_History", tournament_name]
                tournament_index += 1
        else:
            tournament_name = f"{i} LCK Regional Finals"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/LCK/{i}_Season/Regional_Finals/Match_History", tournament_name]
                tournament_index += 1
        
        # Worlds
        if i < 2014:
            tournament_name = f"{i} Worlds"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/Season_{i%10}_World_Championship/Match_History", tournament_name]
                tournament_index += 1
        elif i > 2016:
            tournament_name = f"{i} Worlds"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/{i}_Season_World_Championship/Main_Event/Match_History", tournament_name]
                tournament_index += 1
        else:
            tournament_name = f"{i} Worlds"
            if tournament_name not in existing_tournaments:
                tournaments_to_add[tournament_index] = [f"https://lol.fandom.com/wiki/{i}_Season_World_Championship/Match_History", tournament_name]
                tournament_index += 1
    
    conn.close()
    
    print(f"Found {len(tournaments_to_add)} new tournaments to add for years {start_year}-{end_year}")
    
    # Process the new tournaments
    for i in tournaments_to_add:
        print(f"Processing: {tournaments_to_add[i][1]}")
        try:
            counter, counter2 = popdata(tournaments_to_add[i][0], tournaments_to_add[i][1], counter, counter2)
            print(f"  Added successfully. Next ID: {counter}")
        except Exception as e:
            print(f"  Error processing {tournaments_to_add[i][1]}: {str(e)}")
            continue
    
    print(f"Finished adding matches for years {start_year}-{end_year}")
    return counter, counter2

# Example usage:
# To add all 2025 matches:
# add_matches_for_year(2025, 2025)

# To add a range of years:
# add_matches_for_year(2024, 2025)

# To populate the entire database from scratch:
# add_matches_for_year(2013, 2025)


