
"""Análise de dados das tarefas com pandas - os números da página Analytics."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import pandas as pd

from app.models import Tarefa
from app.models.enums import PrioridadeTarefa, StatusTarefa
from app.repositories import TarefaRepositorio


def arredondar(valor: float) -> int:
    """Arredonda como Math.round do JavaScript: 12,5 vira 13."""
    return math.floor(valor + 0.5)


@dataclass(frozen=True)
class Analytics:
    """Resultado da análise das tarefas de um usuário."""

    total: int
    concluidas: int
    taxa_conclusao: int
    concluidas_na_janela: int
    concluidas_por_dia: list[dict]
    pendentes_por_prioridade: dict[PrioridadeTarefa, int]
    tempo_medio_conclusao_dias: float | None
    concluidas_por_dia_da_semana: dict[str, int]
    percentual_no_prazo: int | None


class AnalyticsServico:
    """Calcula as análises da página Analytics."""

    def __init__(self, tarefas: TarefaRepositorio) -> None:
        self._tarefas = tarefas

    def calcular(
        self,
        usuario_id: int,
        dias: int = 7,
        hoje: date | None = None
    ) -> Analytics:

        hoje = hoje or date.today()

        tabela = self._montar_tabela(
            self._tarefas.todas_do_usuario(usuario_id)
        )

        # Filtra tarefas concluídas.
        concluida = tabela["status"] == StatusTarefa.CONCLUIDA.value

        concluidas = tabela[concluida]
        pendentes = tabela[~concluida]

        total = len(tabela)

        por_dia = self._concluidas_por_dia(
            concluidas, dias, hoje
        )

        return Analytics(
            total=total,
            concluidas=len(concluidas),
            taxa_conclusao=(
                arredondar(len(concluidas) / total * 100)
                if total else 0
            ),
            concluidas_na_janela=sum(
                item["quantidade"] for item in por_dia
            ),
            concluidas_por_dia=por_dia,
            pendentes_por_prioridade=self._pendentes_por_prioridade(
                pendentes
            ),
            tempo_medio_conclusao_dias=self._tempo_medio_conclusao(
                concluidas
            ),
            concluidas_por_dia_da_semana=self._concluidas_por_dia_da_semana(
                concluidas
            ),
            percentual_no_prazo=self._percentual_no_prazo(concluidas),
        )

    # Tabela de tarefas
    @staticmethod
    def _montar_tabela(tarefas: list[Tarefa]) -> pd.DataFrame:
        """Transforma a lista de tarefas num DataFrame."""

        fuso_do_servidor = datetime.now().astimezone().tzinfo

        tabela = pd.DataFrame(
            {
                "status": [t.status.value for t in tarefas],
                "prioridade": [t.prioridade for t in tarefas],
                "criado_em": [t.criado_em for t in tarefas],
                "concluido_em": [t.concluida_em for t in tarefas],
                "prazo": [t.prazo for t in tarefas],
            }
        )

        tabela["criado_em"] = pd.to_datetime(
            tabela["criado_em"], utc=True
        ).dt.tz_convert(fuso_do_servidor)

        tabela["concluido_em"] = pd.to_datetime(
            tabela["concluido_em"], utc=True
        ).dt.tz_convert(fuso_do_servidor)

        tabela["dia_conclusao"] = tabela["concluido_em"].dt.date

        return tabela

    # Métricas
    @staticmethod
    def _concluidas_por_dia(
        concluidas: pd.DataFrame,
        dias: int,
        hoje: date
    ) -> list[dict]:

        """Quantas tarefas foram concluídas em cada um dos últimos dias."""

        janela = [
            hoje - timedelta(days=n)
            for n in range(dias - 1, -1, -1)
        ]

        contagem = (
            concluidas["dia_conclusao"]
            .value_counts()
            .reindex(janela, fill_value=0)
        )

        return [
            {"dia": dia, "quantidade": int(qtd)}
            for dia, qtd in contagem.items()
        ]

    @staticmethod
    def _pendentes_por_prioridade(
        pendentes: pd.DataFrame
    ) -> dict[PrioridadeTarefa, int]:

        """Quantas tarefas pendentes há em cada prioridade."""

        ordem = [
            p.value
            for p in sorted(
                PrioridadeTarefa,
                key=lambda p: p.peso
            )
        ]

        contagem = (
            pendentes["prioridade"]
            .value_counts()
            .reindex(ordem, fill_value=0)
        )

        return {
            PrioridadeTarefa(prioridade): int(qtd)
            for prioridade, qtd in contagem.items()
        }

    @staticmethod
    def _tempo_medio_conclusao(
        concluidas: pd.DataFrame
    ) -> float | None:

        validas = concluidas.dropna(
            subset=["criado_em", "concluido_em"]
        )

        if validas.empty:
            return None

        duracoes = (
            validas["concluido_em"] - validas["criado_em"]
        ).dt.total_seconds() / 86400

        return float(duracoes.mean())

    @staticmethod
    def _concluidas_por_dia_da_semana(
        concluidas: pd.DataFrame
    ) -> dict[str, int]:

        dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

        validas = concluidas.dropna(
            subset=["concluido_em"]
        )

        contagem = (
            validas["concluido_em"]
            .dt.dayofweek
            .value_counts()
            .reindex(range(7), fill_value=0)
        )

        return {
            dia: int(contagem[i])
            for i, dia in enumerate(dias)
        }

    @staticmethod
    def _percentual_no_prazo(
        concluidas: pd.DataFrame
    ) -> int | None:

        com_prazo = concluidas.dropna(
            subset=["prazo", "concluido_em"]
        )

        if com_prazo.empty:
            return None

        dentro_do_prazo = (
            com_prazo["concluido_em"].dt.date <= com_prazo["prazo"]
        )

        return arredondar(
            dentro_do_prazo.sum() / len(com_prazo) * 100
        )
