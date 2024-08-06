from bs4 import BeautifulSoup
import requests
import sqlite3
#Only run this file once to make the databases
# Fetch the web page
url = "https://lol.fandom.com/wiki/2016_Season_World_Championship/Match_History"
response = requests.get(url)
data = response.text

# Parse the HTML content
soup = BeautifulSoup(data, 'html.parser')

# Extract the pick and bans and input into a hashmap
# Every four indexes are a new game so the index for blue_bans%4 == 0, red_bans%4 == 1, blue_picks%4 == 2, red_picks%4 == 3
#Use this to input in database later
titles = soup.find_all('td')
quotes={}
index = 0
index2=0
for title in titles:
    champs =(title.find_all('span', class_ = "sprite champion-sprite"))
    if len(champs)>=1:
        for i in range(len(champs)):
            value = champs[i]['title']
            value = str(value).lower()
            value = value.replace(" ", "")
            value = value.replace("'", "")
            if i ==0:
                quotes[index] = [value]
            else:
                quotes[index].append(value)
        index+=1
#We now do this for the teams that play
teams = soup.find_all('td', class_= "mhgame-result")
squads = {}
index = 0
index2 = 0
for i in teams:
    team = (i.find_all('a', class_="to_hasTooltip"))
    #make sure the component is not empty as there are some in the html file
    if len(team)>0:
        #get rid of the patch objects
        if team[0]['title'] != "Patch 6.18":
            value = team[0]['title']
            # value = str(value).lower()
            # value = value.replace(" ", "")
            # value = value.replace("-", "")
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
index = 0
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
    gameid = i
    tournament = "2016 Worlds"
    game = 1
    red = squads[i][1]
    blue = squads[i][0]

    cur.execute('''
                INSERT INTO game(id, tournament, game, red, blue) 
                VALUES(?,?,?,?,?) ''', (gameid, tournament, game, red, blue))
    conn.commit()
    #we also put the id values for the blue and red team tables that will be updated when we go through that hashmap
    cur.execute('''
                INSERT INTO blueTeam(id, top, jg, mid, adc, sup, ban1, ban2, ban3, ban4, ban5)
                VALUES(?,?,?,?,?,?,?,?,?,?,?) ''', (index, top, jg, mid, adc, sup, ban1, ban2, ban3, ban4, ban5))
    
    cur.execute('''
                INSERT INTO redTeam(id, top, jg, mid, adc, sup, ban1, ban2, ban3, ban4, ban5)
                VALUES(?,?,?,?,?,?,?,?,?,?,?) ''', (index, top, jg, mid, adc, sup, ban1, ban2, ban3, ban4, ban5))
    index+=1
index = 0
#now we loop through the champions using the mod rule discussed earlier
for i in range(len(quotes)):
    
    gameid = index
    if i%4 == 0:
        #these are the bluebans
        ban1 = quotes[i][0]
        ban2 = quotes[i][1]
        ban3 = quotes[i][2]
        ban4 = "null"
        ban5 = "null"
        cur.execute('''
                UPDATE blueTeam SET ban1 = ?, ban2 = ?, ban3 = ?, ban4 = ?, ban5 = ? WHERE id = ?
                 ''', (ban1, ban2, ban3, ban4, ban5, gameid))
        conn.commit()

    elif i%4 == 1:
        #these are the red bans
        ban1 = quotes[i][0]
        ban2 = quotes[i][1]
        ban3 = quotes[i][2]
        ban4 = "null"
        ban5 = "null"
        cur.execute('''
                UPDATE redTeam SET ban1 = ?, ban2 = ?, ban3 = ?, ban4 = ?, ban5 = ? WHERE id = ?
                 ''', (ban1, ban2, ban3, ban4, ban5, gameid))
        conn.commit()

    elif i%4 == 2:
        #these are the blue picks
        top = quotes[i][0]
        jg = quotes[i][1]
        mid = quotes[i][2]
        adc = quotes[i][3]
        sup = quotes[i][4]
        cur.execute('''
                UPDATE blueTeam SET top = ?, jg = ?, mid = ?, adc = ?, sup = ? WHERE id = ?
                 ''', (top, jg, mid, adc, sup, gameid))
        conn.commit()
    else:
        #these are the red picks
        top = quotes[i][0]
        jg = quotes[i][1]
        mid = quotes[i][2]
        adc = quotes[i][3]
        sup = quotes[i][4]
        cur.execute('''
                UPDATE redTeam SET top = ?, jg = ?, mid = ?, adc = ?, sup = ? WHERE id = ?
                 ''', (top, jg, mid, adc, sup, gameid))
        conn.commit()
        index +=1


conn.close()

