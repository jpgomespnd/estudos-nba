"""Baixa as temporadas regulares da NBA e guarda no banco SQLite.

Pode ser rodado de novo sem duplicar nada, porque as linhas são atualizadas.

Como rodar, a partir da pasta do projeto:
    .venv\\Scripts\\python.exe scripts\\coletar_jogos.py
"""

import time

import requests
from nba_api.stats.endpoints import leaguegamelog
from nba_api.stats.static import teams

from banco import conectar, criar_tabelas

TEMPORADAS = ["2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]
PAUSA_SEGUNDOS = 3
TEMPO_LIMITE_SEGUNDOS = 30
MAXIMO_TENTATIVAS = 3

SQL_TIME = """
    INSERT INTO teams (team_id, abbreviation, full_name)
    VALUES (:id, :abbreviation, :full_name)
    ON CONFLICT (team_id) DO UPDATE SET
        abbreviation = excluded.abbreviation,
        full_name = excluded.full_name
"""

SQL_JOGO = """
    INSERT INTO games (game_id, season, game_date, is_neutral)
    VALUES (:game_id, :season, :game_date, :is_neutral)
    ON CONFLICT (game_id) DO UPDATE SET
        season = excluded.season,
        game_date = excluded.game_date,
        is_neutral = excluded.is_neutral
"""

# INSERT OR REPLACE troca a linha inteira quando a chave (jogo + time) já existe.
SQL_TIME_NO_JOGO = """
    INSERT OR REPLACE INTO team_games (
        game_id, team_id, is_home, won, minutes, pts, fgm, fga, fg3m, fg3a,
        ftm, fta, oreb, dreb, reb, ast, stl, blk, tov, pf, plus_minus
    ) VALUES (
        :game_id, :team_id, :is_home, :won, :minutes, :pts, :fgm, :fga, :fg3m, :fg3a,
        :ftm, :fta, :oreb, :dreb, :reb, :ast, :stl, :blk, :tov, :pf, :plus_minus
    )
"""


def buscar_temporada(temporada):
    """Baixa uma temporada, tentando de novo se a chamada falhar."""
    for tentativa in range(1, MAXIMO_TENTATIVAS + 1):
        try:
            resposta = leaguegamelog.LeagueGameLog(
                season=temporada,
                season_type_all_star="Regular Season",
                timeout=TEMPO_LIMITE_SEGUNDOS,
            )
            return resposta.get_data_frames()[0]
        # ValueError cobre uma resposta que não veio no formato JSON esperado.
        except (requests.exceptions.RequestException, ValueError) as erro:
            if tentativa == MAXIMO_TENTATIVAS:
                raise
            espera = PAUSA_SEGUNDOS * 2**tentativa  # 6 s e depois 12 s
            print(f"  Tentativa {tentativa} falhou ({erro}). Nova tentativa em {espera} s.")
            time.sleep(espera)


def preparar_tabelas(jogos, temporada):
    """Separa a tabela da API nos formatos das tabelas games e team_games."""
    # "LAL vs. GSW" indica mandante e "GSW @ LAL" indica visitante.
    # Em quadra neutra, os dois times vêm com "@", então a partida fica sem mandante.
    is_home = jogos["MATCHUP"].str.contains("vs.", regex=False).astype(int)
    mandantes_na_partida = is_home.groupby(jogos["GAME_ID"]).transform("sum")

    partidas = (
        jogos.assign(is_neutral=(mandantes_na_partida == 0).astype(int))[
            ["GAME_ID", "GAME_DATE", "is_neutral"]
        ]
        .drop_duplicates()
        .rename(columns={"GAME_ID": "game_id", "GAME_DATE": "game_date"})
        .assign(season=temporada)
    )

    times_no_jogo = jogos.rename(columns={"MIN": "minutes"}).rename(columns=str.lower)
    times_no_jogo["is_home"] = is_home
    times_no_jogo["won"] = (jogos["WL"] == "W").astype(int)

    return partidas.to_dict("records"), times_no_jogo.to_dict("records")


def salvar_temporada(conexao, partidas, times_no_jogo):
    """Grava tudo de uma vez: ou a temporada inteira entra, ou nada entra."""
    with conexao:
        conexao.executemany(SQL_JOGO, partidas)
        conexao.executemany(SQL_TIME_NO_JOGO, times_no_jogo)


def main():
    conexao = conectar()
    try:
        criar_tabelas(conexao)
        with conexao:
            conexao.executemany(SQL_TIME, teams.get_teams())

        for indice, temporada in enumerate(TEMPORADAS):
            if indice > 0:
                time.sleep(PAUSA_SEGUNDOS)

            print(f"Baixando {temporada}...")
            jogos = buscar_temporada(temporada)
            partidas, times_no_jogo = preparar_tabelas(jogos, temporada)
            salvar_temporada(conexao, partidas, times_no_jogo)
            print(f"  {len(partidas)} partidas salvas.")
    finally:
        conexao.close()


if __name__ == "__main__":
    main()
