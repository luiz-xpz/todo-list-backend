"""
Segurança: funções de hash de senha e verificação de hash.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from app.core.exceptions import TokenInvalido

# O bcrypt só considera os primeiros 72 BYTES da senha (a versão 5 recusa
# senhas maiores). Em UTF-8 um caractere acentuado ocupa 2 bytes, então o limite
# é conferido em bytes, não em caracteres — senhas UsuárioCreate
LIMITE_BYTES_SENHA = 72

class HashDeSenha(ABC):
    """Contrato de implementação de hash de senha. A aplicação só usa a interface, não a implementação concreta.
    """

    @abstractmethod
    def gerar(self, senha: str) -> str:
        """Devolve o hash da senha informada."""

    @abstractmethod
    def verificar(self, senha: str, hash_armazenado: str) -> bool:
        """Confere se a senha corresponde ao hash gravado."""

class HashBcrypt(HashDeSenha):
    """Implementação de hash de senha usando o algoritmo bcrypt.
    """

    def gerar(self, senha: str) -> str:
        return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("ascii")

    def verificar(self, senha: str, hash_armazenado: str) -> bool:
        senha_bytes = senha.encode("utf-8")
        if len(senha_bytes) > LIMITE_BYTES_SENHA:
            # Nenhuma senha cadastrada passa desse tamanho; responder "não confere"
            # é mais seguro do que deixar o bcrypt lançar um erro inesperado.
            return False
        return bcrypt.checkpw(senha_bytes, hash_armazenado.encode("ascii"))

@dataclass (frozen=True)
class TokenEmitido:
    """Um token de acesso recém-criado e o momento em que deixa de valer."""
    valor: str
    expira_em: datetime

class TokenJWT:
    """Emite e confere tokens JWT assinados com HS256.
    """

    ALGORITIMO = "HS256"
    def __init__(self, segredo: str, expira_minutos: int) -> None:
        self._segrdo = segredo
        self._validade = timedelta(minutes=expira_minutos)
    def emitir(self, usuario_id: int, agora:datetime | None = None) -> TokenEmitido:
        """Criar um token válido pelo tempo configurado."""
        expira_em = (agora or datetime.now(timezone.utc)) + self._validade
        conteudo = {"sub": str(usuario_id), "exp":expira_em}
        valor = jwt.encode(conteudo, self._segrdo, algorithm=self.ALGORITIMO)
        return TokenEmitido(valor=valor, expira_em=expira_em)

    def ler(self, token: str) -> int:
        """Confere assinatura e validade e devolde o id do usuário.
        Raise:
            TokenInvalido: token expirado, adulterado ou malformado.
        """

        try:
            conteudo = jwt.decode(
                token,
                self._segrdo,
                algorithms=[self.ALGORITIMO],
                options={"require": ["sub", "exp"]},
            )
            return int (conteudo["sub"])
        except jwt.ExpiredSignatureError as erro:
            raise TokenInvalido("Sessão expirada. Entre novamente.") from erro
        except (jwt.InvalidTokenError, ValueError) as erro:
            raise TokenInvalido() from erro