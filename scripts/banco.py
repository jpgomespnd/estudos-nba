"""Funções compartilhadas para abrir e preparar o banco SQLite."""

import sqlite3
from pathlib import Path

RAIZ_DO_PROJETO = Path(__file__).resolve().parent.parent
CAMINHO_BANCO = RAIZ_DO_PROJETO / "data" / "nba.db"
CAMINHO_ESQUEMA = RAIZ_DO_PROJETO / "sql" / "schema.sql"

# Aumente este número sempre que o schema.sql mudar uma tabela já existente.
VERSAO_ESQUEMA = 2


class EsquemaDesatualizado(RuntimeError):
    """O banco foi criado por uma versão antiga do schema.sql."""


def conectar(caminho=CAMINHO_BANCO):
    """Abre o banco, criando a pasta dele se ainda não existir."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(caminho)
    # O SQLite só confere as chaves estrangeiras quando isso é ligado.
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def criar_tabelas(conexao):
    """Executa o schema.sql, recusando bancos criados por um esquema antigo."""
    # user_version é um número que o SQLite guarda no próprio arquivo do banco.
    versao_atual = conexao.execute("PRAGMA user_version").fetchone()[0]
    tem_tabelas = conexao.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'"
    ).fetchone()[0]

    if tem_tabelas and versao_atual != VERSAO_ESQUEMA:
        raise EsquemaDesatualizado(
            f"O banco está na versão {versao_atual} do esquema, e o código espera a "
            f"versão {VERSAO_ESQUEMA}. Apague data/nba.db e rode a coleta de novo."
        )

    conexao.executescript(CAMINHO_ESQUEMA.read_text(encoding="utf-8"))
    conexao.execute(f"PRAGMA user_version = {VERSAO_ESQUEMA}")
