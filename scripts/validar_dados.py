"""Confere se os dados do banco fazem sentido.

Cada regra é uma consulta que procura dados ERRADOS: se ela não devolve nenhuma
linha, a regra passou. O programa termina com erro se alguma regra falhar.

Como rodar, a partir da pasta do projeto:
    .venv\\Scripts\\python.exe scripts\\validar_dados.py
"""

import sys

from banco import conectar

CHECAGENS = {
    "Cada temporada regular tem 1230 partidas": """
        SELECT season FROM games
        WHERE season_type = 'Regular Season'
        GROUP BY season
        HAVING COUNT(*) <> 1230
    """,
    "Cada time joga 82 vezes por temporada regular": """
        SELECT g.season, t.team_id
        FROM team_games AS t
        JOIN games AS g ON g.game_id = t.game_id
        WHERE g.season_type = 'Regular Season'
        GROUP BY g.season, t.team_id
        HAVING COUNT(*) <> 82
    """,
    "Cada partida tem 2 times e o número certo de mandantes": """
        SELECT g.game_id
        FROM games AS g
        LEFT JOIN team_games AS t ON t.game_id = g.game_id
        GROUP BY g.game_id
        HAVING COUNT(t.team_id) <> 2
            OR COALESCE(SUM(t.is_home), 0) <> 1 - g.is_neutral
    """,
    "A vw_jogos traz toda partida que tem mandante": """
        SELECT g.game_id
        FROM games AS g
        LEFT JOIN vw_jogos AS v ON v.game_id = g.game_id
        WHERE g.is_neutral = 0 AND v.game_id IS NULL
    """,
    "Cada partida tem exatamente 1 vencedor": """
        SELECT game_id FROM team_games
        GROUP BY game_id
        HAVING SUM(won) <> 1
    """,
    "O vencedor marcou mais pontos": """
        SELECT vencedor.game_id
        FROM team_games AS vencedor
        JOIN team_games AS perdedor
          ON perdedor.game_id = vencedor.game_id AND perdedor.team_id <> vencedor.team_id
        WHERE vencedor.won = 1 AND vencedor.pts <= perdedor.pts
    """,
    "Os pontos batem com os arremessos": """
        SELECT game_id, team_id FROM team_games
        WHERE pts <> 2 * (fgm - fg3m) + 3 * fg3m + ftm
    """,
    "O total de rebotes bate com ofensivos + defensivos": """
        SELECT game_id, team_id FROM team_games
        WHERE reb <> oreb + dreb
    """,
    "O saldo do time bate com o placar": """
        SELECT casa.game_id
        FROM team_games AS casa
        JOIN team_games AS fora
          ON fora.game_id = casa.game_id AND fora.team_id <> casa.team_id
        WHERE casa.plus_minus <> casa.pts - fora.pts
    """,
    "Convertidos nunca passam de tentados": """
        SELECT game_id, team_id FROM team_games
        WHERE fgm > fga OR fg3m > fg3a OR ftm > fta OR fg3m > fgm
    """,
    "Toda partida dura 240 minutos ou mais": """
        SELECT game_id, team_id FROM team_games
        WHERE minutes < 240
    """,
    "As datas ficam dentro do período da temporada": """
        SELECT game_id FROM games
        WHERE game_date NOT BETWEEN substr(season, 1, 4) || '-10-01'
                                AND (CAST(substr(season, 1, 4) AS INTEGER) + 1) || '-06-30'
    """,
}


def executar_checagens(conexao):
    """Devolve um dicionário com o número de linhas erradas de cada regra."""
    return {
        nome: len(conexao.execute(consulta).fetchall())
        for nome, consulta in CHECAGENS.items()
    }


def mostrar_resumo(conexao):
    """Mostra números gerais e a referência simples de vitórias do mandante."""
    consulta = """
        SELECT
            g.season,
            COUNT(*),
            SUM(g.is_neutral),
            MIN(g.game_date),
            MAX(g.game_date),
            ROUND(AVG(v.home_pts + v.away_pts), 1),
            ROUND(100.0 * AVG(v.home_won), 1)
        FROM games AS g
        LEFT JOIN vw_jogos AS v ON v.game_id = g.game_id
        WHERE g.season_type = 'Regular Season'
        GROUP BY g.season
        ORDER BY g.season
    """
    print("\nTemporada | Partidas | Neutras | Início     | Fim        | Pontos/jogo | Mandante vence")
    for temporada, partidas, neutras, inicio, fim, pontos, mandante in conexao.execute(consulta):
        print(
            f"{temporada}   | {partidas}     | {neutras:<7} | {inicio} | {fim} | "
            f"{pontos:<11} | {mandante}%"
        )


def main():
    conexao = conectar()
    try:
        resultados = executar_checagens(conexao)
        for nome, erros in resultados.items():
            situacao = "OK" if erros == 0 else f"FALHOU ({erros} linhas erradas)"
            print(f"[{situacao}] {nome}")
        mostrar_resumo(conexao)
    finally:
        conexao.close()

    if any(resultados.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
