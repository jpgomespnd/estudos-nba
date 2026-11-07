"""Funções compartilhadas para abrir e preparar o banco SQLite."""

import sqlite3
from pathlib import Path

RAIZ_DO_PROJETO = Path(__file__).resolve().parent.parent
CAMINHO_BANCO = RAIZ_DO_PROJETO / "data" / "nba.db"
CAMINHO_ESQUEMA = RAIZ_DO_PROJETO / "sql" / "schema.sql"


def conectar(caminho=CAMINHO_BANCO):
    """Abre o banco, criando a pasta dele se ainda não existir."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(caminho)
    # O SQLite só confere as chaves estrangeiras quando isso é ligado.
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def criar_tabelas(conexao):
    """Executa o schema.sql no banco aberto."""
    conexao.executescript(CAMINHO_ESQUEMA.read_text(encoding="utf-8"))
