"""Confere se a nba_api responde nesta máquina e se os dados fazem sentido.

Como rodar, a partir da pasta do projeto:
    .venv\\Scripts\\python.exe scripts\\testar_api.py
"""

import time

from nba_api.stats.endpoints import leaguegamelog
from nba_api.stats.static import teams

TEMPORADAS = ["2024-25", "2025-26"]
PAUSA_SEGUNDOS = 2  # espera entre as chamadas, para respeitar o limite da API
TEMPO_LIMITE_SEGUNDOS = 30  # desiste se o servidor demorar mais que isso


def buscar_jogos(temporada):
    """Baixa os jogos da temporada regular e devolve uma tabela do pandas."""
    resposta = leaguegamelog.LeagueGameLog(
        season=temporada,
        season_type_all_star="Regular Season",
        timeout=TEMPO_LIMITE_SEGUNDOS,
    )
    return resposta.get_data_frames()[0]


def main():
    # Esta lista vem instalada com a biblioteca, então não usa a internet.
    print(f"Times na lista local: {len(teams.get_teams())}")

    for indice, temporada in enumerate(TEMPORADAS):
        # Pausa antes de toda chamada, menos a primeira.
        if indice > 0:
            time.sleep(PAUSA_SEGUNDOS)

        jogos = buscar_jogos(temporada)

        # A API devolve uma linha por time, ou seja, duas linhas por partida.
        linhas_por_jogo = jogos.groupby("GAME_ID").size()

        print(f"\nTemporada {temporada}")
        print(f"  Linhas: {len(jogos)}")
        print(f"  Partidas: {jogos['GAME_ID'].nunique()}")
        print(f"  Times: {jogos['TEAM_ID'].nunique()}")
        print(f"  Período: {jogos['GAME_DATE'].min()} a {jogos['GAME_DATE'].max()}")
        print(f"  Toda partida tem 2 linhas? {(linhas_por_jogo == 2).all()}")

    # Mostra só as colunas mais úteis da última temporada baixada.
    colunas = ["GAME_DATE", "MATCHUP", "WL", "PTS"]
    print("\nExemplo de linhas:")
    print(jogos[colunas].head(4).to_string(index=False))


if __name__ == "__main__":
    main()
