# Contexto do projeto para o Claude

Este arquivo guarda o contexto que não aparece no código: quem é o autor, como ele gosta de trabalhar, as decisões já tomadas e o que falta fazer. Leia antes de qualquer tarefa e mantenha-o atualizado ao fim de cada etapa.

## Sobre o autor e como trabalhar

- João Pedro, estudante de Sistemas de Informação (CESAR School), voltando a programar depois de um tempo parado. Este é um projeto de portfólio e de estudo para vagas de dados, IA ou desenvolvimento.
- **Responda sempre em português** e explique em detalhe o que cada comando e cada trecho de código faz, em linguagem simples. Ele usa as explicações para estudar e para falar em entrevistas.
- Ao fim de cada etapa, diga o que foi feito e qual é o próximo passo, e **só continue quando ele disser que pode seguir**.
- Commits pequenos, no padrão Conventional Commits em português (`feat:`, `fix:`, `docs:`, `chore:`), terminando com a linha de coautoria do Claude.
- Uma branch por tarefa (`feat/...`, `chore/...`). Ao terminar e com o ok dele, envie a branch e junte na `main` com `git merge --ff-only`. Se a `main` do GitHub tiver mudado, faça um merge normal, sem `push --force`.
- Ele às vezes edita arquivos direto no site do GitHub. Rode `git fetch` antes de juntar na `main`.
- Valide sempre os dados e o código e conte os erros encontrados com transparência, inclusive os erros do próprio Claude.

## A direção do projeto

O objetivo deixou de ser prever jogos futuros. Agora é um **simulador de séries de playoffs em melhor de 7** entre times reais de temporadas diferentes, como Warriors 2021-22 contra Thunder 2025-26.

- O usuário escolhe a temporada e o time mandante, que tem o mando de quadra no formato 2-2-1-1-1, e depois o visitante.
- Cada jogo da série mostra o placar e o box score completo dos jogadores.
- Rodando milhares de séries (Monte Carlo), o sistema mostra a chance de vitória de cada time.
- No futuro, haverá um site para o usuário fazer as simulações.

### Regras decididas pelo autor

- **Elenco:** o time como estava no fim da temporada regular. O jogador pertence ao time do seu último jogo.
- **Estatísticas:** só os jogos do jogador pelo time final, porque minutos e função mudam depois de uma troca.
- **Lesões:** são ignoradas, e toda simulação usa a rotação ideal.
- **Rotação ideal:** os 9 jogadores com mais minutos por jogo, entre os que têm pelo menos 20 jogos pelo time final. Os 5 primeiros são titulares, e os minutos são ajustados para somar 240.
- **Casos com menos de 20 jogos:** a view `vw_fora_da_rotacao` lista quem ficaria na rotação pelos minutos, mas não tem jogos suficientes. A decisão foi olhar esses casos nos dados antes de mudar a regra.
- **Badges e tags:** ficam para depois. Se entrarem, serão calculadas a partir dos dados e só informativas, sem dar bônus na simulação.
- **Temporadas:** regulares e playoffs de 2021-22 a 2025-26 por enquanto. Times mais antigos ficam para depois.

### Como validar

Um confronto entre temporadas diferentes nunca aconteceu, então não pode ser conferido. Por isso o modelo deve ser testado em situações reais:
- **Jogos de uma temporada guardada:** o modelo não vê esses jogos no treino e precisa superar a referência "o time da casa vence", que acerta de 54% a 58% por temporada.
- **Séries reais de playoffs:** comparar as séries simuladas com as que aconteceram.

**Evitar vazamento de dados:** no treino e no teste, cada variável de um jogo deve usar só informação de antes daquele jogo. O autor removeu essa frase do README, mas pediu a regra no início do projeto. Pergunte se ele quer recolocá-la.

### Fases (no README)

1. Jogadores, elencos e playoffs no banco (**em andamento**).
2. Variáveis e modelo de placar, testado em jogos reais.
3. Overall e defesa por posição.
4. Simulador de séries em melhor de 7, testado com séries reais.
5. Box score por jogador, somando exatamente o placar do time.
6. API (FastAPI) e site (React).

## O que já descobrimos nos dados

- **`nba_api`:** tem limite de requisições e costuma bloquear servidores na nuvem. A coleta roda na máquina local, com pausa de 3 segundos entre as chamadas. O site futuro deve usar dados já prontos, sem chamar a API.
- **Quadra neutra:** a API marca os dois times com `@`, sem mandante. São 10 jogos, em 2024-25 e 2025-26, marcados com `is_neutral = 1`. Em temporadas anteriores, jogos neutros, como as semifinais da NBA Cup de 2023-24, aparecem com um mandante só nominal.
- **Minutos:** os minutos dos jogadores vêm arredondados, então a soma por time varia de 237 a 242 sem prorrogação.
- **Partidas de playoffs:** o ID segue o formato `004AA00RSJ`, em que R é a rodada, S a série e J o jogo. Os 9 primeiros caracteres identificam a série. Os jogos de play-in não entram em "Playoffs".
- **`PlayerIndex`:** com uma temporada definida, trouxe só 130 jogadores. Use `CommonTeamRoster`, que dá o elenco da temporada com posição, altura e peso.
- **Posições:** vêm amplas (G, F, C, G-F, F-C), sem PG ou SG.
- **Dados defensivos testados na API:** `LeagueDashPtDefend`, `LeagueHustleStatsPlayer`, `LeagueSeasonMatchups` (cerca de 140 mil linhas por temporada) e `LeagueDashPlayerStats` com `measure_type_detailed_defense="Advanced"`. Funcionaram em 2021-22 e 2024-25.
  - **Limitação 1:** são totais da temporada inteira, então usá-los no treino causa vazamento de dados.
  - **Limitação 2:** misturam os times de quem foi trocado. Para respeitar a regra do time final, seria preciso filtrar por time.

## Referência visual: EraBall

O autor gosta do site eraball.com e mandou prints dele. Ele é só **inspiração**: não copie visual, notas, nomes ou modos de jogo, e não raspe dados. O `robots.txt` do site bloqueia robôs de IA, incluindo os da Anthropic, e sinaliza uso só como referência, então não acesse o site automaticamente.

O autor gostou destes elementos, para fazermos uma versão própria:
- **Jogo da série:** placar grande com os líderes de pontos, rebotes e assistências.
- **Box score:** MIN, PTS, REB, AST, STL, BLK, TOV, TS%, FG%, FGM, FGA, 3P% e 3PM.
- **Série:** acompanhamento do placar, como 1-0, com um cartão por jogo, e botões de próximo jogo, avanço automático e pular para o fim.
- **Resumo da série:** médias do time e do adversário, mais o MVP da série.
- **Cartão do jogador:** overall, tier, posição, altura e peso, com filtro por posição e ordenação por estatística.

## Estado atual (fase 1)

Branch: `feat/fase1-jogadores`.

**Já feito:**
- **README:** reescrito com a nova direção.
- **Esquema versão 2:** tabelas `players`, `player_games` e `rosters`, mais a coluna `season_type` em `games`. O `PRAGMA user_version` impede usar um banco antigo.
- **Views novas:** `vw_elenco_final`, `vw_jogadores_time_final`, `vw_rotacao` e `vw_fora_da_rotacao`.
- **Coleta:** baixa a temporada regular e os playoffs de times e de jogadores, além dos elencos. Os elencos são retomáveis, então quem já está salvo não é baixado de novo.

**Resultado da coleta completa:**
- **Volume:** 6.572 partidas, das quais 422 de playoffs; 140.321 linhas de jogadores, 1.035 jogadores e 150 elencos (30 times × 5 temporadas).
- **Validação:** as 12 regras atuais passam.
- **Rotação:** todos os 150 times têm 9 jogadores, os minutos somam 240 e o máximo de um jogador é 38,6.

**Três pontos para discutir com o autor:**
1. **Minutos reduzidos na rotação:** como as lesões são ignoradas, os 9 melhores juntos costumam passar de 240 minutos por jogo, e o ajuste reduz os minutos de todos. Exemplo: Jayson Tatum, no Boston de 2024-25, vai de 36,4 para 33,6 minutos.
2. **Muitos casos com menos de 20 jogos:** a `vw_fora_da_rotacao` tem 143 jogadores, número maior do que eu esperava. É preciso olhar quem são antes de decidir a regra.
3. **Rotação fora do elenco oficial:** 13 jogadores da rotação não aparecem no elenco oficial (`rosters`), provavelmente porque foram dispensados depois do último jogo. É preciso investigar.

**Falta fazer:**
1. **Ampliar o `scripts/validar_dados.py`:**
   - Somas dos jogadores contra os totais do time. Confira antes se TOV e REB do time incluem jogadas de equipe que não são atribuídas a jogadores.
   - Folga de cerca de 5 minutos na soma dos minutos.
   - 15 séries por temporada nos playoffs, cada uma com um time chegando a 4 vitórias, em 4 a 7 jogos.
   - Rotação com 9 jogadores por time, minutos somando 240 e nenhum jogador acima de 48.
2. **Alertas informativos:** que não reprovam a validação.
   - Jogadores da rotação que não estão no elenco oficial (`rosters`).
   - A lista da `vw_fora_da_rotacao`, para o autor decidir a regra dos 20 jogos.
3. **README:** atualizar a seção de dados com as tabelas e views novas.
4. **Fechar a fase:** explicar tudo ao autor, enviar a branch e juntar na `main`.

## Comandos (Windows, Python 3.12)

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe scripts\coletar_jogos.py   # cerca de 10 minutos; cria data/nba.db
.venv\Scripts\python.exe scripts\validar_dados.py
```

- **Banco:** `data/nba.db` não vai para o Git. Recrie-o com a coleta. Se o esquema mudar, apague o banco e rode a coleta de novo.
- **Acentos:** se a saída do terminal sair estranha, defina `PYTHONUTF8=1`.
- **Git no Git Bash:** se `git` não for reconhecido, use o caminho completo, `"C:\Program Files\Git\cmd\git.exe"`, ou abra um terminal novo.
