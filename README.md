# Previsão de jogos da NBA

Coleta dados da NBA com a `nba_api`, guarda em SQLite e usa modelos de machine learning para prever o vencedor e o placar dos próximos jogos. As previsões ficam registradas antes de cada partida e depois são comparadas com o resultado real.

## Como rodar

Windows, Python 3.12:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

.venv\Scripts\python.exe scripts\coletar_jogos.py       # atualiza o banco
.venv\Scripts\python.exe scripts\validar_dados.py       # checagens de consistência
.venv\Scripts\python.exe scripts\prever_jogos.py        # prevê os próximos 7 dias
.venv\Scripts\python.exe scripts\conferir_previsoes.py  # compara com os resultados
```

`treinar_modelo.py` mostra a avaliação do modelo nas temporadas 2024-25 e 2025-26.

## Dados

Temporadas regulares de 2021-22 até a atual (2026-27, em andamento).

| Tabela | Conteúdo |
|---|---|
| `teams` | Times |
| `games` | Partidas |
| `team_games` | Estatísticas de cada time em cada partida |
| `calendario` | Jogos da temporada atual, inclusive os que ainda vão acontecer |
| `vw_jogos` | Mandante e visitante na mesma linha |

O banco fica em `data/` e não é versionado. As previsões ficam em `previsoes/previsoes.csv`, que é versionado, porque não podem ser refeitas depois do jogo.

Jogos em quadra neutra ficam fora do modelo. Antes de 2024-25 a API não os identifica, então alguns podem aparecer com mandante nominal.

## Modelo

Cada time é descrito só por jogos anteriores à partida, na mesma temporada: aproveitamento, ataque e defesa por 100 posses, ritmo, saldo dos últimos 10 jogos e dias de descanso. Regressão logística para o vencedor e Ridge para o placar.

Avaliação com treino em 2021-22 a 2023-24 e teste em 2024-25 e 2025-26 (2.294 partidas):

| | Acerto do vencedor |
|---|---|
| Mandante sempre vence | 55,1% |
| Melhor campanha vence | 66,3% |
| Modelo | 67,0% |

Erro médio do placar: 9,5 pontos por time.

## Próximos passos

- [x] Modelo de vencedor e placar
- [x] Previsão dos próximos jogos e conferência dos resultados
- [ ] Usar a temporada anterior no começo de cada temporada
- [ ] Painel de acompanhamento dos acertos
- [ ] Previsão de pontos, rebotes e assistências por jogador

## Autor

João Pedro, estudante de Sistemas de Informação na CESAR School.
