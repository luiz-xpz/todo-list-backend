
"""Configuração da aplicação a partir de variáveis de ambiente."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

# Carrega as variáveis definidas no arquivo .env
load_dotenv()


class ConfiguracaoInvalida(RuntimeError):
    """Falta ou está incorreta uma variável de ambiente obrigatória."""


@dataclass(frozen=True)
class Configuracao:
    """Parâmetros de execução da aplicação."""

    database_url: str = ""

    @classmethod
    def do_ambiente(cls) -> Configuracao:
        """Monta a configuração a partir das variáveis de ambiente."""
        return cls(
            database_url=os.getenv("DATABASE_URL", "").strip()
        )

    @property
    def url_banco(self) -> str:
        """Retorna a URL do banco ou lança um erro de configuração."""

        if not self.database_url:
            raise ConfiguracaoInvalida(
                "DATABASE_URL não definida. "
                "Copie o arquivo .env.example para .env "
                "e deixe ativa uma das opções: SQLite (local) "
                "ou PostgreSQL no Render."
            )

        return self.database_url


@lru_cache
def obter_configuracao() -> Configuracao:
    """Retorna a configuração da aplicação, carregada uma única vez."""
    return Configuracao.do_ambiente()
