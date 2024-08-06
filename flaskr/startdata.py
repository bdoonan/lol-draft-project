import sqlite3
conn = sqlite3.connect("test.db")
cur = conn.cursor()

cur.execute('''DROP TABLE game''')
cur.execute('''DROP TABLE redTeam''')
cur.execute('''DROP TABLE blueTeam''')
cur.execute('''
            CREATE TABLE game(id INT PRIMARY KEY, tournament TEXT, game INT, red TEXT, blue TEXT)
            ''')
cur.execute('''
            CREATE TABLE redTeam(id INT, top TEXt, jg TEXT, mid TEXT, adc TEXT, sup TEXT, ban1 TEXT, ban2 TEXT, ban3 TEXT, ban4 TEXT, ban5 TEXT, FOREIGN KEY(id) REFERENCES game(id))
            ''')
cur.execute('''
            CREATE TABLE blueTeam(id INT, top TEXt, jg TEXT, mid TEXT, adc TEXT, sup TEXT, ban1 TEXT, ban2 TEXT, ban3 TEXT, ban4 TEXT, ban5 TEXT, FOREIGN KEY(id) REFERENCES game(id))
            ''')
