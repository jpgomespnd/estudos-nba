"""Monta as variáveis do modelo a partir do banco.

Regra principal: as variáveis de uma partida usam SÓ jogos anteriores a ela.
Usar o próprio jogo, ou jogos futuros, seria vazamento de dados: o modelo
pareceria ótimo no teste e erraria na hora de prever de verdade.
"""

import pandas as pd

MIN_JOGOS_ANTES = 5  # partidas em que algum time tem menos histórico que isso ficam de fora
JANELA_RECENTE = 10  # quantos jogos contam como "fase recente"
DESCANSO_MAXIMO = 7  # dias; mais que isso conta como 7

# Estatísticas que resumem cada time antes da partida.
VARIAVEIS_DO_TIME = [
    "jogos_antes",
    "aproveitamento",  # fração de vitórias
    "pts_media",  # pontos marcados por jogo
    "ataque",  # pontos marcados a cada 100 posses
    "defesa",  # pontos sofridos a cada 100 posses
    "ritmo",  # posses a cada 48 minutos
    "saldo_recente",  # ataque menos defesa nos últimos jogos
    "descanso",  # dias desde o jogo anterior
]

# O que o modelo recebe: as variáveis dos dois times, menos as que só servem de controle.
# "saldo" (ataque menos defesa) fica de fora porque o modelo já recebe as duas partes.
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


def posses(fga, oreb, tov, fta):
    """Estimativa usual de posses de bola de um time em uma partida."""
    return fga - oreb + tov + 0.44 * fta


def carregar_time_no_jogo(conexao):
    """Uma linha por time em cada partida, com os números do adversário ao lado."""
    df = pd.read_sql_query(SQL_TIME_NO_JOGO, conexao, parse_dates=["game_date"])
    # As posses dos dois times quase coincidem; a média reduz o erro da estimativa.
    df["posses"] = (
        posses(df["fga"], df["oreb"], df["tov"], df["fta"])
        + posses(df["opp_fga"], df["opp_oreb"], df["opp_tov"], df["opp_fta"])
    ) / 2
    df["minutos_jogo"] = df["minutes"] / 5  # "minutes" soma os 5 jogadores em quadra
    return df.sort_values(["team_id", "game_date"]).reset_index(drop=True)


def historico_do_time(df):
    """Para cada time em cada partida, resume os jogos ANTERIORES da mesma temporada."""
    grupo = df.groupby(["team_id", "season"])
    colunas = ["pts", "opp_pts", "posses", "minutos_jogo", "won"]

    # cumsum inclui o jogo atual; subtrair o próprio jogo deixa só o passado.
    antes = grupo[colunas].cumsum() - df[colunas]
    jogos_antes = grupo.cumcount()

    # Fase recente: soma dos últimos jogos, sem o atual (por isso o shift(1)).
    recente = grupo[["pts", "opp_pts", "posses"]].transform(
        lambda serie: serie.shift(1).rolling(JANELA_RECENTE, min_periods=1).sum()
    )

    # O primeiro jogo da temporada não tem anterior: conta como descanso máximo.
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


def _lado(base, prefixo):
    """Renomeia as colunas de um time para casa_... ou fora_..."""
    colunas = ["game_id", "team_id", "pts", "won", *VARIAVEIS_DO_TIME]
    return base[colunas].rename(columns=lambda c: c if c == "game_id" else f"{prefixo}_{c}")


def montar_partidas(conexao):
    """Uma linha por partida com mandante, com as variáveis dos dois times e o resultado."""
    df = carregar_time_no_jogo(conexao)
    base = df[["game_id", "season", "game_date", "is_neutral", "is_home", "team_id", "pts", "won"]]
    base = base.merge(historico_do_time(df), on=["game_id", "team_id"])

    # Quadra neutra não tem mandante, então não entra (ver README).
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


if __name__ == "__main__":
    from banco import conectar

    conexao = conectar()
    try:
        partidas = montar_partidas(conexao)
    finally:
        conexao.close()
    print(f"Partidas com histórico suficiente: {len(partidas)}")
    print(partidas.groupby("season").size().to_string())
    print("\nExemplo:")
    print(partidas[["game_date", *VARIAVEIS_MODELO[:3], "casa_pts", "fora_pts"]].tail(3).to_string(index=False))
