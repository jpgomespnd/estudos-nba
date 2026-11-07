-- Esquema do banco. "IF NOT EXISTS" permite rodar este arquivo mais de uma vez.
-- Ao mudar uma tabela, aumente VERSAO_ESQUEMA em scripts/banco.py.

CREATE TABLE IF NOT EXISTS teams (
    team_id      INTEGER PRIMARY KEY,
    abbreviation TEXT NOT NULL UNIQUE,
    full_name    TEXT NOT NULL
);

-- Uma linha por partida.
CREATE TABLE IF NOT EXISTS games (
    game_id     TEXT PRIMARY KEY,  -- texto, porque o ID começa com zeros: 0022500001
    season      TEXT NOT NULL,     -- exemplo: 2025-26
    season_type TEXT NOT NULL CHECK (season_type IN ('Regular Season', 'Playoffs')),
    game_date   TEXT NOT NULL,     -- formato AAAA-MM-DD
    -- 1 quando a API não aponta mandante: os dois times vêm marcados com "@".
    is_neutral  INTEGER NOT NULL CHECK (is_neutral IN (0, 1))
);

-- Uma linha por time em cada partida, ou seja, duas linhas por partida.
-- Guarda o que aconteceu DURANTE o jogo. Esses números só poderão virar variáveis
-- do modelo depois de resumidos a partir de jogos anteriores à partida prevista.
CREATE TABLE IF NOT EXISTS team_games (
    game_id    TEXT    NOT NULL REFERENCES games (game_id),
    team_id    INTEGER NOT NULL REFERENCES teams (team_id),
    is_home    INTEGER NOT NULL CHECK (is_home IN (0, 1)),
    won        INTEGER NOT NULL CHECK (won IN (0, 1)),
    minutes    INTEGER NOT NULL,  -- soma dos minutos dos jogadores: 240 sem prorrogação
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

CREATE TABLE IF NOT EXISTS players (
    player_id INTEGER PRIMARY KEY,
    name      TEXT NOT NULL
);

-- Uma linha por jogador em cada partida em que ele entrou em quadra.
CREATE TABLE IF NOT EXISTS player_games (
    game_id    TEXT    NOT NULL,
    player_id  INTEGER NOT NULL REFERENCES players (player_id),
    team_id    INTEGER NOT NULL,
    minutes    INTEGER NOT NULL,  -- a API arredonda para minutos inteiros
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
    PRIMARY KEY (game_id, player_id),
    -- Chave estrangeira composta: o time do jogador precisa ter jogado essa partida.
    FOREIGN KEY (game_id, team_id) REFERENCES team_games (game_id, team_id)
);

-- Elenco oficial de cada time, como a API mostra para a temporada.
CREATE TABLE IF NOT EXISTS rosters (
    season     TEXT    NOT NULL,
    team_id    INTEGER NOT NULL REFERENCES teams (team_id),
    player_id  INTEGER NOT NULL REFERENCES players (player_id),
    position   TEXT,     -- exemplo: G, F, C, G-F ou F-C
    height_in  INTEGER,  -- altura em polegadas
    weight_lb  INTEGER,  -- peso em libras
    PRIMARY KEY (season, team_id, player_id)
);

CREATE INDEX IF NOT EXISTS idx_games_date ON games (game_date);
CREATE INDEX IF NOT EXISTS idx_team_games_team ON team_games (team_id);
CREATE INDEX IF NOT EXISTS idx_player_games_player ON player_games (player_id);
CREATE INDEX IF NOT EXISTS idx_player_games_team ON player_games (game_id, team_id);

-- Mostra cada partida em uma só linha, com mandante e visitante lado a lado.
-- Partidas com is_neutral = 1 ficam de fora, porque não têm mandante.
CREATE VIEW IF NOT EXISTS vw_jogos AS
SELECT
    g.game_id,
    g.season,
    g.season_type,
    g.game_date,
    casa.team_id AS home_team_id,
    fora.team_id AS away_team_id,
    casa.pts     AS home_pts,
    fora.pts     AS away_pts,
    casa.won     AS home_won
FROM games AS g
JOIN team_games AS casa ON casa.game_id = g.game_id AND casa.is_home = 1
JOIN team_games AS fora ON fora.game_id = g.game_id AND fora.is_home = 0;
