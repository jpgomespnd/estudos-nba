"""Confere se a nba_api responde nesta máquina."""

import time

from nba_api.stats.endpoints import leaguegamelog
from nba_api.stats.static import teams

TEMPORADAS = ["2024-25", "2025-26"]
PAUSA_SEGUNDOS = 2
TEMPO_LIMITE_SEGUNDOS = 30


def buscar_jogos(temporada):
    resposta = leaguegamelog.LeagueGameLog(
        season=temporada,
        season_type_all_star="Regular Season",
        timeout=TEMPO_LIMITE_SEGUNDOS,
    )
    return resposta.get_data_frames()[0]


def main():
    print(f"Times na lista local: {len(teams.get_teams())}")

    for indice, temporada in enumerate(TEMPORADAS):
        if indice > 0:
            time.sleep(PAUSA_SEGUNDOS)

        jogos = buscar_jogos(temporada)
        linhas_por_jogo = jogos.groupby("GAME_ID").size()

        print(f"\nTemporada {temporada}")
        print(f"  Linhas: {len(jogos)}")
        print(f"  Partidas: {jogos['GAME_ID'].nunique()}")
        print(f"  Times: {jogos['TEAM_ID'].nunique()}")
        print(f"  Período: {jogos['GAME_DATE'].min()} a {jogos['GAME_DATE'].max()}")
        print(f"  Toda partida tem 2 linhas? {(linhas_por_jogo == 2).all()}")

    print("\nExemplo de linhas:")
    print(jogos[["GAME_DATE", "MATCHUP", "WL", "PTS"]].head(4).to_string(index=False))


if __name__ == "__main__":
    main()
