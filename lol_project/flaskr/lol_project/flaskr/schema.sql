DROP TABLE IF EXISTS blueTeam;
DROP TABLE IF EXISTS redTeam;
DROP TABLE IF EXISTS game;

CREATE TABLE blueTeam(
    gameId INTEGER NOT NULL,
    top TEXT NOT NULL,
    jg TEXT NOT NULL,
    mid TEXT NOT NULL,
    adc TEXT NOT NULL,
    sup TEXT NOT NULL,
    FOREIGN KEY(gameId) REFERENCES game(id)
);

CREATE TABLE redTeam(
    gameId INTEGER NOT NULL,
    top TEXT NOT NULL,
    jg TEXT NOT NULL,
    mid TEXT NOT NULL,
    adc TEXT NOT NULL,
    sup TEXT NOT NULL,
    FOREIGN KEY(gameId) REFERENCES game(id)
);
CREATE TABLE game (
    id INTEGER PRIMARY KEY NOT NULL,
    tournament TEXT NOT NULL,
    game TEXT NOT NULL,
    red TEXT NOT NULL,
    blue TEXT NOT NULL
);




