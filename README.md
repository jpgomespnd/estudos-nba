# Simulador de séries da NBA

Projeto de estudo em ciência de dados: coletar dados da NBA, guardá-los em um banco SQL e treinar modelos de machine learning para simular séries de playoffs, em melhor de 7 jogos, entre times reais de temporadas diferentes. Cada jogo simulado terá placar e box score por jogador.

> **Status:** em andamento. O banco com os jogos de times está pronto e validado. Ainda não há modelo nem simulação.

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

## Como a simulação vai funcionar

1. O usuário escolhe a temporada e o time mandante, que terá o mando de quadra na série.
2. Faz o mesmo para o visitante.
3. O sistema simula uma série em melhor de 7 jogos, com mando de quadra no formato 2-2-1-1-1.
4. Cada jogo mostra o placar e as estatísticas de cada jogador.
5. Rodando milhares de séries, o sistema estima a chance de vitória de cada time.

### Regras de elenco

- **Elenco:** o time como estava no fim da temporada regular. Cada jogador pertence ao time pelo qual fez seu último jogo.
- **Estatísticas:** só os jogos do jogador por esse time, porque minutos e função podem mudar após uma troca.
- **Lesões:** são ignoradas. Toda simulação usa a rotação ideal.
- **Rotação ideal:** os 9 jogadores com mais minutos por jogo, entre os que fizeram pelo menos 20 jogos pelo time. Os 5 primeiros são titulares.

## Como validar

Uma partida entre times de temporadas diferentes nunca aconteceu, então não há resultado real para comparar. Por isso o modelo será testado antes em situações reais:

- **Jogos de uma temporada guardada:** o modelo não vê esses jogos no treino e precisa superar a referência "o time da casa vence".
- **Séries reais de playoffs:** as séries simuladas são comparadas com as que aconteceram.

O confronto entre temporadas diferentes continua sendo uma extrapolação, e o site vai deixar isso claro.

## Regras do projeto

- **Execução local:** a `nba_api` tem limite de requisições e costuma bloquear serviços de nuvem, então tudo roda na máquina local, com pausas entre as chamadas.

## Fases

- [ ] **1. Jogadores, elencos e playoffs no banco**
- [ ] **2. Variáveis e modelo de placar**, testado em jogos reais
- [ ] **3. Overall e defesa por posição**, com dados defensivos da própria API
- [ ] **4. Simulador de séries em melhor de 7**, testado com séries reais
- [ ] **5. Box score por jogador**, somando exatamente o placar do time
- [ ] **6. API e site**, em que o usuário escolhe os times e vê a série

## Tecnologias

- **Em uso:** Python, `nba_api`, pandas e SQLite.
- **Previstas:** scikit-learn para o modelo, FastAPI para a API e React para o site.

## Autor

João Pedro, estudante de Sistemas de Informação na CESAR School.

Projeto de fã, sem vínculo com a NBA ou com seus times.
