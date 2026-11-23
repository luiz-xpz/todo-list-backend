
"""Acesso aos dados de tarefa."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import case

from app.models import Tarefa
from app.models.enums import (
    CampoOrdenacao,
    Ordem,
    PrioridadeTarefa,
    StatusTarefa,
)
from app.repositories.base import RepositorioBase


@dataclass(frozen=True)
class FiltroDeTarefas:
    """Critérios de uma consulta de tarefas."""

    usuario_id: int
    status: StatusTarefa | None = None
    prioridade: PrioridadeTarefa | None = None
    prazo_ate: date | None = None
    busca: str | None = None
    ordena_por: CampoOrdenacao = CampoOrdenacao.CRIADO_EM
    ordem: Ordem = Ordem.DESC
    limite: int = 100
    deslocamento: int = 0


@dataclass(frozen=True)
class PaginaDeTarefa:
    """Uma página da listagem e o total de tarefas que atendem ao filtro."""

    tarefas: list[Tarefa]
    total: int


class TarefaRepositorio(RepositorioBase[Tarefa]):
    """Acesso aos dados de tarefa."""

    _ORDEM_POR_PRIORIDADE = case(
        PrioridadeTarefa.mapa_de_peso(),
        value=Tarefa.prioridade,
        else_=99,
    )

    @property
    def modelo(self) -> type[Tarefa]:
        return Tarefa

    def _coluna_de_ordenacao(self, campo: CampoOrdenacao):
        """Devolve a expressão SQL correspondente ao campo de ordenação."""

        colunas = {
            CampoOrdenacao.CRIADO_EM: Tarefa.criado_em,
            CampoOrdenacao.PRAZO: Tarefa.prazo,
            CampoOrdenacao.PRIORIDADE: self._ORDEM_POR_PRIORIDADE,
        }

        return colunas[campo]

    def listar(self, filtro: FiltroDeTarefas) -> PaginaDeTarefa:
        """Lista as tarefas de um usuário."""

        consulta = self._sessao.query(Tarefa).filter(
            Tarefa.usuario_id == filtro.usuario_id
        )

        if filtro.status is not None:
            consulta = consulta.filter(
                Tarefa.status == filtro.status.value
            )

        if filtro.prioridade is not None:
            consulta = consulta.filter(
                Tarefa.prioridade == filtro.prioridade.value
            )

        if filtro.prazo_ate is not None:
            consulta = consulta.filter(
                Tarefa.prazo.isnot(None),
                Tarefa.prazo <= filtro.prazo_ate,
            )

        if filtro.busca:
            consulta = consulta.filter(
                Tarefa.titulo.icontains(
                    filtro.busca,
                    autoescape=True,
                )
            )

        # O total é contado antes de aplicar limites e deslocamento.
        total = consulta.order_by(None).count()

        coluna = self._coluna_de_ordenacao(filtro.ordena_por)

        ordenacao = [
            coluna.desc()
            if filtro.ordem is Ordem.DESC
            else coluna.asc()
        ]

        if filtro.ordena_por is CampoOrdenacao.PRAZO:
            ordenacao.insert(
                0,
                case((Tarefa.prazo.is_(None), 1), else_=0),
            )
            ordenacao.append(Tarefa.id.desc())

        tarefas = (
            consulta.order_by(*ordenacao)
            .offset(filtro.deslocamento)
            .limit(filtro.limite)
            .all()
        )

        return PaginaDeTarefa(
            tarefas=tarefas,
            total=total,
        )

    def todas_do_usuario(self, usuario_id: int) -> list[Tarefa]:
        """Todas as tarefas de um usuário, sem filtro nem limite."""

        return (
            self._sessao.query(Tarefa)
            .filter(Tarefa.usuario_id == usuario_id)
            .all()
        )
