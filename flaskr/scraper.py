from bs4 import BeautifulSoup
import requests
import sqlite3
import os
import urllib.request 
#Only run this file once to make the databases

def makemaps(url, playermap, picksandbans, squads):   
    response = requests.get(url)
    data = response.text
    #path to save team images to
    image_path = "flaskr/static/images/teams/"
    # Parse the HTML content
    soup = BeautifulSoup(data, 'html.parser')
    index = -1
    fullgame = soup.find_all('tr', class_ = ["mhgame-blue multirow-highlighter", "mhgame-red multirow-highlighter" ])
    for full in fullgame:
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
                if value == "K'Sante":
                    value = "KSante"
                elif "'" in value:
                    value = value.replace("'", "")
                    value = value.lower()
                    value = value.capitalize()
                value = value.replace(".","")
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
            if len(images)>0:
               if not os.path.isfile(image_path+team[0]['title']+'.png'):
                   if 'https' in images[0]['src']:
                       urllib.request.urlretrieve(images[0]['src'],image_path+team[0]['title']+'.png')
                       
                   else:
                       urllib.request.urlretrieve(images[0]['data-src'],image_path+team[0]['title']+'.png')
                       
                    
                   
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
def makedb(tournament, playermap, picksandbans, squads, index, index2):
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
    for i in range(len(squads)):
        #gameid = i
        tournament = tournament
        #print(tournament)
        red = squads[i][1]
        blue = squads[i][0]
        cur.execute('''
                    INSERT INTO game(id, tournament, red, blue) 
                    VALUES(?,?,?,?) ''', (index, tournament, red, blue))
        conn.commit()
        #we also put the id values for the blue and red team tables that will be updated when we go through that hashmap
        cur.execute('''
                    INSERT INTO blueTeam(id, top, jg, mid, adc, sup, ban1, ban2, ban3, ban4, ban5, topPlayer, jgPlayer, midPlayer, adcPlayer, supPlayer)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ''', (index, top, jg, mid, adc, sup, ban1, ban2, ban3, ban4, ban5, topplayer, jgplayer, midplayer, adcplayer, supplayer))
        conn.commit()
        cur.execute('''
                    INSERT INTO redTeam(id, top, jg, mid, adc, sup, ban1, ban2, ban3, ban4, ban5, topPlayer, jgPlayer, midPlayer, adcPlayer, supPlayer)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ''', (index, top, jg, mid, adc, sup, ban1, ban2, ban3, ban4, ban5, topplayer, jgplayer, midplayer, adcplayer, supplayer))
        conn.commit()
        index+=1
    #now we loop through the champions using the mod rule discussed earlier
    for i in range(len(playermap)):
        #print (playermap[i])
        if i%2==0:
            topplayer = playermap[i][0]
            jgplayer = playermap[i][1]
            midplayer = playermap[i][2]
            adcplayer = playermap[i][3]
            supplayer = playermap[i][4]
            cur.execute('''
                    UPDATE blueTeam SET topPlayer= ?, jgPlayer = ?, midPlayer = ?, adcPlayer = ?, supPlayer = ? WHERE id = ?
                    ''', (topplayer, jgplayer, midplayer, adcplayer, supplayer, playercounter))
            conn.commit()
        else:
            topplayer = playermap[i][0]
            jgplayer = playermap[i][1]
            midplayer = playermap[i][2]
            adcplayer = playermap[i][3]
            supplayer = playermap[i][4]
            cur.execute('''
                    UPDATE redTeam SET topPlayer= ?, jgPlayer = ?, midPlayer = ?, adcPlayer = ?, supPlayer = ? WHERE id = ?
                    ''', (topplayer, jgplayer, midplayer, adcplayer, supplayer, playercounter))
            conn.commit()
            playercounter+=1
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
            cur.execute('''
                    UPDATE blueTeam SET ban1 = ?, ban2 = ?, ban3 = ?, ban4 = ?, ban5 = ? WHERE id = ?
                    ''', (ban1, ban2, ban3, ban4, ban5, gameid))
            conn.commit()

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
            cur.execute('''
                    UPDATE redTeam SET ban1 = ?, ban2 = ?, ban3 = ?, ban4 = ?, ban5 = ? WHERE id = ?
                    ''', (ban1, ban2, ban3, ban4, ban5, gameid))
            conn.commit()

        elif i%4 == 2:
            #these are the blue picks
            top = picksandbans[i][0]
            jg = picksandbans[i][1]
            mid = picksandbans[i][2]
            adc = picksandbans[i][3]
            sup = picksandbans[i][4]
            cur.execute('''
                    UPDATE blueTeam SET top = ?, jg = ?, mid = ?, adc = ?, sup = ? WHERE id = ?
                    ''', (top, jg, mid, adc, sup, gameid))
            conn.commit()
        else:
            #these are the red picks
            top = picksandbans[i][0]
            jg = picksandbans[i][1]
            mid = picksandbans[i][2]
            adc = picksandbans[i][3]
            sup = picksandbans[i][4]
            cur.execute('''
                    UPDATE redTeam SET top = ?, jg = ?, mid = ?, adc = ?, sup = ? WHERE id = ?
                    ''', (top, jg, mid, adc, sup, gameid))
            conn.commit()
            index2 +=1


    conn.close()
#function used to populate the database with user manually inputting url and tournament name and then incrementing the counter to make sure game id is unique
def popdata(url, tournament, counter, counter2):
    url = url
    picksandbans = {}
    squads = {}
    playermap ={}
    tournament = tournament
    makemaps(url, playermap, picksandbans, squads)
    makedb(tournament, playermap, picksandbans, squads, counter, counter2)
    counter += len(squads)
    counter2 = counter
    return counter, counter2


#Now we populate a hashmap for links and tournament names

fulltournaments = {}
fulltournamentsindex = 0

for i in range(2013,2025):
    #Winter playoffs
    #LEC
    if i>2022:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/LEC/" + str(i) +"_Season/Winter_Playoffs/Match_History",str(i) + " LEC Winter Playoffs"]
        fulltournamentsindex+=1
    #OGN since this is only 2 and are special queries to remove regular season games we will do two individual if statements for all three splits in 2013 and 2014
    fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/LEC/" + str(i) +"_Season/Winter_Playoffs/Match_History",str(i) + " LEC Winter Playoffs"]
    fulltournamentsindex+=1
    if i == 2013:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryGame?MHG%5Btournament%5D=Champions+2013+Winter&MHG%5Bstartdate%5D=2012-12-25&MHG%5Bpreload%5D=Tournament&MHG%5Bspl%5D=yes&_run=",str(i) + " OGN Winter Playoffs"]
        fulltournamentsindex+=1
    if i == 2014:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryGame?MHG%5Btournament%5D=Champions+2014+Winter&MHG%5Bstartdate%5D=2013-12-25&MHG%5Bpreload%5D=Tournament&MHG%5Bspl%5D=yes&_run=",str(i) + " OGN Winter Playoffs"]
        fulltournamentsindex+=1
    #Spring playoffs
    #LCS
    if i==2013:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/NA_LCS/Season_" + str(i%10) +"/Spring_Playoffs/Match_History",str(i) + " LCS Spring Playoffs"]
        fulltournamentsindex+=1
    elif i<2019:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/NA_LCS/" + str(i) +"_Season/Spring_Playoffs/Match_History",str(i) + " LCS Spring Playoffs"]
        fulltournamentsindex+=1
    elif i == 2021:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/LCS/" + str(i) +"_Season/Mid-Season_Showdown/Match_History",str(i) + " LCS Spring Playoffs"]
        fulltournamentsindex+=1
    else:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/LCS/" + str(i) +"_Season/Spring_Playoffs/Match_History",str(i) + " LCS Spring Playoffs"]
        fulltournamentsindex+=1
    #LEC
    if i==2013:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/EU_LCS/Season_" + str(i%10) +"/Spring_Playoffs/Match_History",str(i) + " LEC Spring Playoffs"]
        fulltournamentsindex+=1
    elif i<2019:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/EU_LCS/" + str(i) +"_Season/Spring_Playoffs/Match_History",str(i) + " LEC Spring Playoffs"]
        fulltournamentsindex+=1
    else:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/LEC/" + str(i) +"_Season/Spring_Playoffs/Match_History",str(i) + " LEC Spring Playoffs"]
        fulltournamentsindex+=1
    #OGN/LCK
    if i == 2013:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryGame?MHG%5Btournament%5D=Champions+2013+Spring&MHG%5Bstartdate%5D=2013-05-08&MHG%5Bpreload%5D=Tournament&MHG%5Bspl%5D=yes&_run=",str(i) + " OGN Spring Playoffs"]
        fulltournamentsindex+=1
    elif i == 2014:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryGame?MHG%5Btournament%5D=Champions+2014+Spring&MHG%5Bstartdate%5D=2014-04-16&MHG%5Bpreload%5D=Tournament&MHG%5Bspl%5D=yes&_run=",str(i) + " OGN Spring Playoffs"]
        fulltournamentsindex+=1
    elif i<2016:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/Champions/" + str(i) + "_Season/Spring_Playoffs/Match_History",str(i) + " LCK Spring Playoffs"]
        fulltournamentsindex+=1
    else:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/LCK/" + str(i) + "_Season/Spring_Playoffs/Match_History",str(i) + " LCK Spring Playoffs"]
        fulltournamentsindex+=1
    #LPL
    fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/LPL/" + str(i) + "_Season/Spring_Playoffs/Match_History",str(i) + " LPL Spring Playoffs"]
    fulltournamentsindex+=1
    
    #MSIs
    if 2016<i<2020:    
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/" + str(i) +"_Mid-Season_Invitational/Main_Event/Match_History",str(i) + " MSI"]
        fulltournamentsindex+=1
  
    else:    
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/" + str(i) +"_Mid-Season_Invitational/Match_History",str(i) + " MSI"]
        fulltournamentsindex+=1
    
    
    #Summer playoffs
    #LCS
    if i==2013:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/NA_LCS/Season_" + str(i%10) +"/Summer_Playoffs/Match_History",str(i) + " LCS Summer Playoffs"]
        fulltournamentsindex+=1
    elif i<2019:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/NA_LCS/" + str(i) +"_Season/Summer_Playoffs/Match_History",str(i) + " LCS Summer Playoffs"]
        fulltournamentsindex+=1
    elif i<2021:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/LCS/" + str(i) +"_Season/Summer_Playoffs/Match_History",str(i) + " LCS Summer Playoffs"]
        fulltournamentsindex+=1
    else:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/LCS/" + str(i)+ "_Season/Championship/Match_History",str(i) + " LCS Summer Playoffs"]
        fulltournamentsindex+=1
    #LEC
    if i==2013:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/EU_LCS/Season_" + str(i%10) +"/Summer_Playoffs/Match_History",str(i) + " LEC Summer Playoffs"]
        fulltournamentsindex+=1
    elif i<2019:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/EU_LCS/" + str(i) +"_Season/Summer_Playoffs/Match_History",str(i) + " LEC Summer Playoffs"]
        fulltournamentsindex+=1
    else:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/LEC/" + str(i) +"_Season/Summer_Playoffs/Match_History",str(i) + " LEC Summer Playoffs"]
        fulltournamentsindex+=1
    #LCK/OGN
    if i == 2013:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryGame?MHG%5Btournament%5D=Champions+2013+Summer&MHG%5Bstartdate%5D=2013-08-07&MHG%5Bpreload%5D=Tournament&MHG%5Bspl%5D=yes&_run=",str(i) + " OGN Summer Playoffs"]
        fulltournamentsindex+=1
    elif i == 2014:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryGame?MHG%5Btournament%5D=Champions+2014+Summer&MHG%5Bstartdate%5D=2014-07-16&MHG%5Bpreload%5D=Tournament&MHG%5Bspl%5D=yes&_run=",str(i) + " OGN Summer Playoffs"]
        fulltournamentsindex+=1
    elif i<2016:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/Champions/" + str(i) +"_Season/Summer_Playoffs/Match_History",str(i) + " LCK Summer Playoffs"]
        fulltournamentsindex+=1
    else:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/LCK/" + str(i) +"_Season/Summer_Playoffs/Match_History",str(i) + " LCK Summer Playoffs"]
        fulltournamentsindex+=1
    #LPL
    fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/LPL/" + str(i) +"_Season/Summer_Playoffs/Match_History",str(i) + " LPL Summer Playoffs"]
    fulltournamentsindex+=1
    

    #Worlds
    if i<2014:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/Season_" + str(i%10) +"_World_Championship/Match_History",str(i) + " Worlds"]
        fulltournamentsindex+=1
    elif i>2016:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/" + str(i) +"_Season_World_Championship/Main_Event/Match_History",str(i) + " Worlds"]
        fulltournamentsindex+=1
    else:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/" + str(i) +"_Season_World_Championship/Match_History",str(i) + " Worlds"]
        fulltournamentsindex+=1
    
    #LEC Season Finals
    fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/LEC/" + str(i) +"_Season/Season_Finals/Match_History",str(i) + " LEC Season Finals"]
    fulltournamentsindex+=1
    
    #Regional Finals
    #LCS
    if i < 2019:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/NA_LCS/" + str(i) +"_Season/Regional_Finals/Match_History",str(i) + " LCS Regional Finals"]
        fulltournamentsindex+=1
    else:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/LCS/" + str(i) +"_Season/Regional_Finals/Match_History",str(i) + " LCS Regional Finals"]
        fulltournamentsindex+=1
    #LEC
    if i<2019:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/EU_LCS/" + str(i) +"_Season/Regional_Finals/Match_History",str(i) + " LEC Regional Finals"]
        fulltournamentsindex+=1
    else:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/LEC/" + str(i) +"_Season/Regional_Finals/Match_History",str(i) + " LEC Regional Finals"]
        fulltournamentsindex+=1
    #LPL
    fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/LPL/" + str(i) +"_Season/Regional_Finals/Match_History",str(i) + " LPL Regional Finals"]
    fulltournamentsindex+=1
    #LCK
    if i == 2013:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/Season_" + str(i%10) +"_Korea_Regional_Finals/Match_History",str(i) + " OGN Regional Finals"]
        fulltournamentsindex+=1
    elif i < 2016:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/" + str(i) +"_Season_Korea_Regional_Finals/Match_History",str(i) + " LCK Regional Finals"]
        fulltournamentsindex+=1
    else:
        fulltournaments[fulltournamentsindex]=["https://lol.fandom.com/wiki/LCK/" + str(i) +"_Season/Regional_Finals/Match_History",str(i) + " LCK Regional Finals"]
        fulltournamentsindex+=1
    


#This calls the functions for all of the tournaments
for i in fulltournaments:
    #print (fulltournaments[i][0])
    counter, counter2 = popdata(fulltournaments[i][0], fulltournaments[i][1], counter, counter2)

# url = 'https://lol.fandom.com/wiki/2017_Season_World_Championship/Main_Event/Match_History'
# picksandbans = {}
# squads = {}
# playermap ={}
# tournament = '2017 MSI'
# makemaps(url, playermap, picksandbans, squads)
# makedb(tournament, playermap, picksandbans, squads, counter, counter2)
print("Databases populated")


