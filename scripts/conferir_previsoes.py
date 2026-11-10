"""Compara as previsões gravadas com os resultados que já estão no banco."""

import pandas as pd

from banco import conectar
from prever_jogos import CAMINHO_PREVISOES, ler_previsoes
from variaveis import montar_partidas

COLUNAS_RESULTADO = [
    "game_id", "casa_pts", "fora_pts", "casa_venceu", "casa_aproveitamento", "fora_aproveitamento",
]


def main():
    if not CAMINHO_PREVISOES.exists():
        print("Ainda não há previsões. Rode prever_jogos.py.")
        return

    previsoes = ler_previsoes()
    conexao = conectar()
    try:
        resultados = montar_partidas(conexao)[COLUNAS_RESULTADO]
    finally:
        conexao.close()

    jogos = previsoes.merge(resultados, on="game_id")
    pendentes = len(previsoes) - len(jogos)
    if jogos.empty:
        print(f"Nenhuma previsão com resultado ainda ({pendentes} aguardando).")
        return

    real = jogos["casa_venceu"]
    acertou = (jogos["prob_casa"] >= 0.5).astype(int) == real
    melhor_campanha = (jogos["casa_aproveitamento"] >= jogos["fora_aproveitamento"]).astype(int)
    erro_pts = pd.concat(
        [jogos["pontos_previstos_casa"] - jogos["casa_pts"], jogos["pontos_previstos_fora"] - jogos["fora_pts"]]
    ).abs().mean()

    print(f"Jogos conferidos: {len(jogos)} | aguardando resultado: {pendentes}\n")
    print(f"Acerto do modelo:           {100 * acertou.mean():.1f}%")
    print(f"Mandante sempre vence:      {100 * real.mean():.1f}%")
    print(f"Melhor campanha vence:      {100 * (melhor_campanha == real).mean():.1f}%")
    print(f"Erro médio de pontos/time:  {erro_pts:.1f}\n")

    jogos["jogo"] = jogos["casa"] + " x " + jogos["fora"]
    jogos["previsto"] = jogos["pontos_previstos_casa"].astype(str) + " x " + jogos["pontos_previstos_fora"].astype(str)
    jogos["real"] = jogos["casa_pts"].astype(str) + " x " + jogos["fora_pts"].astype(str)
    jogos["acertou"] = acertou.map({True: "sim", False: "não"})
    colunas = ["data", "jogo", "chance_vitoria_casa", "chance_vitoria_fora", "previsto", "real", "acertou"]
    print(jogos.sort_values("data").tail(15)[colunas].to_string(index=False))


if __name__ == "__main__":
    main()
