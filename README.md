# Previsão de jogos da NBA

Projeto de estudo em ciência de dados: coletar dados da NBA, guardá-los em um banco SQL e treinar modelos de machine learning para prever o vencedor e o placar das partidas, comparando depois as previsões com os resultados reais.

> **Status:** em início. Até agora, só a estrutura do repositório foi criada. Ainda não há código nem resultados.

## Objetivos

- Prever o vencedor e o placar de cada jogo.
- Medir a diferença de pontos, para cada time, entre o placar previsto e o placar real.
- Verificar se o modelo supera uma referência simples, como "o time da casa vence".

## Regras do projeto

- **Sem vazamento de dados:** o modelo só usa informações que existiam antes do início do jogo.
- **Execução local:** a `nba_api` tem limite de requisições e costuma bloquear serviços de nuvem, então tudo roda na máquina local, com pausas entre as chamadas.

## Etapas planejadas

- [ ] **(a) Vencedor e placar:** modelo treinado com temporadas passadas, usando estatísticas de time (ataque, defesa, ritmo, mando de quadra e dias de descanso).
- [ ] **(b) Jogos futuros:** previsão das próximas partidas, com um painel que acompanha os acertos.
- [ ] **(c) Box score por jogador:** previsão de pontos, rebotes e assistências, usando defesa contra posição e matchups.

## Tecnologias previstas

Python, `nba_api`, SQL e bibliotecas de machine learning.

## Autor

João Pedro, estudante de Sistemas de Informação na CESAR School.
