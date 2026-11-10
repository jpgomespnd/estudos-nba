"""Prevê os próximos jogos da temporada atual e grava em previsoes/previsoes.csv.

Rode coletar_jogos.py antes, para usar os resultados mais recentes.
Uso: prever_jogos.py [dias]  (padrão: 7)
"""

import sys
from datetime import date, timedelta

import pandas as pd

from banco import RAIZ_DO_PROJETO, conectar
from temporadas import TEMPORADA_ATUAL
from treinar_modelo import treinar
from variaveis import (
    DESCANSO_MAXIMO,
    MIN_JOGOS_ANTES,
    VARIAVEIS_MODELO,
    carregar_time_no_jogo,
    estado_atual,
    montar_partidas,
)

DIAS_PADRAO = 7
CAMINHO_PREVISOES = RAIZ_DO_PROJETO / "previsoes" / "previsoes.csv"
COLUNAS_CSV = [
    "game_id", "data", "casa", "fora",
    "chance_vitoria_casa", "pontos_previstos_casa",
    "chance_vitoria_fora", "pontos_previstos_fora",
]

SQL_PROXIMOS = """
    SELECT c.game_id, c.season, c.game_date,
           c.home_team_id AS casa_team_id, c.away_team_id AS fora_team_id,
           casa.abbreviation AS casa, fora.abbreviation AS fora
    FROM calendario AS c
    JOIN teams AS casa ON casa.team_id = c.home_team_id
    JOIN teams AS fora ON fora.team_id = c.away_team_id
    WHERE c.season = :temporada AND c.status = 1 AND c.is_neutral = 0
      AND c.game_date BETWEEN :inicio AND :fim
    ORDER BY c.game_date, c.game_id
"""

SQL_JOGOS_DO_TIME = """
    SELECT game_id, game_date, home_team_id AS team_id FROM calendario WHERE season = :temporada
    UNION ALL
    SELECT game_id, game_date, away_team_id FROM calendario WHERE season = :temporada
"""

SQL_DESATUALIZADOS = """
    SELECT COUNT(*) FROM calendario
    WHERE season = :temporada AND status <> 3 AND game_date < :hoje
"""


def descanso_pelo_calendario(conexao, temporada):
    jogos = pd.read_sql_query(
        SQL_JOGOS_DO_TIME, conexao, params={"temporada": temporada}, parse_dates=["game_date"]
    ).sort_values(["team_id", "game_date"])
    dias = jogos.groupby("team_id")["game_date"].diff().dt.days
    jogos["descanso"] = dias.fillna(DESCANSO_MAXIMO).clip(upper=DESCANSO_MAXIMO)
    return jogos.set_index(["game_id", "team_id"])["descanso"]


def montar_proximos(conexao, df, inicio, fim):
    proximos = pd.read_sql_query(
        SQL_PROXIMOS,
        conexao,
        params={"temporada": TEMPORADA_ATUAL, "inicio": inicio.isoformat(), "fim": fim.isoformat()},
    )
    estado = estado_atual(df, TEMPORADA_ATUAL)
    descanso = descanso_pelo_calendario(conexao, TEMPORADA_ATUAL)

    for lado in ("casa", "fora"):
        proximos = proximos.merge(
            estado.add_prefix(f"{lado}_"), left_on=f"{lado}_team_id", right_index=True, how="left"
        )
        chaves = pd.MultiIndex.from_arrays([proximos["game_id"], proximos[f"{lado}_team_id"]])
        proximos[f"{lado}_descanso"] = descanso.reindex(chaves).to_numpy()
    return proximos


def em_porcentagem(probabilidade):
    return (100 * probabilidade).map("{:.1f}%".format)


def formatar(proximos, prob_casa, pontos):
    return pd.DataFrame(
        {
            "game_id": proximos["game_id"],
            "data": proximos["game_date"],
            "casa": proximos["casa"],
            "fora": proximos["fora"],
            "chance_vitoria_casa": em_porcentagem(prob_casa),
            "pontos_previstos_casa": pontos[:, 0].round().astype(int),
            "chance_vitoria_fora": em_porcentagem(1 - prob_casa),
            "pontos_previstos_fora": pontos[:, 1].round().astype(int),
        }
    )


def ler_previsoes():
    previsoes = pd.read_csv(CAMINHO_PREVISOES, dtype={"game_id": str})
    previsoes["prob_casa"] = previsoes["chance_vitoria_casa"].str.rstrip("%").astype(float) / 100
    return previsoes


def atualizar_csv(novas):
    if CAMINHO_PREVISOES.exists():
        antigas = pd.read_csv(CAMINHO_PREVISOES, dtype={"game_id": str})
        # Jogos ainda não iniciados recebem a previsão mais recente.
        antigas = antigas[~antigas["game_id"].isin(novas["game_id"])]
        novas = pd.concat([antigas, novas])
    CAMINHO_PREVISOES.parent.mkdir(exist_ok=True)
    novas.sort_values(["data", "game_id"])[COLUNAS_CSV].to_csv(CAMINHO_PREVISOES, index=False)


def main():
    dias = int(sys.argv[1]) if len(sys.argv) > 1 else DIAS_PADRAO
    hoje = date.today()

    conexao = conectar()
    try:
        desatualizados = conexao.execute(
            SQL_DESATUALIZADOS, {"temporada": TEMPORADA_ATUAL, "hoje": hoje.isoformat()}
        ).fetchone()[0]
        if desatualizados:
            print(f"Aviso: {desatualizados} jogos passados sem resultado no banco. Rode coletar_jogos.py.\n")
        partidas = montar_partidas(conexao)
        df = carregar_time_no_jogo(conexao)
        proximos = montar_proximos(conexao, df, hoje, hoje + timedelta(days=dias))
    finally:
        conexao.close()

    if proximos.empty:
        print(f"Nenhum jogo agendado nos próximos {dias} dias.")
        return

    pouco_historico = (proximos["casa_jogos_antes"].fillna(0) < MIN_JOGOS_ANTES) | (
        proximos["fora_jogos_antes"].fillna(0) < MIN_JOGOS_ANTES
    )
    if pouco_historico.any():
        print(f"{pouco_historico.sum()} jogos ignorados: time com menos de {MIN_JOGOS_ANTES} jogos.")
    proximos = proximos[~pouco_historico].copy()

    vencedor, placar = treinar(partidas)
    prob_casa = pd.Series(vencedor.predict_proba(proximos[VARIAVEIS_MODELO])[:, 1], index=proximos.index)
    previsoes = formatar(proximos, prob_casa, placar.predict(proximos[VARIAVEIS_MODELO]))
    atualizar_csv(previsoes)

    print(f"Previsões de {hoje} a {hoje + timedelta(days=dias)}:\n")
    print(previsoes.drop(columns="game_id").to_string(index=False))
    print(f"\n{len(previsoes)} previsões gravadas em {CAMINHO_PREVISOES.relative_to(RAIZ_DO_PROJETO)}")


if __name__ == "__main__":
    main()
