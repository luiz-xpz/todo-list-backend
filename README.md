# Todo List API

**Backend REST para gerenciamento de tarefas — Curso Desenvolvedor Full Stack | SENAC**

API desenvolvida com **Python, FastAPI e SQLAlchemy**, com autenticação por **JWT**, armazenamento em **SQLite** (desenvolvimento local) ou **PostgreSQL** (Render) e indicadores calculados com **Pandas**. Oferece cadastro e login de usuários, operações de tarefas, consultas com filtros e paginação, resumo do painel e análises estatísticas.

> **Base documental e escopo da verificação:** esta documentação foi conferida com o backend em `Todo-List-Backend.zip`, o front-end React em `todo-list-main-completo-uc-01.rar` e os **14 manuais oficiais de construção** da UC 2 (SENAC). A tabela da seção 10 reproduz as funcionalidades por dia da página final do Manual do Dia 14. Os caminhos e campos de API documentam **o backend efetivamente enviado**, que em alguns pontos difere do roteiro dos manuais. O funcionamento geral foi informado pelo desenvolvedor, mas a inspeção dos arquivos não substitui testes de ponta a ponta: **não houve comprovação de instalação limpa com as dependências exatas, autenticação com bcrypt real ou deploy no Render; a inspeção do React confirmou que ele ainda utiliza serviços simulados em `localStorage`, sem integração HTTP com a API Python**. Os exemplos de JSON são ilustrativos.

---

## 1. O projeto e a arquitetura em camadas

### Objetivo

A Todo List API fornece o serviço de dados de uma aplicação de organização pessoal. Cada usuário autenticado pode manter suas próprias tarefas, consultar seu andamento e visualizar métricas de produtividade. O sistema mantém o vínculo entre as tarefas e o usuário que as criou.

### Organização das camadas

```text
Cliente HTTP / Front-end React
            |
            v
app/main.py                         FastAPI, CORS, ciclo de vida e erros HTTP
            |
            v
app/api/routers/                  Endpoints HTTP (usuários e tarefas)
            |
            v
app/api/dependencies.py           Injeção de dependências e usuário autenticado
            |
            v
app/services/                     Regras de negócio e cálculos do Analytics
            |
            v
app/repositories/                 Consultas e persistência de dados
            |
            v
app/models/ + app/db/database.py  Modelos SQLAlchemy, sessões e engine
            |
            v
SQLite local / PostgreSQL no Render

app/schemas/                      Contratos de entrada e saída (Pydantic)
app/core/                         Configuração, segurança, datas e exceções
```

| Camada | Arquivos principais | Responsabilidade |
|---|---|---|
| Aplicação | `app/main.py` | Inicializar a API, adicionar middleware CORS, registrar rotas, criar tabelas e traduzir exceções para HTTP. |
| API | `app/api/routers/usuario.py`, `app/api/routers/tasks.py` | Declarar caminhos, métodos, parâmetros e respostas HTTP. |
| Dependências | `app/api/dependencies.py` | Montar repositórios e serviços e validar o token Bearer. |
| Serviços | `app/services/usuario.py`, `tarefa.py`, `analytics.py` | Executar cadastro, autenticação, regras de tarefa e indicadores. |
| Repositórios | `app/repositories/` | Realizar acesso ao banco, filtros, paginação e buscas. |
| Modelos | `app/models/` | Representar `Usuario` e `Tarefa` e preservar regras de domínio. |
| Schemas | `app/schemas/` | Validar entradas e serializar saídas no formato JSON. |
| Infraestrutura | `app/db/database.py`, `app/core/` | Conexão SQLAlchemy, variáveis de ambiente, JWT, hash e tratamento de erros. |

### Regras de negócio implementadas

- **E-mails únicos:** contas não podem repetir o mesmo e-mail, normalizado em letras minúsculas.
- **Tarefas com proprietário:** o ID do usuário é obtido do token, não informado no JSON de criação.
- **Status inicial:** toda tarefa é criada como `pendente`.
- **Conclusão e reabertura:** concluir registra a data/hora; reabrir apaga essa data.
- **Tarefas atrasadas:** uma tarefa pendente com `prazo` anterior à data atual é considerada atrasada.
- **Acesso restrito:** as operações de tarefas usam o usuário autenticado e impedem acesso a tarefas de terceiros.

> **Observação de compatibilidade com os manuais:** os exercícios dos Dias 6–14 escrevem os endpoints de tarefas como `/tasks` (por exemplo, `GET /tasks/analytics`), enquanto os arquivos reais em `app/api/routers/tasks.py` usam o prefixo **`/tarefas`**. Por isso os exemplos deste README usam `/tarefas`; uma chamada a `/tasks` não corresponde às rotas do código enviado. Antes de integrar um front-end ou submeter a testes externos baseados no manual, é necessário alinhar essa diferença.

### Principais tecnologias

Python (o ambiente incluído no ZIP indica **3.13.7**), FastAPI, Uvicorn, SQLAlchemy 2, Pydantic 2, SQLite, PostgreSQL com Psycopg 3, PyJWT, bcrypt, python-dotenv e Pandas. `pytest` e `httpx` constam nas dependências, mas não foram encontrados arquivos de testes automatizados no ZIP.

---

## 2. Pré-requisitos e instalação

### Requisitos

- **Python 3.13** (versão identificada no ambiente virtual fornecido; confirme compatibilidade se utilizar outra versão).
- `pip` e um terminal (PowerShell, CMD, Bash etc.).
- Git, caso deseje clonar o repositório.
- Acesso à internet na primeira instalação, para obter as dependências.
- Não é necessário instalar PostgreSQL para executar o **caminho SQLite**.

### Instalação no Windows (PowerShell)

1. Coloque os arquivos do backend numa pasta e abra o terminal **na pasta que contém `requirements.txt` e `app/`**.
2. Crie e ative um ambiente virtual novo:

   ```powershell
   py -3.13 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   Se o comando `py -3.13` não existir, utilize `python -m venv .venv` com a versão de Python instalada.

3. **Antes de instalar**, abra `requirements.txt` e corrija `uvicorn[standart]==0.52.4` para `uvicorn[standard]==0.52.4` (o extra se escreve `standard`). Em seguida, execute:

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

   > Sem a correção do `requirements.txt`, o pacote-base pode ser instalado com aviso, mas os extras do Uvicorn não ficam garantidos.

4. Copie o exemplo de configuração:

   ```powershell
   Copy-Item .env.example .env
   ```

5. **Revise `.env` manualmente** antes de iniciar: o `.env.example` original contém duas linhas `DATABASE_URL`, uma linha `JWT EXPIRA MINUTOS` com nome incorreto e CORS com barra final. Use as variáveis e os valores válidos da seção 3. Não reaproveite cegamente os valores de demonstração do exemplo.
6. Verifique se `DATABASE_URL` aponta para o banco pretendido e gere um `JWT_SECRET` exclusivo e forte.
7. Execute a API **a partir da raiz do projeto**:

   ```powershell
   python -m uvicorn app.main:app --reload
   ```

8. Abra a documentação automática: **http://127.0.0.1:8000/docs**.

### Instalação no Linux/macOS

```bash
python3.13 -m venv .venv   # ou python3, com versão compatível
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
# Corrija requirements.txt e edite .env conforme a seção 3
python -m uvicorn app.main:app --reload
```

### Endereços úteis

| Endereço local | Utilidade |
|---|---|
| `http://127.0.0.1:8000/` | Verificar se a API responde. |
| `http://127.0.0.1:8000/docs` | Documentação interativa Swagger UI. |
| `http://127.0.0.1:8000/redoc` | Documentação alternativa ReDoc. |
| `http://127.0.0.1:8000/openapi.json` | Especificação OpenAPI. |

A rota `/` devolve `{"mensagem":"Todo List API no ar","documentacao":"/docs"}`. Ela confirma que o servidor responde, mas não equivale a uma checagem completa de saúde do banco.

> **Importante:** sem `DATABASE_URL` a importação da aplicação falha; com `JWT_SECRET` ausente ou inferior a 32 caracteres a inicialização falha. A aplicação usa `Base.metadata.create_all()` para criar as tabelas ausentes, **não** para migrar tabelas existentes. Para ver os logs de erros, mantenha o terminal do servidor aberto.
>
> **Distribuição:** não entregue `.env`, `venv/`, `.venv/`, `.git/` como parte de um pacote público nem dados reais de `todo_list.db`. O `.gitignore` original cobre `venv/`, mas **não** `.venv/`; adicione `.venv/` se usar o nome recomendado acima.

---

## 3. Dois caminhos de banco: SQLite e PostgreSQL no Render

Os dados são manipulados pelo SQLAlchemy. A seleção do banco é feita pela variável `DATABASE_URL`.

### Caminho A — SQLite (local)

No arquivo `.env`, configure:

```dotenv
DATABASE_URL=sqlite:///./todo_list.db
JWT_SECRET=COLOQUE_AQUI_UM_SEGREDO_SEGURO_COM_PELO_MENOS_32_CARACTERES
JWT_EXPIRA_MINUTOS=120
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Gere um segredo real (não copie o valor fictício acima):

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Em seguida, execute `python -m uvicorn app.main:app --reload`. O SQLite utiliza um arquivo `todo_list.db` na pasta de execução. As tabelas `usuarios` e `tarefas` são criadas automaticamente caso ainda não existam.

**Persistência:** os registros permanecem no arquivo SQLite entre reinicializações, desde que o arquivo não seja excluído e a aplicação continue usando o mesmo caminho. O banco incluído no ZIP pode conter dados locais; não o inclua em uma distribuição pública sem verificar seu conteúdo.

**Como confirmar o caminho SQLite:** a aplicação usa `sqlite:///./todo_list.db`; por ser um caminho relativo, execute os comandos na **raiz do backend**, ao lado de `requirements.txt`.

### Caminho B — PostgreSQL no Render

1. Crie um banco **Render Postgres** no painel do Render.
2. Crie ou configure um **Web Service** para executar a API.
3. Defina as variáveis do serviço, usando os dados de conexão fornecidos pelo Render:

   ```dotenv
   DATABASE_URL=postgresql+psycopg://USUARIO:SENHA@HOST/BANCO?sslmode=require
   JWT_SECRET=SEGREDO_FORTE_GERADO_PARA_PRODUCAO
   JWT_EXPIRA_MINUTOS=120
   CORS_ORIGINS=https://SEU_FRONTEND.onrender.com
   ```

4. Confirme que o serviço instala as dependências do `requirements.txt`. Um comando de build possível é:

   ```bash
   pip install -r requirements.txt
   ```

5. Configure o comando de inicialização para escutar na porta fornecida pelo ambiente:

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

6. Publique o serviço e acesse `https://SUA-API.onrender.com/docs` para validar a implantação.

**Observações:**

- A URL para SQLAlchemy/Psycopg 3 utiliza o esquema `postgresql+psycopg://`.
- Use preferencialmente a URL de conexão **interna** do Render quando o serviço e o banco forem compatíveis com esse acesso. Os parâmetros SSL dependem da URL e do modo de conexão efetivamente fornecidos pelo ambiente; não adicione `?sslmode=require` cegamente a uma URL que já possui parâmetros.
- O banco deve estar acessível ao serviço e as credenciais precisam ser definidas como variáveis de ambiente, **nunca em código versionado**.
- **Não foi localizado `render.yaml` nem evidência de um deploy concluído no ZIP.** Os comandos acima são uma orientação baseada na estrutura FastAPI existente e precisam ser validados no Render.

| Característica | SQLite local | PostgreSQL no Render |
|---|---|---|
| Conexão | Arquivo `.db` | Servidor PostgreSQL |
| Configuração | Simples | Exige credenciais e serviço de banco |
| Uso sugerido | Desenvolvimento e estudos | Publicação e armazenamento remoto |
| Configuração de URL | `sqlite:///./todo_list.db` | `postgresql+psycopg://...` |

---

## 4. Autenticação: como obter e enviar o token

O sistema utiliza senhas protegidas por **bcrypt** e tokens **JWT assinados com HS256**. O prazo de validade padrão é configurado por `JWT_EXPIRA_MINUTOS` (**120 minutos**, se não alterado). As rotas de tarefas são privadas.

### 4.1 Cadastrar um usuário

**`POST /usuarios`** — não requer autenticação.

```http
POST /usuarios HTTP/1.1
Content-Type: application/json
```

```json
{
  "nome": "Pessoa Exemplo",
  "email": "pessoa@example.com",
  "senha": "SenhaFicticia123"
}
```

Sucesso: **`201 Created`**, retornando os dados públicos do usuário. O campo `senha` **não é retornado**.

### 4.2 Fazer login

**`POST /usuarios/login`** — não requer autenticação.

```json
{
  "email": "pessoa@example.com",
  "senha": "SenhaFicticia123"
}
```

Exemplo da estrutura de resposta **`200 OK`**:

```json
{
  "accessToken": "TOKEN_JWT_RECEBIDO_NO_LOGIN",
  "tokenType": "bearer",
  "expiraEm": "2026-11-25T18:00:00Z",
  "usuario": {
    "id": 1,
    "nome": "Pessoa Exemplo",
    "email": "pessoa@example.com",
    "criadoEm": "2026-11-25T15:00:00Z"
  }
}
```

> **Atenção aos nomes corretos:** a rota é **`/usuarios/login`** (sem acento), e a resposta pública usa **`accessToken`** em `camelCase` (com dois “s” em `access`), não `access_token` nem `acessToken`. Há erros de digitação na descrição do Swagger dentro de `app/main.py`; use os nomes de rota e de campo documentados aqui e nos schemas.

### 4.3 Enviar o token

O cliente deve incluir o cabeçalho em cada rota protegida:

```http
Authorization: Bearer TOKEN_JWT_RECEBIDO_NO_LOGIN
```

Exemplo usando `curl`:

```bash
curl -H "Authorization: Bearer SEU_TOKEN" http://127.0.0.1:8000/usuarios/me
```

**Teste completo em PowerShell (Windows)** — após iniciar a API e cadastrar um usuário via `POST /usuarios` ou pelo Swagger:

```powershell
$credenciais = @{ email = "pessoa@example.com"; senha = "SenhaFicticia123" } | ConvertTo-Json
$sessao = Invoke-RestMethod -Uri "http://127.0.0.1:8000/usuarios/login" -Method Post -ContentType "application/json" -Body $credenciais
$token = $sessao.accessToken
Invoke-RestMethod -Uri "http://127.0.0.1:8000/usuarios/me" -Headers @{ Authorization = "Bearer $token" }
Invoke-RestMethod -Uri "http://127.0.0.1:8000/tarefas/resumo" -Headers @{ Authorization = "Bearer $token" }
```

Alternativamente, use `http://127.0.0.1:8000/docs`: abra `POST /usuarios`, faça o cadastro; execute `POST /usuarios/login`, copie o `accessToken`, pressione **Authorize** e informe o token. Não publique tokens de sessão em prints ou commits.

### 4.4 Restrições de cadastro e sessão

- Nome: de **1 a 120 caracteres**; não aceita apenas espaços.
- E-mail: formato válido e exclusivo por usuário.
- Senha de cadastro: **mínimo 6 caracteres** e **máximo 72 bytes UTF-8** (limite do bcrypt).
- Token sem autorização, inválido ou expirado: **`401 Unauthorized`**.
- E-mail já cadastrado: **`409 Conflict`**.
- Não foi encontrado endpoint de recuperação de senha ou renovação de token.

---

## 5. Tabela de endpoints

**URL-base local:** `http://127.0.0.1:8000`  
**URL-base de produção:** depende do serviço Render; não informada no material recebido.

| Método | Endpoint | Função | Autenticação | Sucesso |
|---|---|---|---|---|
| `GET` | `/` | Verificar o status da API | Pública | `200` |
| `POST` | `/usuarios` | Cadastrar usuário | Pública | `201` |
| `POST` | `/usuarios/login` | Fazer login e obter JWT | Pública | `200` |
| `GET` | `/usuarios/me` | Consultar usuário autenticado | Bearer | `200` |
| `POST` | `/tarefas` | Criar tarefa | Bearer | `201` |
| `GET` | `/tarefas` | Listar tarefas, filtrar, ordenar e paginar | Bearer | `200` |
| `GET` | `/tarefas/resumo` | Obter totais do painel | Bearer | `200` |
| `GET` | `/tarefas/analytics` | Obter métricas calculadas com Pandas | Bearer | `200` |
| `GET` | `/tarefas/{tarefa_id}` | Consultar uma tarefa | Bearer | `200` |
| `PATCH` | `/tarefas/{tarefa_id}` | Atualizar parcialmente uma tarefa | Bearer | `200` |
| `DELETE` | `/tarefas/{tarefa_id}` | Excluir uma tarefa | Bearer | `204` |

### Filtros, ordenação e paginação — `GET /tarefas`

| Parâmetro | Tipo / valores | Padrão | Comportamento |
|---|---|---|---|
| `status` | `pendente`, `concluida` | Não aplicado | Filtra por situação. |
| `prioridade` | `baixa`, `media`, `alta`, `urgente` | Não aplicado | Filtra por prioridade. |
| `prazo` | Data `AAAA-MM-DD` | Não aplicado | Limita a tarefas com prazo até a data informada. |
| `busca` | Texto de até 200 caracteres | Não aplicado | Procura no título sem diferenciar maiúsculas e minúsculas. |
| `ordenarPor` | `criadoEm`, `prazo`, `prioridade` | `criadoEm` | Define a coluna de ordenação. |
| `ordem` | `asc`, `desc` | `desc` | Define o sentido da ordenação. |
| `limit` | Inteiro de 1 a 1000 | `100` | Quantidade máxima de tarefas retornadas. |
| `offset` | Inteiro maior ou igual a 0 | `0` | Quantidade de registros a pular. |

Exemplo de consulta:

```http
GET /tarefas?status=pendente&prioridade=alta&ordenarPor=criadoEm&ordem=desc&limit=10&offset=0
Authorization: Bearer SEU_TOKEN
```

A API devolve uma **lista JSON** no corpo (`[]` quando não há tarefas); não há objeto com chave `items` ou `data`. O total de registros que correspondem ao filtro é enviado no cabeçalho **`X-Total-Count`**, antes da aplicação de `limit` e `offset`. O middleware CORS expõe esse cabeçalho ao navegador.

### Indicador com período — `GET /tarefas/analytics`

Aceita `dias` de **1 a 90**, com valor padrão **7**. Exemplo: `GET /tarefas/analytics?dias=30`.

---

## 6. Contrato JSON

A aplicação usa **`camelCase`** nos nomes públicos dos campos JSON, mesmo que os atributos internos em Python estejam em `snake_case`.

### 6.1 Tarefas — criação

**`POST /tarefas`**, JSON de entrada:

```json
{
  "titulo": "Estudar para a prova",
  "prioridade": "alta",
  "prazo": "2026-11-30"
}
```

Somente `titulo` é obrigatório. Quando omitida, `prioridade` assume `media`; `prazo` pode ser `null`. O cliente **não** envia `usuarioId` nem `status` na criação.

### 6.2 Usuários — resposta de cadastro e campos públicos

O cadastro e a rota `/usuarios/me` devolvem o mesmo formato de usuário (sem senha nem hash):

```json
{
  "id": 1,
  "nome": "Pessoa Exemplo",
  "email": "pessoa@example.com",
  "criadoEm": "2026-11-25T15:00:00Z"
}
```

O login devolve `accessToken`, `tokenType`, `expiraEm` e `usuario` (como mostrado na seção 4). Esses nomes são essenciais para a integração.

### 6.3 Tarefas — resposta

Resposta ilustrativa **`201 Created`**:

```json
{
  "id": 1,
  "usuarioId": 1,
  "titulo": "Estudar para a prova",
  "status": "pendente",
  "prioridade": "alta",
  "prazo": "2026-11-30",
  "criadoEm": "2026-11-25T15:00:00Z",
  "atualizadoEm": "2026-11-25T15:00:00Z",
  "concluidaEm": null
}
```

| Campo | Tipo | Observações |
|---|---|---|
| `id` | Inteiro | Identificador da tarefa. |
| `usuarioId` | Inteiro | Proprietário definido pelo backend. |
| `titulo` | String | De 1 a 200 caracteres. |
| `status` | Enum | `pendente` ou `concluida`. |
| `prioridade` | Enum | `baixa`, `media`, `alta` ou `urgente`. |
| `prazo` | Data ou `null` | Data no formato ISO `AAAA-MM-DD`. |
| `criadoEm` | Data/hora | Horário serializado com informação de fuso UTC. |
| `atualizadoEm` | Data/hora | Última alteração. |
| `concluidaEm` | Data/hora ou `null` | Definida ao concluir e apagada ao reabrir. |

### 6.4 Atualização parcial — `PATCH /tarefas/{tarefa_id}`

Somente os campos enviados são alterados:

```json
{
  "titulo": "Revisar conteúdo de Python",
  "status": "concluida",
  "prioridade": "urgente"
}
```

Para remover um prazo, envie `{"prazo": null}`. **Não envie `null` para `status` ou `prioridade` no PATCH atual**: embora esses valores passem pelo schema, `status: null` causa erro `500` e `prioridade: null` é recusado como `422` pelo modelo, em vez de uma validação consistente na entrada. Para limpar um título não há operação prevista; títulos vazios são recusados. A exclusão (`DELETE`) retorna **`204 No Content`** e **nenhum JSON**.

### 6.5 Resumo — `GET /tarefas/resumo`

```json
{
  "total": 12,
  "pendentes": 7,
  "concluidas": 5,
  "atrasadas": 2
}
```

Valores ilustrativos; a API calcula os números somente a partir das tarefas do usuário autenticado.

### 6.6 Erros e códigos HTTP

| Código | Situação no backend |
|---|---|
| `400` | Erro de domínio genérico. |
| `401` | Login inválido, token ausente, expirado ou inválido. |
| `403` | Tentativa de acessar tarefa pertencente a outro usuário. |
| `404` | Recurso/tarefa não encontrado. |
| `409` | E-mail já cadastrado. |
| `422` | Falha de validação ou violação de regra de negócio. |
| `500` | Falha inesperada, não tratada como erro de domínio. |

Exemplo de resposta de validação **`422`**:

```json
{
  "detail": "O campo 'titulo' é obrigatório.",
  "erros": [
    {"campo": "titulo", "mensagem": "O campo 'titulo' é obrigatório."}
  ]
}
```

O tratamento de erros Pydantic em `app/main.py` devolve `detail` em português e uma lista `erros`. Erros de domínio retornam normalmente `{"detail":"mensagem"}`. A situação de `500` não tem contrato de erro público específico. O texto de erros de valores de enumeração pode sair mal formatado na versão enviada, pois a rotina atual percorre os caracteres da descrição das opções.

---

## 7. Análises do Analytics

**Endpoint real:** `GET /tarefas/analytics?dias=7` — autenticado.

As análises são calculadas no servidor a partir de todas as tarefas **do usuário autenticado**, convertidas para um `pandas.DataFrame` em `app/services/analytics.py`.

| Indicador JSON | Definição implementada |
|---|---|
| `total` | Número total de tarefas do usuário. |
| `concluidas` | Número de tarefas com status `concluida`. |
| `taxaConclusao` | `concluidas / total * 100`, arredondado; `0` se o total for `0`. |
| `concluidasNaJanela` | Soma das conclusões na janela de `dias` dias. |
| `concluidasPorDia` | Lista de objetos `{dia, quantidade}` cobrindo cada dia da janela, inclusive dias sem conclusão. |
| `pendentesPorPrioridade` | Quantidade de tarefas pendentes em cada prioridade. |
| `tempoMedioConclusaoDias` | Média de dias entre criação e conclusão; `null` se não houver conclusões válidas. |
| `concluidasPorDiaDaSemana` | Total histórico de conclusões para `Seg`, `Ter`, `Qua`, `Qui`, `Sex`, `Sáb`, `Dom`. |
| `percentualNoPrazo` | Percentual de tarefas concluídas com prazo que foram finalizadas até o dia do prazo; `null` se nenhuma concluída tiver prazo. |

**Importante:** só `concluidasPorDia` e `concluidasNaJanela` usam a janela temporal definida por `dias`; os demais indicadores consideram o histórico completo do usuário. A contagem considera o fuso local do servidor conforme a implementação atual.

**Comparação com o manual do Dia 14:** o roteiro pede arredondar `tempoMedioConclusaoDias` para **uma casa decimal** e usar as chaves **`seg`, `ter`, `qua`, `qui`, `sex`, `sab`, `dom`** em `concluidasPorDiaDaSemana`. O backend enviado, porém, devolve a média sem `round(..., 1)` e usa **`Seg`, `Ter`, `Qua`, `Qui`, `Sex`, `Sáb`, `Dom`**. Os exemplos abaixo refletem **a implementação recebida**. Ajuste o código se o professor ou o front-end exigir o contrato do manual.

Exemplo ilustrativo para `?dias=3`:

```json
{
  "total": 5,
  "concluidas": 3,
  "taxaConclusao": 60,
  "concluidasNaJanela": 2,
  "concluidasPorDia": [
    {"dia": "2026-11-23", "quantidade": 0},
    {"dia": "2026-11-24", "quantidade": 1},
    {"dia": "2026-11-25", "quantidade": 1}
  ],
  "pendentesPorPrioridade": {
    "urgente": 0,
    "alta": 1,
    "media": 1,
    "baixa": 0
  },
  "tempoMedioConclusaoDias": 1.5,
  "concluidasPorDiaDaSemana": {
    "Seg": 0,
    "Ter": 1,
    "Qua": 2,
    "Qui": 0,
    "Sex": 0,
    "Sáb": 0,
    "Dom": 0
  },
  "percentualNoPrazo": 100
}
```

> Os valores acima são apenas uma demonstração do **formato** do contrato, não resultados de um banco real.

---

## 8. Integração com o front-end React

### Situação real do front-end enviado

O projeto `todo-list-main-completo-uc-01.rar` contém um **front-end React 19 + Vite 6** com telas de cadastro, login, lista de tarefas, painel, Analytics e recuperação de senha. A verificação dos arquivos `src/services/taskService.js`, `src/services/usuarioService.js`, `src/services/mockStorage.js`, `src/context/AuthContext.jsx` e das páginas mostrou que **a integração com a API Python ainda não foi implementada**:

- `usuarioService` e `taskService` leem e gravam **dados fictícios no `localStorage`**; não há chamadas HTTP reais aos endpoints FastAPI.
- `AuthContext` autentica comparando credenciais locais e persiste um **ID de usuário**, não o token JWT emitido pelo backend.
- `useTasks` filtra e ordena as tarefas **no navegador**; a paginação e o `X-Total-Count` do servidor ainda não são usados.
- `DashboardPage` e `AnalyticsPage` calculam seus indicadores no cliente; **não utilizam** `/tarefas/resumo` e `/tarefas/analytics`.
- A página `/recuperar-senha` é apenas **simulada** e não envia e-mail. A API também não oferece um endpoint para recuperação de senha.

> **Importante:** as rotas **de navegação do React** (`/dashboard`, `/tasks`, `/analytics`) são diferentes das **rotas HTTP da API** (`/tarefas`, `/tarefas/resumo`, `/tarefas/analytics`). A página React `/tasks` pode conservar esse endereço; o cliente HTTP deve chamar `/tarefas` no backend analisado. Os manuais usam `/tasks` como endpoint da API, mas esse prefixo não está implementado no backend enviado.

### Tabela obrigatória: função real do front-end → endpoint da API

A tabela relaciona **arquivos/funções encontrados no React** com o endpoint FastAPI **correspondente à integração futura**. A coluna de estado evita confundir o mapeamento planejado com uma implementação pronta.

| Função ou tela no React (arquivo) | Endpoint correspondente no backend | Estado atual / adaptação necessária |
|---|---|---|
| Cadastro: `AuthContext.cadastrar()` → `usuarioService.criar()` (`CadastroForm.jsx`) | `POST /usuarios` | **Mock**. Enviar `{nome, email, senha}` à API; após cadastrar, chamar login, pois o cadastro do backend não fornece JWT. |
| Login: `AuthContext.login()` → `usuarioService.verificarCredenciais()` (`LoginForm.jsx`) | `POST /usuarios/login` | **Mock**. Ler `accessToken` da resposta; o login real precisa de token JWT. |
| Restaurar sessão: `AuthContext` + `authStorage.js` | `GET /usuarios/me` | **Mock**. Em vez de confiar só em ID salvo, validar token e carregar o usuário pela API. |
| Listagem, filtros e busca: `useTasks()` / `TasksPage.jsx` | `GET /tarefas` | **Mock**. Substituir `listarPorUsuario` por requisição autenticada; passar `status`, `prioridade`, `busca`, `prazo`, `ordenarPor`, `ordem`, `limit`, `offset` e ler `X-Total-Count` conforme a interface. |
| Criar: `useCriarTask()` → `taskService.criar()` (`TaskForm.jsx`) | `POST /tarefas` | **Mock**. Enviar `titulo`, `prioridade`, `prazo`; **não enviar `usuarioId`**, pois o backend identifica o proprietário pelo Bearer token. |
| Detalhes da tarefa: `TaskCard.jsx` / edição | `GET /tarefas/{tarefa_id}` | **Endpoint disponível**. Implementar chamada quando for necessário obter a tarefa individualmente; atualmente as telas usam o objeto já carregado. |
| Editar, concluir e reabrir: `useAtualizarTask()` → `taskService.atualizar()` | `PATCH /tarefas/{tarefa_id}` | **Mock**. Enviar apenas os campos modificados, inclusive `status`, observando as limitações de `null` descritas na seção 9. |
| Excluir: `useExcluirTask()` → `taskService.remover()` | `DELETE /tarefas/{tarefa_id}` | **Mock**. Esperar HTTP `204 No Content`, sem tentar ler JSON da resposta. |
| Cards do painel: `DashboardPage.jsx` | `GET /tarefas/resumo` | **Cálculo local**. Trocar contagens feitas no navegador pelos dados `total`, `pendentes`, `concluidas`, `atrasadas` do servidor. |
| Próximas tarefas: `DashboardPage.jsx` | `GET /tarefas` | **Cálculo local**. Obter tarefas autenticadas e usar ordenação/filtros apropriados para o recorte da tela. |
| Gráficos e taxa de conclusão: `AnalyticsPage.jsx` | `GET /tarefas/analytics?dias=7` | **Cálculo local**. Consumir `taxaConclusao`, `concluidasPorDia` e `pendentesPorPrioridade`; o backend também retorna os três insights adicionais do Dia 14. |
| Recuperar senha: `RecuperarSenhaForm.jsx` | **Não há endpoint** | **Simulação**. A tela apenas apresenta uma mensagem de confirmação; não ocorre envio de e-mail ou redefinição real de senha. |

### Como preparar a integração (ainda não aplicada no código enviado)

Na pasta do front-end React, os scripts disponíveis no `package.json` são:

```bash
npm ci
npm run dev
```

O Vite costuma disponibilizar o aplicativo em `http://localhost:5173`. Para criar **uma futura camada HTTP**, defina no front-end um arquivo `.env.local` com uma URL pública de desenvolvimento (sem segredos):

```dotenv
VITE_API_URL=http://127.0.0.1:8000
```

> Só adicionar `VITE_API_URL` **não integra o front-end automaticamente**: os serviços ainda devem ser alterados para usar `fetch` e tratar as respostas. Não há uso dessa variável no código React recebido.

Exemplo **proposto**, não presente atualmente em `src/services/usuarioService.js`:

```javascript
const API_URL = import.meta.env.VITE_API_URL;

export async function entrarNaApi(email, senha) {
  const resposta = await fetch(`${API_URL}/usuarios/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, senha }),
  });

  const dados = await resposta.json();
  if (!resposta.ok) throw new Error(dados.detail ?? 'Falha no login.');
  return dados; // { accessToken, tokenType, expiraEm, usuario }
}

export async function listarNaApi(token, filtros = {}) {
  const params = new URLSearchParams(filtros);
  const resposta = await fetch(`${API_URL}/tarefas?${params}`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!resposta.ok) {
    const erro = await resposta.json().catch(() => ({}));
    throw new Error(erro.detail ?? `Erro HTTP ${resposta.status}`);
  }

  return {
    tarefas: await resposta.json(),
    total: Number(resposta.headers.get('X-Total-Count') ?? 0),
  };
}
```

**Pontos essenciais para a integração real:**

1. Alterar `src/services/usuarioService.js` e `src/services/taskService.js` para realizar requisições HTTP e retirar a dependência dos dados simulados.
2. Substituir o login/sessão local de `AuthContext.jsx` por autenticação com JWT, mantendo o token protegido e validando-o em `/usuarios/me`.
3. Ajustar `useCriarTask.js` para **não enviar `usuarioId`**. A API obtém o usuário a partir do token; os IDs reais de usuário e tarefa são numéricos, enquanto os IDs do mock são strings como `usuario-1` e `task-1`.
4. Adaptar `useTasks.js`, `DashboardPage.jsx` e `AnalyticsPage.jsx` para usar os resultados reais; respeitar paginação e diferenças de estrutura do Analytics.
5. Configurar `CORS_ORIGINS=http://localhost:5173` no backend local (sem barra final); o token deve ir no header `Authorization: Bearer ...`.
6. Tratar `401`, `403`, `404`, `409`, `422` e `204` e exibir carregamento/erro nos componentes já existentes.
7. Testar a integração de ponta a ponta com a API executando e dois usuários diferentes. **Esse teste ainda não foi realizado** com os materiais recebidos.

---

## 9. Limitações conhecidas e correções recomendadas

Esta seção é deliberadamente transparente: relaciona **pontos verificados pela inspeção do ZIP** e aspectos que ainda exigem testes, sem afirmar que uma funcionalidade inexistente foi concluída.

| Situação observada | Impacto | Ação recomendada |
|---|---|---|
| Não foram encontrados arquivos de testes no projeto compartilhado. | Não há evidências de cobertura automatizada, embora `pytest` e `httpx` estejam no `requirements.txt`. | Criar testes para autenticação, CRUD, validações e Analytics. |
| Criação de tabelas com `Base.metadata.create_all()` e ausência de migrações no ZIP. | Mudanças futuras de esquema não são migradas automaticamente. | Adotar migrações versionadas (ex.: Alembic), se necessário. |
| Nenhuma rota de renovação de token ou recuperação de senha identificada. | Sessão expirada exige novo login; não há recuperação de senha pela API atual. | Planejar funcionalidades somente se fizerem parte do escopo. |
| Front-end React recebido, mas ainda baseado em `localStorage` (`src/services/taskService.js` e `usuarioService.js`). | As telas não fazem requisições à API Python; login, tarefas, painel e Analytics operam no mock. | Implementar cliente HTTP, JWT e substituir os cálculos locais, conforme a tabela da seção 8. |
| O mock React mantém credenciais em texto puro no armazenamento local e a conta demo tem senha fixa. | Adequado apenas para demonstração isolada; não deve ser usado como autenticação real ou em produção. | Remover o mock na integração, utilizar a API com bcrypt e nunca armazenar senhas no front-end. |
| A tela React de recuperação de senha apenas simula o envio; o backend não tem rota correspondente. | Não existe redefinição real de senha. | Manter como demonstração claramente sinalizada ou implementar o fluxo em etapa futura. |
| Não foi identificado `render.yaml` ou URL de deploy validada. | O funcionamento em produção não foi comprovado pelo material analisado. | Configurar e testar serviço no Render. |
| Dependência `uvicorn[standart]` escrita incorretamente no `requirements.txt`. | O extra `standard` pode não ser instalado como pretendido. | Corrigir para `uvicorn[standard]`. |
| A configuração padrão de CORS em `app/core/config.py` contém `http://localhost:5173/` (com barra final). | A origem do navegador costuma chegar sem essa barra e pode não coincidir. | Definir `CORS_ORIGINS=http://localhost:5173` explicitamente e corrigir o padrão. |
| O `.env.example` contém `DATABASE_URL` duplicada e `JWT EXPIRA MINUTOS` em vez de `JWT_EXPIRA_MINUTOS`. | A instalação por cópia direta pode carregar parâmetros incorretos. | Deixar uma única `DATABASE_URL` ativa e definir `JWT_EXPIRA_MINUTOS=120`. |
| `PATCH /tarefas/{tarefa_id}` aceita `null` para `status` e `prioridade` no schema, mas o serviço trata esses casos de forma inconsistente. | `status: null` provoca `500`; `prioridade: null` gera `422` por erro de domínio. | Validar esses campos na entrada ou tratar explicitamente `null`. |
| `app/main.py` descreve `/usuários/login` e `acessToken`, diferentes de `/usuarios/login` e `accessToken` reais. | Pode confundir quem usa a documentação Swagger. | Corrigir texto explicativo do FastAPI. |
| `app/main.py` formata a mensagem de erro de enum percorrendo caracteres de uma string. | Mensagens de enum podem ficar ilegíveis. | Ajustar construção da mensagem de validação. |
| O ZIP enviado contém `.env`, `venv/`, `.git/` e `todo_list.db`. | Pode incluir dados locais e material sensível; o pacote fica desnecessariamente grande. | Não compartilhar segredos ou banco local; distribuir somente o código e o exemplo sanitizado. |
| Manuais usam `/tasks`, mas o código usa `/tarefas`. | Requisições copiadas diretamente dos manuais podem resultar em 404, e o front React precisa usar o prefixo real. | Alinhar o contrato público antes da integração; não alterar silenciosamente nomes de rotas. |
| O Analytics do Dia 14 difere do manual no arredondamento da média e nas chaves dos dias da semana. | O contrato pode não coincidir com o formato exigido nas verificações da disciplina. | Arredondar `tempoMedioConclusaoDias` a uma casa e padronizar chaves para `seg` a `dom`, se for necessário seguir exatamente o roteiro. |
| O manual do Dia 14 menciona um script cliente e a biblioteca `requests`, mas não foram encontrados no ZIP compartilhado. | A entrega do cliente não está comprovada. | Conferir com o professor se o script cliente também é item obrigatório da entrega final e incluí-lo se necessário. |

**Erro confirmado por inspeção de código:** `app/services/usuario.py` usa `TokenInvalido` em `usuario_do_token()` sem importá-lo. Se o token for válido mas o usuário não existir mais, o código pode gerar `NameError` e devolver `500`, em vez do `401` esperado. No início desse arquivo, inclua `TokenInvalido` entre os imports de `app.core.exceptions` e teste o caso.

**Estado dos testes:** rotas, schemas, casos comuns de CRUD e Analytics foram exercitados em um teste isolado com SQLite e autenticação simulada; o `PATCH` com `status: null` retornou `500` e com `prioridade: null` retornou `422`. As versões reais de todas as dependências, o bcrypt e o PostgreSQL/Render **não foram testados ponta a ponta**. O front-end React foi inspecionado estaticamente, mas não foi testado no navegador nem integrado à API: a aplicação enviada usa `localStorage`.

---

## 10. Tabela dos 14 dias de desenvolvimento e entrega

O quadro abaixo segue **a tabela oficial “Fim da construção” (página 16 do *Manual de Construção — Dia 14*)**. Os títulos representam **as atividades planejadas do curso**; o fato de uma funcionalidade aparecer no roteiro não prova, por si só, que todos os testes foram realizados no ambiente final. A coluna “Onde conferir” relaciona essas atividades aos arquivos ou rotas presentes no projeto enviado.

| Dia | Funcionalidade oficial do curso | Onde conferir no backend enviado |
|---|---|---|
| **1** | Consultar se a API está no ar | `GET /` em `app/main.py` e `/docs`. |
| **2** | Criar uma conta | `POST /usuarios`, `app/models/usuario.py`, `app/services/usuario.py`. |
| **3** | Cadastro com e-mail único e erros em português | `EmailJaCadastrado`, `app/main.py`, validadores e tratamento HTTP 409/422. |
| **4** | Entrar no sistema (login) | `POST /usuarios/login`, bcrypt e emissão de JWT. |
| **5** | Ver o meu perfil, autenticado pelo token | `GET /usuarios/me` e dependência `UsuarioAtual`. |
| **6** | Criar uma tarefa | `POST /tarefas` e entidade `Tarefa`. |
| **7** | Listar as minhas tarefas | `GET /tarefas`, com identificação pelo token. |
| **8** | Consultar, editar e excluir uma tarefa | `GET`, `PATCH` e `DELETE /tarefas/{tarefa_id}`; validação do proprietário. |
| **9** | Concluir e reabrir uma tarefa (RN-03) | Métodos de `Tarefa` acionados pelo `PATCH` do campo `status`. |
| **10** | Filtrar e buscar tarefas | Parâmetros `status`, `prioridade`, `prazo` e `busca` em `GET /tarefas`. |
| **11** | Ordenar e paginar a lista (e CORS) | `ordenarPor`, `ordem`, `limit`, `offset`, `X-Total-Count` e `CORSMiddleware`. |
| **12** | Ver os números do Painel | `GET /tarefas/resumo` (`total`, `pendentes`, `concluidas`, `atrasadas`). |
| **13** | Ver as análises da página Analytics (pandas) | `GET /tarefas/analytics` e `app/services/analytics.py`. |
| **14** | Ver insights de produtividade — e entregar | Novos indicadores do Analytics, versão `1.0.0`, documentação `README.md` e conferência de entrega. |

> **Atenção:** nos manuais, os endpoints de tarefas aparecem como `/tasks`; nesta tabela, ao indicar os arquivos concretos, foi utilizado `/tarefas` para reproduzir o código recebido. Os Dias 13 e 14 também exigem conferir os detalhes do contrato Analytics citados na seção 7.

### Verificação do checklist do Dia 14

O manual orienta conferir o seguinte com a aplicação em execução. **Itens verificados por leitura de código não devem ser confundidos com testes completos em execução.**

| Item exigido no manual | Conferência do material recebido |
|---|---|
| `/docs` lista **11 endpoints** (3 de usuários, 7 de tarefas e `GET /`) | Foram identificadas 11 operações HTTP nos routers e em `app/main.py`; a abertura do Swagger com instalação limpa ainda precisa ser repetida no ambiente de entrega. |
| `import pandas` apenas em `app/services/analytics.py` | **Confirmado por busca** nos arquivos `.py` enviados. |
| Nenhum `fastapi` importado em `models/`, `services/` ou `repositories/` | **Confirmado por busca** nos arquivos `.py` enviados. |
| Sem token, a listagem de tarefas responde `401` | A dependência de autenticação prevê `401`; repetir o teste em `/docs`. |
| Token de outro usuário tentando acessar uma tarefa responde `403` | Há regra de domínio e tratamento `403`; repetir com duas contas. |
| Atribuir diretamente `tarefa.status = ...` levanta `AttributeError` | Existe propriedade de status sem setter; validar no ambiente final. |
| Editar o título de tarefa concluída preserva `concluidaEm` | Lógica de atualização separada da transição de status; validar em execução. |
| Nenhuma resposta inclui `senha` ou `senhaHash` | Os schemas públicos enviados não incluem esses campos; conferir cadastro, login e `/usuarios/me`. |
| Erros de validação `422` possuem `detail` em português | Há tratamento personalizado em `app/main.py`; foram identificados problemas no texto para alguns valores de enumeração. |
| Nenhum `.env` versionado e um commit por dia | `.gitignore` contém `.env`, porém o ZIP inclui o arquivo local e o histórico git. **A situação de versionamento e os 14 commits não foi atestada**; executar `git ls-files .env` e `git log --oneline` no repositório do aluno. |

### Checklist manual para o último teste

1. Em um ambiente virtual novo, ajustar `requirements.txt`, `.env` e `CORS_ORIGINS`, instalar as dependências e executar `python -m uvicorn app.main:app --reload`.
2. Abrir `http://127.0.0.1:8000/docs` e testar as 11 operações, cadastro/login e um token inválido.
3. Criar duas contas e tentar consultar a tarefa de outra conta; testar conclusão, reabertura, edição, exclusão, filtros e paginação.
4. Consultar resumo e Analytics, incluindo um usuário sem tarefas ou sem tarefas concluídas com prazo (os indicadores sem base de cálculo devem ser `null`).
5. Conferir o alinhamento de `/tasks` vs. `/tarefas`, as diferenças do Analytics frente ao Dia 14 e as limitações da seção 9.
6. Não publicar `.env`, senhas, tokens, banco local nem `venv/`; conferir o histórico antes de fazer o commit final.

---

**Documentação:** Todo List API — UC 2, Desenvolvedor Full Stack (SENAC Minas Gerais).  
**Versão declarada no FastAPI:** `1.0.0`.  
**Fontes:** `Todo-List-Backend.zip`, `todo-list-main-completo-uc-01.rar` e *Manuais de Construção*, Dias 1–14.  
**Responsável e URL pública do repositório/deploy:** não informados nos materiais.  
**Status do front-end:** interface React funcional com persistência local em `localStorage`, conforme informado pelo desenvolvedor; **não realiza integração HTTP com FastAPI** na versão enviada. O mapeamento função → endpoint está documentado na seção 8.  
**Status do Render:** o README orienta a configuração; URL e teste de deploy não foram fornecidos para conferência.

## 11. Orientações para aplicar as correções (guia complementar, fora dos dez tópicos do curso)

As dez seções exigidas pelo Passo 9 estão preservadas na ordem solicitada. Este complemento **não significa que as correções já foram aplicadas ao código**. Para o procedimento passo a passo, consulte `GUIA_DE_CORRECOES.md`, entregue junto deste README.

**Correções de código a conferir:** `requirements.txt` (`uvicorn[standard]`); `.env.example` (uma `DATABASE_URL`, `JWT_SECRET` seguro, `JWT_EXPIRA_MINUTOS`, CORS sem barra final); `app/services/usuario.py` (importar `TokenInvalido`); `app/core/config.py` (origens CORS); `app/main.py` (textos de documentação e formatação dos erros de enum); `PATCH /tarefas/{tarefa_id}` (tratamento de `null`); e Analytics (formato exigido pelo manual).

**Limitação mantida propositalmente:** o React usa `localStorage`; não declarar integração HTTP/JWT com o backend enquanto ela não existir. **Segurança:** não compartilhar `.env`, `venv/`, `.venv/`, `.git/` nem bancos com dados pessoais.
