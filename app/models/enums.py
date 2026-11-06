"""Enumeração do domínio.

Antes, os valores válidos de status e prioridade estavam escritos como texto
solto em três lugares: `Literal` dos schemas, no `default` das colunas e no 
`case` que ordeva por prioridade. Acrescentar uma prioridade nova exigia
lembrar dos três. Aqui eles passam a ter um único lugar de definição.

Herdar de `str` faz cada membro se comportar como próprio texto - o que 
permite gravá-lo em uma coluna `String`, compará-lo com uma string vinda do 
bamco e serializá-lo em JSON em conversão manual.
"""
from enum import Enum 

class StatusTarefa(str, Enum):
    """Situação em  que uma tarefa pode estar."""

    PENDENTE = "pendente"
    CONCLUIDA = "concluida"

class PrioridadeTafera(str, Enum):
    """Nível de prioridade de uma tarefa, de menor para a maior."""

    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    URGENTE = "urgente"
    @property
    def peso(self) -> int:
        """Posição na ordenação pro peioridade - 0 é a mais urgente.
        Ordenar pelo texto daria "alta, baixa, media, urgente", que não é a 
        ordem que o usuário espera ver. O peso existe para isso.
        """
        return _PESOS[self]
    @classmethod
    def mapa_de_peso(cls) -> dict[str, int]:
        """Mapa `valor -> peso`, no formato que o `case()` do SQL consome."""
        return {prioridade.value: prioridade.peso for prioridade in cls}
_PESOS = {
    PrioridadeTafera.URGENTE: 0,
    PrioridadeTafera.ALTA: 1,
    PrioridadeTafera.MEDIA: 2,
    PrioridadeTafera.BAIXA: 3,
}