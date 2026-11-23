
"""Operações sobre as tarefas do usuário autenticado."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from app.core.exceptions import AcessoNaoAutorizado, TarefaNaoEncontrada
from app.models import Tarefa
from app.models.enums import PrioridadeTarefa, StatusTarefa
from app.repositories import FiltroDeTarefas, PaginaDeTarefa, TarefaRepositorio

# Sentinela para distinguir "campo não enviado" de "campo enviado como null".
# Sem ela, não haveria como diferenciar um PATCH que não menciona o prazo de
# um PATCH que pede explicitamente para apaga-lo.

NAO_INFORMADO: Any = object()


@dataclass(frozen=True)
class AlteracoesDaTarefa:
    """Campos que um PATCH pediu para alterar."""

    titulo: Any = NAO_INFORMADO
    status: Any = NAO_INFORMADO
    prioridade: Any = NAO_INFORMADO
    prazo: Any = NAO_INFORMADO

    def informado(self, campo: str) -> bool:
        """Informa se o cliente enviou este campo."""
        return getattr(self, campo) is not NAO_INFORMADO

@dataclass(frozen=True)
class Resumo:
    """Os números do Painel de um usuário."""

    total: int
    pendentes: int
    concluidas: int
    atrasadas: int

class TarefaServico:
    """Operações sobre as tarefas do usuário autenticado."""

    def __init__(self, tarefas: TarefaRepositorio) -> None:
        self._tarefas = tarefas

    def criar(
        self,
        usuario_id: int,
        titulo: str,
        prioridade: PrioridadeTarefa,
        prazo: date | None,
    ) -> Tarefa:
        """Cria uma tarefa para o usuário autenticado.  """

        tarefa = Tarefa(
            usuario_id=usuario_id,
            titulo=titulo,
            prioridade=prioridade,
            prazo=prazo,
        )
        return self._tarefas.salvar(tarefa)

    def listar(self, filtro: FiltroDeTarefas) -> PaginaDeTarefa:
        """Lista as tarefas do usuário autenticado."""
        return self._tarefas.listar(filtro)

    def buscar(self, tarefa_id: int, usuario_id: int) -> Tarefa:
        """Devolve uma tarefa do usuário."""
        tarefa = self._tarefas.buscar_por_id(tarefa_id)

        if tarefa is None:
            raise TarefaNaoEncontrada()
        if not tarefa.pertence_a(usuario_id):
            raise AcessoNaoAutorizado()
        return tarefa

    def atualizar(
        self,
        tarefa_id: int,
        usuario_id: int,
        alternacoes: AlteracoesDaTarefa,
    ) -> Tarefa:
        """Aplica as alterações informadas e devolve a tarefa atualizada.
        """
        tarefa = self.buscar(tarefa_id, usuario_id)

        if alternacoes.informado("titulo"):
            tarefa.titulo = alternacoes.titulo

        if alternacoes.informado("prioridade"):
            tarefa.prioridade = alternacoes.prioridade

        if alternacoes.informado("prazo"):
            tarefa.prazo = alternacoes.prazo

        if alternacoes.informado("status"):
            tarefa.definir_status(
                StatusTarefa(alternacoes.status)        
            )

        return self._tarefas.salvar(tarefa)

    def remover(self, tarefa_id: int, usuario_id: int) -> None:
        """Remove a tarefa definitivamente.
        """ 
        self._tarefas.remover(self.buscar(tarefa_id, usuario_id))
    
    def resumo (self, usuario_id: int, hoje: date | None = None) -> Resumo:
        """Calcula os números do Painel: total, pendente, concluídas e atrasadas."""
        hoje = hoje or date.today()
        tarefas = self._tarefas .todas_do_usuario(usuario_id)
        pendentes = sum(1 for t in tarefas if t.status is StatusTarefa.PENDENTE)
        concluidas = sum(1 for t in tarefas if t.status is StatusTarefa.CONCLUIDA)

        return Resumo(
            total=len(tarefas),
            pendentes=pendentes,
            concluidas=concluidas,
            atrasadas=sum(1 for t in tarefas if t.esta_atrasada(hoje)),
        )