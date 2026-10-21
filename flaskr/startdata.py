import sqlite3
conn = sqlite3.connect("test.db")
cur = conn.cursor()

cur.execute('''DROP TABLE IF EXISTS game''')
cur.execute('''DROP TABLE IF EXISTS redTeam''')
cur.execute('''DROP TABLE IF EXISTS blueTeam''')
cur.execute('''DROP TABLE IF EXISTS checkid''')

cur.execute('''
            CREATE TABLE game(id INT PRIMARY KEY, tournament TEXT, red TEXT, blue TEXT, vod TEXT)
            ''')
cur.execute('''
            CREATE TABLE redTeam(id INT, top TEXt, jg TEXT, mid TEXT, adc TEXT, sup TEXT, ban1 TEXT, ban2 TEXT, ban3 TEXT, ban4 TEXT, ban5 TEXT, topPlayer TEXT, jgPlayer TEXT, midPlayer TEXT, adcPlayer TEXT, supPlayer TEXT, FOREIGN KEY(id) REFERENCES game(id))
            ''')
cur.execute('''
            CREATE TABLE blueTeam(id INT, top TEXt, jg TEXT, mid TEXT, adc TEXT, sup TEXT, ban1 TEXT, ban2 TEXT, ban3 TEXT, ban4 TEXT, ban5 TEXT, topPlayer TEXT, jgPlayer TEXT, midPlayer TEXT, adcPlayer TEXT, supPlayer TEXT, FOREIGN KEY(id) REFERENCES game(id))
            ''')
cur.execute('''
            CREATE TABLE checkid(id INT)
            ''')
print("Databases created")
