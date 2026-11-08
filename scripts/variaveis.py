"""Variáveis do modelo. Cada partida usa só jogos anteriores a ela."""

import pandas as pd

MIN_JOGOS_ANTES = 5
JANELA_RECENTE = 10
DESCANSO_MAXIMO = 7

VARIAVEIS_DO_TIME = [
    "jogos_antes",
    "aproveitamento",
    "pts_media",
    "ataque",  # pontos marcados a cada 100 posses
    "defesa",  # pontos sofridos a cada 100 posses
    "ritmo",  # posses a cada 48 minutos
    "saldo_recente",
    "descanso",
]

_USADAS_NO_MODELO = ["aproveitamento", "ataque", "defesa", "ritmo", "saldo_recente", "descanso"]
VARIAVEIS_MODELO = [f"{lado}_{nome}" for lado in ("casa", "fora") for nome in _USADAS_NO_MODELO]

SQL_TIME_NO_JOGO = """
    SELECT
        g.game_id, g.season, g.game_date, g.is_neutral,
        t.team_id, t.is_home, t.won, t.minutes, t.pts,
        t.fga, t.oreb, t.tov, t.fta,
        o.pts  AS opp_pts,
        o.fga  AS opp_fga,
        o.oreb AS opp_oreb,
        o.tov  AS opp_tov,
        o.fta  AS opp_fta
    FROM team_games AS t
    JOIN team_games AS o ON o.game_id = t.game_id AND o.team_id <> t.team_id
    JOIN games AS g ON g.game_id = t.game_id
"""

_SOMAS = ["pts", "opp_pts", "posses", "minutos_jogo", "won"]


def posses(fga, oreb, tov, fta):
    return fga - oreb + tov + 0.44 * fta


def carregar_time_no_jogo(conexao):
    df = pd.read_sql_query(SQL_TIME_NO_JOGO, conexao, parse_dates=["game_date"])
    df["posses"] = (
        posses(df["fga"], df["oreb"], df["tov"], df["fta"])
        + posses(df["opp_fga"], df["opp_oreb"], df["opp_tov"], df["opp_fta"])
    ) / 2
    df["minutos_jogo"] = df["minutes"] / 5
    return df.sort_values(["team_id", "game_date"]).reset_index(drop=True)


def historico_do_time(df):
    grupo = df.groupby(["team_id", "season"])
    antes = grupo[_SOMAS].cumsum() - df[_SOMAS]  # tira o próprio jogo
    jogos_antes = grupo.cumcount()
    recente = grupo[["pts", "opp_pts", "posses"]].transform(
        lambda serie: serie.shift(1).rolling(JANELA_RECENTE, min_periods=1).sum()
    )
    descanso = grupo["game_date"].diff().dt.days

    return pd.DataFrame(
        {
            "game_id": df["game_id"],
            "team_id": df["team_id"],
            "jogos_antes": jogos_antes,
            "aproveitamento": antes["won"] / jogos_antes,
            "pts_media": antes["pts"] / jogos_antes,
            "ataque": 100 * antes["pts"] / antes["posses"],
            "defesa": 100 * antes["opp_pts"] / antes["posses"],
            "ritmo": 48 * antes["posses"] / antes["minutos_jogo"],
            "saldo_recente": 100 * (recente["pts"] - recente["opp_pts"]) / recente["posses"],
            "descanso": descanso.fillna(DESCANSO_MAXIMO).clip(upper=DESCANSO_MAXIMO),
        }
    )


def estado_atual(df, temporada):
    """Resumo de cada time com todos os jogos já disputados na temporada.

    Acrescenta um jogo fictício zerado depois do último jogo de cada time e usa
    historico_do_time; assim as fórmulas ficam num lugar só. O descanso fica de fora,
    porque depende da data do jogo a prever.
    """
    atual = df[df["season"] == temporada]
    ficticio = atual.groupby("team_id").tail(1).copy()
    ficticio[_SOMAS] = 0
    ficticio["game_id"] = "ficticio"
    ficticio["game_date"] += pd.Timedelta(days=1)

    juntos = pd.concat([atual, ficticio]).sort_values(["team_id", "game_date"]).reset_index(drop=True)
    resumo = historico_do_time(juntos)
    return resumo[resumo["game_id"] == "ficticio"].drop(columns=["game_id", "descanso"]).set_index("team_id")


def _lado(base, prefixo):
    colunas = ["game_id", "team_id", "pts", "won", *VARIAVEIS_DO_TIME]
    return base[colunas].rename(columns=lambda c: c if c == "game_id" else f"{prefixo}_{c}")


def montar_partidas(conexao):
    df = carregar_time_no_jogo(conexao)
    base = df[["game_id", "season", "game_date", "is_neutral", "is_home", "team_id", "pts", "won"]]
    base = base.merge(historico_do_time(df), on=["game_id", "team_id"])

    base = base[base["is_neutral"] == 0]
    casa = base[base["is_home"] == 1]
    fora = base[base["is_home"] == 0]

    partidas = (
        casa[["game_id", "season", "game_date"]]
        .merge(_lado(casa, "casa"), on="game_id")
        .merge(_lado(fora, "fora").drop(columns="fora_won"), on="game_id")
        .rename(columns={"casa_won": "casa_venceu"})
    )

    com_historico = (partidas["casa_jogos_antes"] >= MIN_JOGOS_ANTES) & (
        partidas["fora_jogos_antes"] >= MIN_JOGOS_ANTES
    )
    return partidas[com_historico].sort_values("game_date").reset_index(drop=True)
