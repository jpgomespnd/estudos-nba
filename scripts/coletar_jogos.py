"""Baixa os jogos da NBA e o calendário da temporada atual para o banco."""

import time

import pandas as pd
import requests
from nba_api.stats.endpoints import leaguegamelog, scheduleleaguev2
from nba_api.stats.static import teams

from banco import conectar, criar_tabelas
from temporadas import TEMPORADA_ATUAL, TEMPORADAS_COMPLETAS

PAUSA_SEGUNDOS = 3
TEMPO_LIMITE_SEGUNDOS = 30
MAXIMO_TENTATIVAS = 3
JOGO_ENCERRADO = 3

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

SQL_TIME_NO_JOGO = """
    INSERT OR REPLACE INTO team_games (
        game_id, team_id, is_home, won, minutes, pts, fgm, fga, fg3m, fg3a,
        ftm, fta, oreb, dreb, reb, ast, stl, blk, tov, pf, plus_minus
    ) VALUES (
        :game_id, :team_id, :is_home, :won, :minutes, :pts, :fgm, :fga, :fg3m, :fg3a,
        :ftm, :fta, :oreb, :dreb, :reb, :ast, :stl, :blk, :tov, :pf, :plus_minus
    )
"""

SQL_CALENDARIO = """
    INSERT INTO calendario (game_id, season, game_date, home_team_id, away_team_id, is_neutral, status)
    VALUES (:game_id, :season, :game_date, :home_team_id, :away_team_id, :is_neutral, :status)
    ON CONFLICT (game_id) DO UPDATE SET
        game_date = excluded.game_date,
        home_team_id = excluded.home_team_id,
        away_team_id = excluded.away_team_id,
        is_neutral = excluded.is_neutral,
        status = excluded.status
"""


def com_tentativas(chamada):
    for tentativa in range(1, MAXIMO_TENTATIVAS + 1):
        try:
            return chamada()
        except (requests.exceptions.RequestException, ValueError) as erro:
            if tentativa == MAXIMO_TENTATIVAS:
                raise
            espera = PAUSA_SEGUNDOS * 2**tentativa
            print(f"  Tentativa {tentativa} falhou ({erro}). Nova tentativa em {espera} s.")
            time.sleep(espera)


def buscar_temporada(temporada):
    return com_tentativas(
        lambda: leaguegamelog.LeagueGameLog(
            season=temporada,
            season_type_all_star="Regular Season",
            timeout=TEMPO_LIMITE_SEGUNDOS,
        ).get_data_frames()[0]
    )


def buscar_calendario(temporada):
    return com_tentativas(
        lambda: scheduleleaguev2.ScheduleLeagueV2(
            season=temporada, timeout=TEMPO_LIMITE_SEGUNDOS
        ).season_games.get_data_frame()
    )


def preparar_tabelas(jogos, temporada):
    # "LAL vs. GSW" = mandante, "GSW @ LAL" = visitante; em quadra neutra os dois vêm com "@".
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


def preparar_calendario(calendario, temporada, ids_dos_times):
    # Só temporada regular (ID "002...") e jogos com os dois times já definidos.
    calendario = calendario[
        calendario["gameId"].str.startswith("002")
        & calendario["homeTeam_teamId"].isin(ids_dos_times)
        & calendario["awayTeam_teamId"].isin(ids_dos_times)
    ]
    return pd.DataFrame(
        {
            "game_id": calendario["gameId"],
            "season": temporada,
            "game_date": calendario["gameDateEst"].str[:10],
            "home_team_id": calendario["homeTeam_teamId"],
            "away_team_id": calendario["awayTeam_teamId"],
            "is_neutral": calendario["isNeutral"].astype(int),
            "status": calendario["gameStatus"],
        }
    ).to_dict("records")


def salvar(conexao, partidas, times_no_jogo, calendario=()):
    with conexao:
        conexao.executemany(SQL_JOGO, partidas)
        conexao.executemany(SQL_TIME_NO_JOGO, times_no_jogo)
        conexao.executemany(SQL_CALENDARIO, calendario)


def main():
    conexao = conectar()
    try:
        criar_tabelas(conexao)
        lista_de_times = teams.get_teams()
        with conexao:
            conexao.executemany(SQL_TIME, lista_de_times)
        ids_dos_times = [time_["id"] for time_ in lista_de_times]

        for indice, temporada in enumerate([*TEMPORADAS_COMPLETAS, TEMPORADA_ATUAL]):
            if indice > 0:
                time.sleep(PAUSA_SEGUNDOS)
            print(f"Baixando {temporada}...")
            jogos = buscar_temporada(temporada)
            calendario = []

            if temporada == TEMPORADA_ATUAL:
                time.sleep(PAUSA_SEGUNDOS)
                calendario = preparar_calendario(buscar_calendario(temporada), temporada, ids_dos_times)
                # O registro de jogos também traz partidas em andamento: fica só o que terminou.
                encerrados = {j["game_id"] for j in calendario if j["status"] == JOGO_ENCERRADO}
                jogos = jogos[jogos["GAME_ID"].isin(encerrados)]

            partidas, times_no_jogo = preparar_tabelas(jogos, temporada)
            salvar(conexao, partidas, times_no_jogo, calendario)
            print(f"  {len(partidas)} partidas salvas.")
    finally:
        conexao.close()


if __name__ == "__main__":
    main()
