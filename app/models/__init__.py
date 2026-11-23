"""Entidades do domínio, mapeadas para o banco pelo SQLAlchemy.
 
Decisão de projeto: no início, as classes eram só listas de colunas — um
modelo anêmico — e as regras viviam nas rotas. Agora cada entidade mantém o
próprio estado válido: a RN-03 está nos métodos `concluir` e `reabrir`, o
único caminho para mudar o status de uma tarefa.
 
Modelo anêmico é a entidade que só guarda dados, sem comportamento. A
construção destes 14 dias fez o caminho oposto: `normalizar_email`,
`senha_confere`, `concluir`, `reabrir` e `esta_atrasada` moram nas entidades.
"""

#Importar as entidades aqui registra as tabelas no SQLAlchemy (é o que
# `cria_tabelas()` usa) e permite escrever `from app.modules import Usuario`.
from app.models.tarefa import Tarefa
from app.models.usuario import Usuario

__all__ = ["Tarfa", "Usuario"]