"""Treina os modelos de vencedor e placar e avalia nas temporadas mais recentes."""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import log_loss, mean_absolute_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from banco import RAIZ_DO_PROJETO, conectar
from variaveis import VARIAVEIS_MODELO, montar_partidas

TEMPORADAS_TREINO = ["2021-22", "2022-23", "2023-24"]
TEMPORADAS_TESTE = ["2024-25", "2025-26"]
CAMINHO_PREVISOES = RAIZ_DO_PROJETO / "data" / "previsoes_teste.csv"

ACERTO = "Acerto do vencedor"
LOG_LOSS = "Log loss"
ERRO_PONTOS = "Erro médio de pontos por time"
ERRO_SALDO = "Erro médio no saldo"
FORMATOS = {
    ACERTO: lambda v: f"{100 * v:>9.1f}%",
    LOG_LOSS: lambda v: f"{v:>10.3f}",
    ERRO_PONTOS: lambda v: f"{v:>7.1f} pt",
    ERRO_SALDO: lambda v: f"{v:>7.1f} pt",
}


def treinar(treino):
    x = treino[VARIAVEIS_MODELO]
    vencedor = make_pipeline(StandardScaler(), LogisticRegression())
    vencedor.fit(x, treino["casa_venceu"])
    placar = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    placar.fit(x, treino[["casa_pts", "fora_pts"]])
    return vencedor, placar


def avaliar(jogos, taxa_mandante_treino):
    real = jogos["casa_venceu"]
    pts_reais = np.concatenate([jogos["casa_pts"], jogos["fora_pts"]])
    melhor_campanha = (jogos["casa_aproveitamento"] >= jogos["fora_aproveitamento"]).astype(int)
    placar_aponta_casa = (jogos["prev_casa_pts"] > jogos["prev_fora_pts"]).astype(int)
    taxa_fixa = np.full(len(jogos), taxa_mandante_treino)

    return {
        (ACERTO, "Mandante sempre vence"): real.mean(),
        (ACERTO, "Melhor campanha vence"): (melhor_campanha == real).mean(),
        (ACERTO, "Modelo de vencedor"): ((jogos["prob_casa"] >= 0.5).astype(int) == real).mean(),
        (ACERTO, "Modelo de placar"): (placar_aponta_casa == real).mean(),
        (LOG_LOSS, "Taxa fixa do mandante"): log_loss(real, taxa_fixa, labels=[0, 1]),
        (LOG_LOSS, "Modelo de vencedor"): log_loss(real, jogos["prob_casa"], labels=[0, 1]),
        (ERRO_PONTOS, "Média do time na temporada"): mean_absolute_error(
            pts_reais, np.concatenate([jogos["casa_pts_media"], jogos["fora_pts_media"]])
        ),
        (ERRO_PONTOS, "Modelo de placar"): mean_absolute_error(
            pts_reais, np.concatenate([jogos["prev_casa_pts"], jogos["prev_fora_pts"]])
        ),
        (ERRO_SALDO, "Modelo de placar"): mean_absolute_error(
            jogos["casa_pts"] - jogos["fora_pts"], jogos["prev_casa_pts"] - jogos["prev_fora_pts"]
        ),
    }


def mostrar(tabela, partidas_por_coluna):
    print(f"\n{'':<34}" + "".join(f"{c:>10}" for c in tabela.columns))
    print(f"{'Partidas':<34}" + "".join(f"{n:>10}" for n in partidas_por_coluna))
    for secao, formato in FORMATOS.items():
        print(secao)
        for nome, linha in tabela.loc[secao].iterrows():
            print(f"  {nome:<32}" + "".join(formato(v) for v in linha))


def main():
    conexao = conectar()
    try:
        partidas = montar_partidas(conexao)
    finally:
        conexao.close()

    treino = partidas[partidas["season"].isin(TEMPORADAS_TREINO)]
    teste = partidas[partidas["season"].isin(TEMPORADAS_TESTE)].copy()
    print(f"Treino: {len(treino)} partidas | Teste: {len(teste)} partidas")

    vencedor, placar = treinar(treino)
    teste["prob_casa"] = vencedor.predict_proba(teste[VARIAVEIS_MODELO])[:, 1]
    teste[["prev_casa_pts", "prev_fora_pts"]] = placar.predict(teste[VARIAVEIS_MODELO])

    taxa_mandante = treino["casa_venceu"].mean()
    grupos = {temporada: teste[teste["season"] == temporada] for temporada in TEMPORADAS_TESTE}
    grupos["Total"] = teste
    tabela = pd.DataFrame({nome: avaliar(jogos, taxa_mandante) for nome, jogos in grupos.items()})
    mostrar(tabela, [len(jogos) for jogos in grupos.values()])

    pesos = pd.Series(vencedor[-1].coef_[0], index=VARIAVEIS_MODELO).sort_values()
    print("\nPesos do modelo de vencedor:")
    print(pesos.round(2).to_string())

    CAMINHO_PREVISOES.parent.mkdir(parents=True, exist_ok=True)
    teste[
        ["game_id", "season", "game_date", "casa_team_id", "fora_team_id", "casa_pts", "fora_pts",
         "prev_casa_pts", "prev_fora_pts", "prob_casa", "casa_venceu"]
    ].round({"prev_casa_pts": 1, "prev_fora_pts": 1, "prob_casa": 3}).to_csv(
        CAMINHO_PREVISOES, index=False
    )


if __name__ == "__main__":
    main()
