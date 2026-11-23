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
    tempo_medio_conclusao_dias: float | None = Field(
        description="Média de dias entre criar e concluir; `null` se nada foi concluído"
    )
    concluidas_por_dia_da_semana: dict[str, int] = Field(
        description="Conclusões de todo o histórico por dia da semana, de `Seg` a `Dom`"
    )
    percentual_no_prazo: int | None = Field(
        description="Das concluídas que tinham prazo, % concluídas até o prazo;"
        "`null` se nenhuma tinha prazo"
    )