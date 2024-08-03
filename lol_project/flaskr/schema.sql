DROP TABLE IF EXISTS blueTeam;
DROP TABLE IF EXISTS redTeam;
DROP TABLE IF EXISTS game;

CREATE TABLE blueTeam(
    team TEXT PRIMARY KEY,
    pick1 TEXT NOT NULL,
    pick2 TEXT NOT NULL,
    pick3 TEXT NOT NULL,
    pick4 TEXT NOT NULL,
    pick5 TEXT NOT NULL
);

CREATE TABLE redTeam(
    team TEXT PRIMARY KEY,
    pick1 TEXT NOT NULL,
    pick2 TEXT NOT NULL,
    pick3 TEXT NOT NULL,
    pick4 TEXT NOT NULL,
    pick5 TEXT NOT NULL
);


CREATE TABLE game (
    year INTEGER PRIMARY KEY NOT NULL,
    league TEXT NOT NULL,
    red TEXT NOT NULL,
    blue TEXT NOT NULL,
    FOREIGN KEY (red) REFERENCES redTeam (team),
    FOREIGN KEY (blue) REFERENCES blueTeam (team)

);




