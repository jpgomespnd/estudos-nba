import sqlite3
from pathlib import Path

RAIZ_DO_PROJETO = Path(__file__).resolve().parent.parent
CAMINHO_BANCO = RAIZ_DO_PROJETO / "data" / "nba.db"
CAMINHO_ESQUEMA = RAIZ_DO_PROJETO / "sql" / "schema.sql"


def conectar(caminho=CAMINHO_BANCO):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(caminho)
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def criar_tabelas(conexao):
    conexao.executescript(CAMINHO_ESQUEMA.read_text(encoding="utf-8"))
