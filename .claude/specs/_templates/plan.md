# Plan: [Nome da Feature]

> **Camada 2 de 3 (SDD)** — design técnico derivado de `spec.md` + `documentacao/*-ARCHITECTURE.md`.
> Se a spec mudar, este plan deve ser regenerado/revisado — nunca o contrário.
> **Spec de origem**: `./spec.md` (status deve ser `aprovada`)
> **Status**: `rascunho` | `aprovado`
> **Aprovado pelo usuário em**: [data ou "pendente"] ← gate humano obrigatório

---

## 1. Abordagem

[2-4 frases: estratégia geral. Qual módulo existente serve de referência de padrão
(ex.: "espelhar `donors_collections_motilities`"), o que será criado vs. alterado.]

## 2. Backend

### 2.1 Entidades / Tabelas

**Módulo**: `src/modules/<contexto>/<modulo>/`

| Campo | Tipo TypeORM | Nulável | FK / Observação |
|-------|--------------|---------|-----------------|
| `id` | `uuid` PK | não | ⚠️ **BE-007**: sem `default` e sem `generationStrategy` na migration — o uuid vem do `uuidv4()` da aplicação, no `create` do repositório. Nenhuma função do Postgres (`gen_random_uuid()` nem existe neste banco). |
| ... | ... | ... | ... |
| `user_created` | `varchar` | sim | auditoria (padrão) |
| `user_updated` | `varchar` | sim | auditoria (padrão) |
| `created_at` | `timestamp` | não | auditoria (padrão) |
| `updated_at` | `timestamp` | não | auditoria (padrão) |

### 2.2 Enums

```typescript
// nome, valores e onde ficam
```

### 2.3 Contrato de API

> A coluna **Resposta** não é opcional: é o que o frontend afirma no tipo e nunca confere
> (AG-022). Sem ela, `backend-lead`, `frontend-lead` e `ui-planner` devolvem CONTESTADO.

| Método | Rota | Permissão | Body / Params (campo: tipo) | Resposta |
|--------|------|-----------|------------------------------|----------|
| `GET` | `/<endpoint>` | `<modulo>_view` | query: `search_*`, `page`, `rowsperpage`, `sort_*` | `{ <entities>: I<E>[], <entities>total: number }` |
| `GET` | `/<endpoint>/show/:id` | `<modulo>_view` | — | `{ <entity>: I<E> }` |
| `POST` | `/<endpoint>` | `<modulo>_create` | `nome: string`, `x_id: uuid` | `{ <entity>: I<E> }` |
| `PUT` | `/` | `<modulo>_update` | `<tabela>_id: uuid` (no **body**), ... | `{ <entity>: I<E> }` |
| `DELETE` | `/` | `<modulo>_delete` | `id` por **query string** (array) | `204` |

**Campos da resposta que a tela vai ler** — um por linha, com o tipo. É esta lista que o
`check-module.py --contract` compara depois entre o tipo do frontend e o que o backend devolve:

| Campo | Tipo | De onde vem | Tela que lê |
|-------|------|-------------|-------------|
| `<entity>.<campo>` | `string` | coluna da tabela | Listagem de X |
| `<entity>.<relacao>.<campo>` | `string \| null` | `relations: ['<relacao>']` | Ficha de X |

> Campo que a tela lê e não está aqui é defeito de plan, não de código. Campo que existe na
> resposta e nenhuma tela lê entra como INFO — pode ser backend-only legítimo.

> **Permissões (spec 085, RN-10)**: **módulo novo = `_view/_create/_update/_delete`** (é o que o
> scaffold gera e como os módulos gerados desde junho estão seedados). **Módulo legado = o sufixo
> que as rotas dele já têm** (`_edit` em 77 módulos) — copiar do `accessControl` existente, nunca
> inventar. Formas reais das rotas geradas: `PUT /` com o id no **body** (`<tabela>_id`),
> `DELETE /` com `id` por **query string** (array), só o `show` usa `/show/:id`.

### 2.4 Validações (Joi)

| Campo | Regra Joi |
|-------|-----------|
| ... | ... |

### 2.5 Services

- [ ] `Create<Entity>Service`
- [ ] `Update<Entity>Service`
- [ ] `Show<Entity>Service`
- [ ] `List<Entity>Service`
- [ ] `ListTotal<Entity>Service`
- [ ] `Delete<Entity>Service`
- [ ] [Services adicionais — helpers de cálculo, workflow, etc.]

### 2.6 Migration

**Arquivo**: `CreateTable<Tabelas>`
FKs: `<tabela>.<fk>_id` → `<tabela_ref>.id` — onDelete: `[CASCADE | SET NULL | RESTRICT]`

### 2.7 Mapeamento RN → implementação

> Cada regra de negócio da spec aponta para onde será implementada. Nenhuma RN pode ficar órfã.

| RN | Onde | Como |
|----|------|------|
| RN-01 | `helpers/...` | ... |
| RN-02 | `Update...Service` | ... |

## 3. Frontend

### 3.1 Onde aparece na UI

- **Rota/aba**: ...
- **Página(s)**: `pages/<contexto>/<Modulo>...`

### 3.2 Campos do formulário

| Campo | Componente | Obrigatório | Validação Yup |
|-------|-----------|-------------|----------------|
| ... | ... | ... | ... |

### 3.3 Comportamento

- **Listagem**: [colunas, filtros, ação de clique]
- **Criação/Edição/Exclusão**: [toast, redirect, confirmação]

### 3.4 Telas

> Preenchida pelo **`ui-planner`** ANTES da aprovação do plan (`/spec-plan`). Só entram
> componentes que existem hoje em `styles/global_v2.tsx` / `globalMaterialUi_v2.tsx` — o
> `check-ui-v2-refs.py` reprova nome ou cor inexistente. Tela nova é **sempre v2**.

| Tela | Família v2 | Componentes | Tela canônica de referência |
|------|-----------|-------------|------------------------------|
| Listagem de X | listagem | `ContainerList` › `ListSurface` › `CssDataGrid` | `pages/clinics/ClinicsList` |

**Onde vive o estado** (FE-020 — antecipada para o plan, onde custa uma linha em vez de quatro
rodadas de revisão):

| Estado | Origem | Sobrevive à troca de aba? | Onde vive |
|--------|--------|----------------------------|-----------|
| `filtro` | interação | não precisa | `useState` da listagem |
| `<selecionado>` | resposta da API | **precisa** | sobe para o pai / refeito no `mount` |

> A pergunta que esta tabela responde: *se o usuário trocar de aba e voltar, este valor tem de
> continuar lá?* Se tem, ele não pode morar no `useState` do componente da aba.

### 3.5 Arquivos a criar/alterar

- `types/...`, `services/...`, `constants/...`, `pages/...`
- **Registro** (`src/routes/index.tsx`, `App.tsx`, `menuItens.tsx`): escrito pela **sessão
  principal** depois que os builders terminam — um só escritor nos arquivos que toda feature toca.

## 4. Riscos e pontos de atenção

- [Lessons relevantes a este plan: BE-xxx, FE-xxx, AG-xxx]
- [Partes com maior chance de erro e como mitigar]
