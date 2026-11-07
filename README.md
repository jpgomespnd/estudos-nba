# Previsão de jogos da NBA

Projeto de estudo em ciência de dados: coletar dados da NBA, guardá-los em um banco SQL e treinar modelos de machine learning para prever o vencedor e o placar das partidas, comparando depois as previsões com os resultados reais.

> **Status:** em andamento. O banco de dados e a coleta estão prontos e validados. Ainda não há modelo nem resultados de previsão.

## Como rodar

No Windows, com Python 3.12, a partir da pasta do projeto:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe scripts\testar_api.py
.venv\Scripts\python.exe scripts\coletar_jogos.py
.venv\Scripts\python.exe scripts\validar_dados.py
```

O banco é gerado em `data/nba.db` e não vai para o repositório, porque os scripts conseguem recriá-lo.

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

## Regras do projeto

- **Execução local:** a `nba_api` tem limite de requisições e costuma bloquear serviços de nuvem, então tudo roda na máquina local, com pausas entre as chamadas.

## Etapas planejadas

- [ ] **(a) Vencedor e placar:** modelo treinado com temporadas passadas, usando estatísticas de time (ataque, defesa, ritmo, mando de quadra e dias de descanso).
- [ ] **(b) Jogos futuros:** previsão das próximas partidas, com um painel que acompanha os acertos.
- [ ] **(c) Box score por jogador:** previsão de pontos, rebotes e assistências, usando defesa contra posição e matchups.

## Tecnologias previstas

Python, `nba_api`, SQL e bibliotecas de machine learning.

## Autor

João Pedro, estudante de Sistemas de Informação na CESAR School.
