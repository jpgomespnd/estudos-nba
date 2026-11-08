# Previsão de jogos da NBA

Projeto de estudo em ciência de dados: coletar dados da NBA, guardá-los em um banco SQL e treinar modelos de machine learning para prever o vencedor e o placar das partidas, comparando depois as previsões com os resultados reais.

> **Status:** em andamento. Banco, coleta e validação prontos. A primeira versão do modelo de vencedor e placar (etapa a) acerta 67% dos vencedores no teste, contra 55% de "o mandante sempre vence".

## Como rodar

No Windows, com Python 3.12, a partir da pasta do projeto:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe scripts\testar_api.py
.venv\Scripts\python.exe scripts\coletar_jogos.py
.venv\Scripts\python.exe scripts\validar_dados.py
.venv\Scripts\python.exe scripts\treinar_modelo.py
```

Para estudar a etapa (a) passo a passo, abra o notebook [01_modelo_vencedor_placar.ipynb](notebooks/01_modelo_vencedor_placar.ipynb) com `.venv\Scripts\jupyter.exe lab` e rode as células em ordem.

O banco é gerado em `data/nba.db` e as previsões do teste em `data/previsoes_teste.csv`. Nenhum dos dois vai para o repositório, porque os scripts conseguem recriá-los.

## Dados

Temporadas regulares de 2021-22 a 2025-26: 6.150 partidas, guardadas em SQLite.

| Tabela | Conteúdo |
|---|---|
| `teams` | Os 30 times |
| `games` | Uma linha por partida |
| `team_games` | Uma linha por time em cada partida, com as estatísticas do jogo |
| `vw_jogos` | Visão com mandante e visitante na mesma linha |

**Limitação conhecida:** em 10 partidas de 2024-25 e 2025-26, a API não aponta mandante, e elas ficam marcadas com `is_neutral = 1`. Nas temporadas anteriores nenhuma partida vem assim, então jogos disputados em quadra neutra podem aparecer com um mandante apenas nominal.

## Objetivos

- Prever o vencedor e o placar de cada jogo.
- Medir a diferença de pontos, para cada time, entre o placar previsto e o placar real.
- Verificar se o modelo supera uma referência simples, como "o time da casa vence".

## Modelo de vencedor e placar (etapa a)

**Variáveis** ([variaveis.py](scripts/variaveis.py)): para cada partida, cada time é resumido só pelos jogos anteriores a ela na mesma temporada. Entram aproveitamento, ataque e defesa (pontos a cada 100 posses), ritmo (posses a cada 48 minutos), saldo nos últimos 10 jogos e dias de descanso. Partidas em que algum time tem menos de 5 jogos na temporada ficam de fora, assim como as de quadra neutra. Um teste confirmou que apagar os jogos posteriores a uma data não muda as variáveis dos jogos até ela, ou seja, não há vazamento de dados.

**Modelos** ([treinar_modelo.py](scripts/treinar_modelo.py)): regressão logística para a chance de vitória do mandante e regressão Ridge para os pontos de cada time. Treino com 2021-22 a 2023-24 (3.452 partidas) e teste com 2024-25 e 2025-26 (2.294 partidas).

| Teste (2.294 partidas) | Resultado |
|---|---|
| Acerto do vencedor: mandante sempre vence | 55,1% |
| Acerto do vencedor: melhor campanha vence | 66,3% |
| Acerto do vencedor: modelo | 67,0% |
| Log loss: taxa fixa do mandante / modelo | 0,688 / 0,605 |
| Erro médio de pontos por time: média do time / modelo | 10,0 / 9,5 pt |
| Erro médio no saldo da partida: modelo | 11,3 pt |

O modelo supera as duas referências, mas a vantagem sobre "melhor campanha vence" ainda é pequena (0,7 ponto percentual).

## Regras do projeto

- **Execução local:** a `nba_api` tem limite de requisições e costuma bloquear serviços de nuvem, então tudo roda na máquina local, com pausas entre as chamadas.

## Etapas planejadas

- [x] **(a) Vencedor e placar:** modelo treinado com temporadas passadas, usando estatísticas de time (ataque, defesa, ritmo, mando de quadra e dias de descanso). Primeira versão pronta; dá para melhorar.
- [ ] **(b) Jogos futuros:** previsão das próximas partidas, com um painel que acompanha os acertos.
- [ ] **(c) Box score por jogador:** previsão de pontos, rebotes e assistências, usando defesa contra posição e matchups.

## Tecnologias previstas

Python, `nba_api`, SQLite, pandas e scikit-learn.

## Autor

João Pedro, estudante de Sistemas de Informação na CESAR School.
