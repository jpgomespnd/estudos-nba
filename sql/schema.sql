-- Esquema do banco. "IF NOT EXISTS" permite rodar este arquivo mais de uma vez.

CREATE TABLE IF NOT EXISTS teams (
    team_id      INTEGER PRIMARY KEY,
    abbreviation TEXT NOT NULL UNIQUE,
    full_name    TEXT NOT NULL
);

-- Uma linha por partida.
CREATE TABLE IF NOT EXISTS games (
    game_id   TEXT PRIMARY KEY,  -- texto, porque o ID começa com zeros: 0022500001
    season    TEXT NOT NULL,     -- exemplo: 2025-26
    game_date TEXT NOT NULL      -- formato AAAA-MM-DD
);

-- Uma linha por time em cada partida, ou seja, duas linhas por partida.
-- Guarda o que aconteceu DURANTE o jogo. Esses números só poderão virar variáveis
-- do modelo depois de resumidos a partir de jogos anteriores à partida prevista.
CREATE TABLE IF NOT EXISTS team_games (
    game_id    TEXT    NOT NULL REFERENCES games (game_id),
    team_id    INTEGER NOT NULL REFERENCES teams (team_id),
    is_home    INTEGER NOT NULL CHECK (is_home IN (0, 1)),
    won        INTEGER NOT NULL CHECK (won IN (0, 1)),
    minutes    INTEGER NOT NULL,
    pts        INTEGER NOT NULL,
    fgm        INTEGER NOT NULL,  -- arremessos de quadra convertidos
    fga        INTEGER NOT NULL,  -- arremessos de quadra tentados
    fg3m       INTEGER NOT NULL,  -- bolas de 3 convertidas
    fg3a       INTEGER NOT NULL,  -- bolas de 3 tentadas
    ftm        INTEGER NOT NULL,  -- lances livres convertidos
    fta        INTEGER NOT NULL,  -- lances livres tentados
    oreb       INTEGER NOT NULL,  -- rebotes ofensivos
    dreb       INTEGER NOT NULL,  -- rebotes defensivos
    reb        INTEGER NOT NULL,  -- total de rebotes
    ast        INTEGER NOT NULL,  -- assistências
    stl        INTEGER NOT NULL,  -- roubos de bola
    blk        INTEGER NOT NULL,  -- tocos
    tov        INTEGER NOT NULL,  -- desperdícios de bola
    pf         INTEGER NOT NULL,  -- faltas pessoais
    plus_minus INTEGER NOT NULL,  -- saldo de pontos na partida
    PRIMARY KEY (game_id, team_id)
);

CREATE INDEX IF NOT EXISTS idx_games_date ON games (game_date);
CREATE INDEX IF NOT EXISTS idx_team_games_team ON team_games (team_id);

-- Mostra cada partida em uma só linha, com mandante e visitante lado a lado.
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
