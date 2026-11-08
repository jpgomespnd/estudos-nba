"""Baixa jogos de times e jogadores, playoffs e elencos, e guarda no banco SQLite.

Pode ser rodado de novo sem duplicar nada, porque as linhas são atualizadas.
Os elencos já salvos não são baixados de novo, então uma coleta interrompida
continua de onde parou.

Como rodar, a partir da pasta do projeto:
    .venv\\Scripts\\python.exe scripts\\coletar_jogos.py
"""

import time

import requests
from nba_api.stats.endpoints import commonteamroster, leaguegamelog
from nba_api.stats.static import teams

from banco import conectar, criar_tabelas

TEMPORADAS = ["2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]
TIPOS_DE_TEMPORADA = ["Regular Season", "Playoffs"]
PAUSA_SEGUNDOS = 3
TEMPO_LIMITE_SEGUNDOS = 60
MAXIMO_TENTATIVAS = 3

COLUNAS_ESTATISTICAS = [
    "minutes", "pts", "fgm", "fga", "fg3m", "fg3a", "ftm", "fta", "oreb",
    "dreb", "reb", "ast", "stl", "blk", "tov", "pf", "plus_minus",
]
LISTA_COLUNAS = ", ".join(COLUNAS_ESTATISTICAS)
LISTA_PARAMETROS = ", ".join(f":{coluna}" for coluna in COLUNAS_ESTATISTICAS)

SQL_TIME = """
    INSERT INTO teams (team_id, abbreviation, full_name)
    VALUES (:id, :abbreviation, :full_name)
    ON CONFLICT (team_id) DO UPDATE SET
        abbreviation = excluded.abbreviation,
        full_name = excluded.full_name
"""

SQL_JOGO = """
    INSERT INTO games (game_id, season, season_type, game_date, is_neutral)
    VALUES (:game_id, :season, :season_type, :game_date, :is_neutral)
    ON CONFLICT (game_id) DO UPDATE SET
        season = excluded.season,
        season_type = excluded.season_type,
        game_date = excluded.game_date,
        is_neutral = excluded.is_neutral
"""

# INSERT OR REPLACE troca a linha inteira quando a chave já existe.
SQL_TIME_NO_JOGO = f"""
    INSERT OR REPLACE INTO team_games (game_id, team_id, is_home, won, {LISTA_COLUNAS})
    VALUES (:game_id, :team_id, :is_home, :won, {LISTA_PARAMETROS})
"""

SQL_JOGADOR = """
    INSERT INTO players (player_id, name) VALUES (:player_id, :name)
    ON CONFLICT (player_id) DO UPDATE SET name = excluded.name
"""

# Usado pelos elencos: só cria o jogador se ele ainda não existir.
SQL_JOGADOR_SE_NOVO = """
    INSERT INTO players (player_id, name) VALUES (:player_id, :name)
    ON CONFLICT (player_id) DO NOTHING
"""

SQL_JOGADOR_NO_JOGO = f"""
    INSERT OR REPLACE INTO player_games (game_id, player_id, team_id, {LISTA_COLUNAS})
    VALUES (:game_id, :player_id, :team_id, {LISTA_PARAMETROS})
"""

SQL_ELENCO = """
    INSERT OR REPLACE INTO rosters (season, team_id, player_id, position, height_in, weight_lb)
    VALUES (:season, :team_id, :player_id, :position, :height_in, :weight_lb)
"""

_ultima_chamada = 0.0


def chamar_api(criar_requisicao):
    """Faz uma chamada à API com pausa mínima entre chamadas e novas tentativas.

    criar_requisicao é uma função sem argumentos que faz a chamada e devolve
    a primeira tabela da resposta.
    """
    global _ultima_chamada
    for tentativa in range(1, MAXIMO_TENTATIVAS + 1):
        # Garante pelo menos PAUSA_SEGUNDOS desde a chamada anterior.
        espera = PAUSA_SEGUNDOS - (time.monotonic() - _ultima_chamada)
        if espera > 0:
            time.sleep(espera)
        try:
            return criar_requisicao()
        # ValueError cobre uma resposta que não veio no formato JSON esperado.
        except (requests.exceptions.RequestException, ValueError) as erro:
            if tentativa == MAXIMO_TENTATIVAS:
                raise
            espera_extra = PAUSA_SEGUNDOS * 2**tentativa  # 6 s e depois 12 s
            print(f"  Tentativa {tentativa} falhou ({erro}). Nova tentativa em {espera_extra} s.")
            time.sleep(espera_extra)
        finally:
            _ultima_chamada = time.monotonic()


def baixar_log(temporada, tipo, de_jogadores):
    """Baixa o registro de jogos de times (T) ou de jogadores (P)."""
    return chamar_api(
        lambda: leaguegamelog.LeagueGameLog(
            season=temporada,
            season_type_all_star=tipo,
            player_or_team_abbreviation="P" if de_jogadores else "T",
            timeout=TEMPO_LIMITE_SEGUNDOS,
        ).get_data_frames()[0]
    )


def preparar_jogos_de_times(jogos, temporada, tipo):
    """Separa o log de times nos formatos das tabelas games e team_games."""
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
        .assign(season=temporada, season_type=tipo)
    )

    times_no_jogo = jogos.rename(columns={"MIN": "minutes"}).rename(columns=str.lower)
    times_no_jogo["is_home"] = is_home
    times_no_jogo["won"] = (jogos["WL"] == "W").astype(int)

    return partidas.to_dict("records"), times_no_jogo.to_dict("records")


def preparar_jogos_de_jogadores(jogos):
    """Separa o log de jogadores nos formatos das tabelas players e player_games."""
    jogadores = (
        jogos[["PLAYER_ID", "PLAYER_NAME"]]
        .drop_duplicates("PLAYER_ID")
        .rename(columns={"PLAYER_ID": "player_id", "PLAYER_NAME": "name"})
    )
    jogadores_no_jogo = jogos.rename(columns={"MIN": "minutes"}).rename(columns=str.lower)
    return jogadores.to_dict("records"), jogadores_no_jogo.to_dict("records")


def altura_em_polegadas(texto):
    """Converte a altura do formato "6-8" (pés-polegadas) para polegadas: 80."""
    try:
        pes, polegadas = str(texto).split("-")
        return int(pes) * 12 + int(polegadas)
    except ValueError:
        return None


def numero_ou_vazio(texto):
    """Converte para inteiro, ou devolve None quando o valor está vazio."""
    try:
        return int(texto)
    except (TypeError, ValueError):
        return None


def coletar_jogos(conexao, temporada, tipo):
    """Baixa e salva os jogos de times e de jogadores de uma temporada."""
    partidas, times_no_jogo = preparar_jogos_de_times(
        baixar_log(temporada, tipo, de_jogadores=False), temporada, tipo
    )
    jogadores, jogadores_no_jogo = preparar_jogos_de_jogadores(
        baixar_log(temporada, tipo, de_jogadores=True)
    )
    # Tudo de uma vez: ou a temporada inteira entra, ou nada entra.
    with conexao:
        conexao.executemany(SQL_JOGO, partidas)
        conexao.executemany(SQL_TIME_NO_JOGO, times_no_jogo)
        conexao.executemany(SQL_JOGADOR, jogadores)
        conexao.executemany(SQL_JOGADOR_NO_JOGO, jogadores_no_jogo)
    print(f"  {tipo}: {len(partidas)} partidas e {len(jogadores_no_jogo)} linhas de jogadores.")


def coletar_elencos(conexao, temporada):
    """Baixa o elenco de cada time que ainda não tem elenco salvo na temporada."""
    ja_salvos = {
        linha[0]
        for linha in conexao.execute(
            "SELECT DISTINCT team_id FROM rosters WHERE season = ?", (temporada,)
        )
    }
    faltando = [time_ for time_ in teams.get_teams() if time_["id"] not in ja_salvos]
    print(f"  Elencos: {len(ja_salvos)} já salvos, {len(faltando)} para baixar.")

    for time_ in faltando:
        elenco = chamar_api(
            lambda: commonteamroster.CommonTeamRoster(
                team_id=time_["id"], season=temporada, timeout=TEMPO_LIMITE_SEGUNDOS
            ).get_data_frames()[0]
        )
        linhas = [
            {
                "season": temporada,
                "team_id": time_["id"],
                "player_id": int(jogador["PLAYER_ID"]),
                "name": jogador["PLAYER"],
                "position": jogador["POSITION"] or None,
                "height_in": altura_em_polegadas(jogador["HEIGHT"]),
                "weight_lb": numero_ou_vazio(jogador["WEIGHT"]),
            }
            for jogador in elenco.to_dict("records")
        ]
        with conexao:
            conexao.executemany(SQL_JOGADOR_SE_NOVO, linhas)
            conexao.executemany(SQL_ELENCO, linhas)


def main():
    conexao = conectar()
    try:
        criar_tabelas(conexao)
        with conexao:
            conexao.executemany(SQL_TIME, teams.get_teams())

        for temporada in TEMPORADAS:
            print(f"Temporada {temporada}")
            for tipo in TIPOS_DE_TEMPORADA:
                coletar_jogos(conexao, temporada, tipo)
            coletar_elencos(conexao, temporada)
    finally:
        conexao.close()


if __name__ == "__main__":
    main()
