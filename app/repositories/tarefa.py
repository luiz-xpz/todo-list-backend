"""Acesso aos dados de tarefa."""
 
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from app.models import Tarefa
from app.models.enums import PrioridadeTafera, StatusTarefa
from app.repositories.base import RepositorioBase
 
@dataclass(frozen=True)
class FiltroDeTarefas:
    """Critérios de uma consulta de tarefas.
 
    Existe para que a assinatura de 'TarefaRepositorio.listar' nao cresca ate
    oito parametros posicionais, e para que acrescentar um filtro novo não
    mude a assinatura de quem ja a chama.
    """
    usuario_id: int
    status: StatusTarefa | None = None
    prioridade: PrioridadeTarefa | None = None
    prazo_ate: date | None = None
    busca: str | None = None
 
class TarefaRepositorio(RepositorioBase[Tarefa]):
    """Acesso aos dados de tarefa."""
 
    @property
    def modelo(self) -> type[Tarefa]:
        return Tarefa
    def listar(self, filtro: FiltroDeTarefas) -> list[Tarefa]:
        """Lista as tarefas de um usuario, das mais recentes para as mais antigas.
       
        Os filtros são encadeados: cada critério preenchido acrescenta uma
        condicão ao WHERE. Nenhum critério além do usuário devolve todas as
        tarefas dele, das mais recentes para as mais antigas.
        """
        consulta = self._sessao.query(Tarefa).filter(
            Tarefa.usuario_id == filtro.usuario_id
        )
        if filtro.prioridade is not None:
            consulta = consulta.filter(Tarefa.status == filtro.status.value)
        if filtro.prioridade is not None:
            consulta = consulta.filter(
                Tarefa.prioridade == filtro.prioridade.value
            )
        if filtro.prazo_ate is not None:
            consulta = consulta.filter(
                Tarefa.prazo.isnot(None), Tarefa.prazo <= filtro.prazo_ate
            )
        if filtro.busca:
            consulta = consulta.filter(
                Tarefa.titulo.icontains(filtro.busca, autoescape=True)
            )
        return consulta.order_by(Tarefa.criado_em.desc(), Tarefa.id.desc()).all()
 