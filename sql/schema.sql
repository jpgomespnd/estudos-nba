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

-- As views são apagadas e recriadas sempre, para que uma mudança aqui
-- chegue ao banco sem precisar recriar as tabelas.
DROP VIEW IF EXISTS vw_jogos;
DROP VIEW IF EXISTS vw_fora_da_rotacao;
DROP VIEW IF EXISTS vw_rotacao;
DROP VIEW IF EXISTS vw_jogadores_time_final;
DROP VIEW IF EXISTS vw_elenco_final;

-- Mostra cada partida em uma só linha, com mandante e visitante lado a lado.
-- Partidas com is_neutral = 1 ficam de fora, porque não têm mandante.
CREATE VIEW vw_jogos AS
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

-- Elenco final: cada jogador pertence ao time do seu último jogo na temporada regular.
CREATE VIEW vw_elenco_final AS
WITH jogos_numerados AS (
    SELECT
        g.season,
        pg.player_id,
        pg.team_id,
        -- Numera os jogos de cada jogador do mais recente (1) para o mais antigo.
        ROW_NUMBER() OVER (
            PARTITION BY g.season, pg.player_id
            ORDER BY g.game_date DESC, g.game_id DESC
        ) AS ordem
    FROM player_games AS pg
    JOIN games AS g ON g.game_id = pg.game_id
    WHERE g.season_type = 'Regular Season'
)
SELECT season, player_id, team_id
FROM jogos_numerados
WHERE ordem = 1;

-- Totais de cada jogador SÓ nos jogos pelo time final, na temporada regular.
CREATE VIEW vw_jogadores_time_final AS
SELECT
    e.season,
    e.team_id,
    e.player_id,
    COUNT(*)          AS games,
    AVG(pg.minutes)   AS mpg,  -- minutos por jogo
    SUM(pg.minutes)   AS minutes,
    SUM(pg.pts)       AS pts,
    SUM(pg.fgm)       AS fgm,
    SUM(pg.fga)       AS fga,
    SUM(pg.fg3m)      AS fg3m,
    SUM(pg.fg3a)      AS fg3a,
    SUM(pg.ftm)       AS ftm,
    SUM(pg.fta)       AS fta,
    SUM(pg.oreb)      AS oreb,
    SUM(pg.dreb)      AS dreb,
    SUM(pg.reb)       AS reb,
    SUM(pg.ast)       AS ast,
    SUM(pg.stl)       AS stl,
    SUM(pg.blk)       AS blk,
    SUM(pg.tov)       AS tov,
    SUM(pg.pf)        AS pf,
    SUM(pg.plus_minus) AS plus_minus
FROM vw_elenco_final AS e
JOIN player_games AS pg ON pg.player_id = e.player_id AND pg.team_id = e.team_id
JOIN games AS g
  ON g.game_id = pg.game_id
 AND g.season = e.season
 AND g.season_type = 'Regular Season'
GROUP BY e.season, e.team_id, e.player_id;

-- Rotação ideal: os 9 jogadores com mais minutos por jogo, entre os que fizeram
-- pelo menos 20 jogos pelo time final. Os 5 primeiros são titulares.
-- Os minutos são ajustados para o time somar 240 (5 jogadores x 48 minutos).
CREATE VIEW vw_rotacao AS
WITH elegiveis AS (
    SELECT
        j.*,
        ROW_NUMBER() OVER (
            PARTITION BY j.season, j.team_id
            ORDER BY j.mpg DESC, j.minutes DESC
        ) AS ordem
    FROM vw_jogadores_time_final AS j
    WHERE j.games >= 20
),
nove AS (
    SELECT * FROM elegiveis WHERE ordem <= 9
)
SELECT
    n.season,
    n.team_id,
    n.player_id,
    n.ordem,
    CASE WHEN n.ordem <= 5 THEN 'Titular' ELSE 'Reserva' END AS funcao,
    n.games,
    n.mpg,
    240.0 * n.mpg / SUM(n.mpg) OVER (PARTITION BY n.season, n.team_id) AS minutos_simulacao,
    r.position,
    r.height_in,
    r.weight_lb
FROM nove AS n
LEFT JOIN rosters AS r
  ON r.season = n.season AND r.team_id = n.team_id AND r.player_id = n.player_id;

-- Jogadores que entrariam na rotação pelos minutos, mas ficaram fora por terem
-- menos de 20 jogos pelo time final. Serve para revisar a regra, caso a caso.
CREATE VIEW vw_fora_da_rotacao AS
WITH corte AS (
    SELECT season, team_id, MIN(mpg) AS menor_mpg
    FROM vw_rotacao
    GROUP BY season, team_id
)
SELECT j.season, j.team_id, j.player_id, j.games, j.mpg, c.menor_mpg
FROM vw_jogadores_time_final AS j
JOIN corte AS c ON c.season = j.season AND c.team_id = j.team_id
WHERE j.games < 20 AND j.mpg > c.menor_mpg;
