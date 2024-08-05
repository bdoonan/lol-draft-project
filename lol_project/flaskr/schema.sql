DROP TABLE IF EXISTS blueTeam;
DROP TABLE IF EXISTS redTeam;
DROP TABLE IF EXISTS game;

CREATE TABLE blueTeam(
    team TEXT PRIMARY KEY,
    top TEXT NOT NULL,
    jg TEXT NOT NULL,
    mid TEXT NOT NULL,
    adc TEXT NOT NULL,
    sup TEXT NOT NULL
);

CREATE TABLE redTeam(
    team TEXT PRIMARY KEY,
    top TEXT NOT NULL,
    jg TEXT NOT NULL,
    mid TEXT NOT NULL,
    adc TEXT NOT NULL,
    sup TEXT NOT NULL
);


CREATE TABLE game (
    number INTEGER PRIMARY KEY NOT NULL,
    tournament TEXT NOT NULL,
    game TEXT NOT NULL,
    red TEXT NOT NULL,
    blue TEXT NOT NULL,
    FOREIGN KEY (red) REFERENCES redTeam (team),
    FOREIGN KEY (blue) REFERENCES blueTeam (team)

);




