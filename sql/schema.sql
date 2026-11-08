CREATE TABLE IF NOT EXISTS teams (
    team_id      INTEGER PRIMARY KEY,
    abbreviation TEXT NOT NULL UNIQUE,
    full_name    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS games (
    game_id    TEXT PRIMARY KEY,
    season     TEXT NOT NULL,
    game_date  TEXT NOT NULL,
    is_neutral INTEGER NOT NULL CHECK (is_neutral IN (0, 1))
);

CREATE TABLE IF NOT EXISTS team_games (
    game_id    TEXT    NOT NULL REFERENCES games (game_id),
    team_id    INTEGER NOT NULL REFERENCES teams (team_id),
    is_home    INTEGER NOT NULL CHECK (is_home IN (0, 1)),
    won        INTEGER NOT NULL CHECK (won IN (0, 1)),
    minutes    INTEGER NOT NULL,
    pts        INTEGER NOT NULL,
    fgm        INTEGER NOT NULL,
    fga        INTEGER NOT NULL,
    fg3m       INTEGER NOT NULL,
    fg3a       INTEGER NOT NULL,
    ftm        INTEGER NOT NULL,
    fta        INTEGER NOT NULL,
    oreb       INTEGER NOT NULL,
    dreb       INTEGER NOT NULL,
    reb        INTEGER NOT NULL,
    ast        INTEGER NOT NULL,
    stl        INTEGER NOT NULL,
    blk        INTEGER NOT NULL,
    tov        INTEGER NOT NULL,
    pf         INTEGER NOT NULL,
    plus_minus INTEGER NOT NULL,
    PRIMARY KEY (game_id, team_id)
);

CREATE TABLE IF NOT EXISTS calendario (
    game_id      TEXT    PRIMARY KEY,
    season       TEXT    NOT NULL,
    game_date    TEXT    NOT NULL,
    home_team_id INTEGER NOT NULL REFERENCES teams (team_id),
    away_team_id INTEGER NOT NULL REFERENCES teams (team_id),
    is_neutral   INTEGER NOT NULL CHECK (is_neutral IN (0, 1)),
    status       INTEGER NOT NULL CHECK (status IN (1, 2, 3))  -- 1 agendado, 2 em andamento, 3 encerrado
);

CREATE INDEX IF NOT EXISTS idx_games_date ON games (game_date);
CREATE INDEX IF NOT EXISTS idx_team_games_team ON team_games (team_id);

CREATE VIEW IF NOT EXISTS vw_jogos AS
SELECT
    g.game_id,
    g.season,
    g.game_date,
    casa.team_id AS home_team_id,
    fora.team_id AS away_team_id,
    casa.pts     AS home_pts,
    fora.pts     AS away_pts,
    casa.won     AS home_won
FROM games AS g
JOIN team_games AS casa ON casa.game_id = g.game_id AND casa.is_home = 1
JOIN team_games AS fora ON fora.game_id = g.game_id AND fora.is_home = 0;
