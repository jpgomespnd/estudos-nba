"""Compara as previsões gravadas com os resultados que já estão no banco."""

import pandas as pd

from banco import conectar
from prever_jogos import CAMINHO_PREVISOES

SQL_RESULTADOS = "SELECT game_id, home_pts AS casa_pts, away_pts AS fora_pts, home_won AS casa_venceu FROM vw_jogos"


def main():
    if not CAMINHO_PREVISOES.exists():
        print("Ainda não há previsões. Rode prever_jogos.py.")
        return

    previsoes = pd.read_csv(CAMINHO_PREVISOES, dtype={"game_id": str})
    conexao = conectar()
    try:
        resultados = pd.read_sql_query(SQL_RESULTADOS, conexao)
    finally:
        conexao.close()

    jogos = previsoes.merge(resultados, on="game_id")
    pendentes = len(previsoes) - len(jogos)
    if jogos.empty:
        print(f"Nenhuma previsão com resultado ainda ({pendentes} aguardando).")
        return

    antes_do_jogo = jogos["feita_em"].str[:10] <= jogos["game_date"]
    if not antes_do_jogo.all():
        print(f"Aviso: {(~antes_do_jogo).sum()} previsões com data posterior ao jogo.")

    real = jogos["casa_venceu"]
    acerto_modelo = ((jogos["prob_casa"] >= 0.5).astype(int) == real).mean()
    acerto_mandante = real.mean()
    melhor_campanha = (jogos["casa_aproveitamento"] >= jogos["fora_aproveitamento"]).astype(int)
    acerto_campanha = (melhor_campanha == real).mean()
    erro_pts = pd.concat(
        [jogos["prev_casa_pts"] - jogos["casa_pts"], jogos["prev_fora_pts"] - jogos["fora_pts"]]
    ).abs().mean()

    print(f"Jogos conferidos: {len(jogos)} | aguardando resultado: {pendentes}\n")
    print(f"Acerto do modelo:           {100 * acerto_modelo:.1f}%")
    print(f"Mandante sempre vence:      {100 * acerto_mandante:.1f}%")
    print(f"Melhor campanha vence:      {100 * acerto_campanha:.1f}%")
    print(f"Erro médio de pontos/time:  {erro_pts:.1f}\n")

    jogos["previsto"] = jogos["prev_casa_pts"].round().astype(int).astype(str) + " x " + jogos["prev_fora_pts"].round().astype(int).astype(str)
    jogos["real"] = jogos["casa_pts"].astype(str) + " x " + jogos["fora_pts"].astype(str)
    jogos["acertou"] = ((jogos["prob_casa"] >= 0.5).astype(int) == real).map({True: "sim", False: "não"})
    jogos["jogo"] = jogos["casa"] + " x " + jogos["fora"]
    print(jogos.sort_values("game_date").tail(15)[["game_date", "jogo", "previsto", "real", "acertou"]].to_string(index=False))


if __name__ == "__main__":
    main()
