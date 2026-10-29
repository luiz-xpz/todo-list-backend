
"""Schemas públicos: o contrato de entrada e saída da API.

Aqui mora a tradução entre dois mundos de nomenclatura. O Python escreve
`criado_em` e `possui` com o front-end consegue esperar `criadoEm`. A conversão
acontece "na borda", que é o lugar correto: ela domina pela Python idiomático e
estes schemas fazem a tradução automaticamente, pelo alias_generator.
`populate_by_name=True` mantém a compatibilidade: a API aceita tanto o nome em
camelCase quanto o nome em Python na entrada.
"""

from app.schemas.base import DataHoraUTC, EsquemaDeEntrada, EsquemaDeSaida
from app.schemas.usuario import UsuarioCreate, UsuarioOut

__all__ = [
    "DataHoraUTC",
    "EsquemaDeEntrada",
    "EsquemaDeSaida",
    "UsuarioCreate",
    "UsuarioOut",
]
