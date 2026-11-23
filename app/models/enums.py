"""Enumeração do domínio."""
from enum import Enum 


class StatusTarefa(str, Enum):
    """Situação em  que uma tarefa pode estar."""

    PENDENTE = "pendente"
    CONCLUIDA = "concluida"

class PrioridadeTarefa(str, Enum):
    """Nível de prioridade de uma tarefa, de menor para a maior."""

    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    URGENTE = "urgente"
    @property
    def peso(self) -> int:
        """Posição na ordenação pro peioridade - 0 é a mais urgente."""
        return _PESOS[self]
    @classmethod
    def mapa_de_peso(cls) -> dict[str, int]:
        """Mapa `valor -> peso`, no formato que o `case()` do SQL consome."""
        return {prioridade.value: prioridade.peso for prioridade in cls}
_PESOS = {
    PrioridadeTarefa.URGENTE: 0,
    PrioridadeTarefa.ALTA: 1,
    PrioridadeTarefa.MEDIA: 2,
    PrioridadeTarefa.BAIXA: 3,
}

class CampoOrdenacao(str, Enum):
    """Campos pelos quais a listagem de tarefas pode ser ordenada.

    Os valores repetem o nome público do campo API (camelCase), porque é
    isso que o cliente envia `?ordenarPor=`. Como é um enum, um valor fora
    da lista passa a ser recusado com 422 - antes, o código caía
    silenciosamente ma ordenação por data de criação e o cliente nunca sabia
    que seu parâmetro havia sido ignorado
    """

    CRIADO_EM = "criadoEm"
    PRAZO = "prazo"
    PRIORIDADE = "prioridade"

class Ordem(str, Enum):
    """Sentido da ordenação."""

    ASC = "asc"
    DESC = "desc"