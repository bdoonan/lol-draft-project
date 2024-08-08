from bs4 import BeautifulSoup
import requests
import sqlite3
#Only run this file once to make the databases

def makemaps(url, picksandbans, squads):   
    response = requests.get(url)
    data = response.text

    # Parse the HTML content
    soup = BeautifulSoup(data, 'html.parser')

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
                value = str(value).lower()
                value = value.replace(" ", "")
                value = value.replace("'", "")
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
        team = (i.find_all('a', class_="to_hasTooltip"))
        #make sure the component is not empty as there are some in the html file
        if len(team)>0:
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
def makedb(tournament, picksandbans, squads, index, index2):
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
    #connect to database
    conn = sqlite3.connect("test.db")
    cur = conn.cursor()
    #loop through the teams hashmap and input into the game database the two teams at each index

    for i in range(len(squads)):
        #gameid = i
        tournament = tournament
        red = squads[i][1]
        blue = squads[i][0]

        cur.execute('''
                    INSERT INTO game(id, tournament, red, blue) 
                    VALUES(?,?,?,?) ''', (index, tournament, red, blue))
        conn.commit()
        #we also put the id values for the blue and red team tables that will be updated when we go through that hashmap
        cur.execute('''
                    INSERT INTO blueTeam(id, top, jg, mid, adc, sup, ban1, ban2, ban3, ban4, ban5)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?) ''', (index, top, jg, mid, adc, sup, ban1, ban2, ban3, ban4, ban5))
        
        cur.execute('''
                    INSERT INTO redTeam(id, top, jg, mid, adc, sup, ban1, ban2, ban3, ban4, ban5)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?) ''', (index, top, jg, mid, adc, sup, ban1, ban2, ban3, ban4, ban5))
        index+=1
    #now we loop through the champions using the mod rule discussed earlier
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
    tournament = tournament
    makemaps(url, picksandbans, squads)
    makedb(tournament, picksandbans, squads, counter, counter2)
    counter += len(squads)
    counter2 = counter
    return counter, counter2
#this is the individual entries
# url = "https://lol.fandom.com/wiki/2024_Mid-Season_Invitational/Match_History"
# tournament = "2024 MSI"
# counter, counter2 = popdata(url, tournament, counter, counter2)

# url = "https://lol.fandom.com/wiki/2016_Season_World_Championship/Match_History"
# tournament = "2016 Worlds"
# counter, counter2 = popdata(url, tournament, counter, counter2)

fulltournaments = {}
fulltournaments[0]=["https://lol.fandom.com/wiki/2024_Mid-Season_Invitational/Match_History", "2024 MSI"]
fulltournaments[1]=["https://lol.fandom.com/wiki/2023_Mid-Season_Invitational/Match_History", "2023 MSI"]
fulltournaments[2]=["https://lol.fandom.com/wiki/2022_Mid-Season_Invitational/Match_History", "2022 MSI"]
fulltournaments[3]=["https://lol.fandom.com/wiki/2021_Mid-Season_Invitational/Match_History", "2021 MSI"]
fulltournaments[4]=["https://lol.fandom.com/wiki/2019_Mid-Season_Invitational/Main_Event/Match_History", "2019 MSI"]
fulltournaments[5]=["https://lol.fandom.com/wiki/2018_Mid-Season_Invitational/Main_Event/Match_History", "2018 MSI"]
fulltournaments[6]=["https://lol.fandom.com/wiki/2017_Mid-Season_Invitational/Main_Event/Match_History", "2017 MSI"]
fulltournaments[7]=["https://lol.fandom.com/wiki/2016_Mid-Season_Invitational/Match_History", "2016 MSI"]
fulltournaments[8]=["https://lol.fandom.com/wiki/2015_Mid-Season_Invitational/Match_History", "2015 MSI"]

fulltournaments[10]=["https://lol.fandom.com/wiki/Season_2_World_Championship/Match_History", "2012 Worlds"]
fulltournaments[11]=["https://lol.fandom.com/wiki/Season_3_World_Championship/Match_History", "2013 Worlds"]

fulltournaments[12]=["https://lol.fandom.com/wiki/2014_Season_World_Championship/Match_History", "2014 Worlds"]
fulltournaments[13]=["https://lol.fandom.com/wiki/2015_Season_World_Championship/Match_History", "2015 Worlds"]
fulltournaments[14]=["https://lol.fandom.com/wiki/2016_Season_World_Championship/Match_History", "2016 Worlds"]

fulltournaments[15]=["https://lol.fandom.com/wiki/2017_Season_World_Championship/Main_Event/Match_History", "2017 Worlds"]
fulltournaments[16]=["https://lol.fandom.com/wiki/2018_Season_World_Championship/Main_Event/Match_History", "2018 Worlds"]
fulltournaments[17]=["https://lol.fandom.com/wiki/2019_Season_World_Championship/Main_Event/Match_History", "2019 Worlds"]
fulltournaments[18]=["https://lol.fandom.com/wiki/2020_Season_World_Championship/Main_Event/Match_History", "2020 Worlds"]
fulltournaments[19]=["https://lol.fandom.com/wiki/2021_Season_World_Championship/Main_Event/Match_History", "2021 Worlds"]
fulltournaments[20]=["https://lol.fandom.com/wiki/2022_Season_World_Championship/Main_Event/Match_History", "2022 Worlds"]
fulltournaments[21]=["https://lol.fandom.com/wiki/2023_Season_World_Championship/Main_Event/Match_History", "2023 Worlds"]


for i in fulltournaments:
    #print (fulltournaments[i][0])
    counter, counter2 = popdata(fulltournaments[i][0], fulltournaments[i][1], counter, counter2)
print("Databases populated")