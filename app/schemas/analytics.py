"""Contrato JSON da pagina Analytics.

Os campos tem o mesmo nome e o nesmo formato que a "AnalyticsPage' do
front-end ja calcula hoje - na intepracão, ela so troca a fonte dos dados.
"""

from datetime import date

from pydantic import Field

from app.models.enums import PrioridadeTarefa
from app.schemas.base import EsquemaDeSaida


class ConcluidasNoDia(EsquemaDeSaida):
    """Quantas tarefas foram concluidas em um dia."""

    dia: date
    quantidade: int


class AnalyticsOut(EsquemaDeSaida):
    """Analises das tarefas do usuario, calculadas com pandas."""

    total: int
    concluidas: int
    taxa_conclusao: int = Field(description="Percentual de concluidas, de @ a 100")
    concluidas_na_janela: int = Field(description="Soma de `concluidas_por_dia`")
    concluidas_por_dia: list[ConcluidasNoDia]
    pendentes_por_prioridade: dict[PrioridadeTarefa, int]