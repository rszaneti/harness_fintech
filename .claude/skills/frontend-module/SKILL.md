---
name: frontend-module
description: Conhecimento de construção de módulo frontend — contrato com a API, dados, fluxo e decisões. O módulo é GERADO por `.claude/scaffold/scaffold.py frontend`; o padrão visual está na skill `ui-v2`. Usar ao criar ou auditar páginas/módulos nos frontends da plataforma de pagamentos (comando /new-frontend-module).
---

# Skill: frontend-module

Scaffold de módulo frontend (`frontend/<ws>/` — `frontend/<ws>` = o workspace de frontend da feature (`frontend/operador` ou `frontend/cliente` — `.claude/workspaces.json`); o scaffold exige `--ws`). **Regra central: NUNCA gerar arquivo de estrutura
do zero e NUNCA copiar de outro módulo existente (AG-002/FE-001..7 — vazamento de imports/campos).
Rodar o scaffold, que copia os templates v2 de `.claude/scaffold/templates/frontend/`, e preencher
só os marcadores de bloco.** Layout é sempre o **v2**: `styles/global_v2`, `styles/globalMaterialUi_v2`
e o tema de `src/theme.ts` (decisão de 2026-09-11); os templates são modelados nas telas canônicas
de Clínicas (`ClinicsList`, `ClinicForm`, `ClinicFormRegisterData`, `ClinicFormContactsList`,
`ClinicFormContactRegister`).

```bash
python3 .claude/scaffold/scaffold.py frontend <contexto> <modulo> <Modulo> --ws <operador|cliente> --label "<Rótulo>" \
    [--endpoint <e>] [--filho <Filho> --filho-label "<Rótulo>"] [--constants]
```

## Placeholders (spec 085 — o script deriva; você não substitui nada à mão)

Exemplo: contexto=`clinics`, modulo=`clinic`, Modulo=`Clinic`, `--label Clínica --filho Contact`

| Placeholder | Significado | Exemplo |
|-------------|-------------|---------|
| `__Modulo__` / `__Modulos__` | PascalCase singular (argumento) / plural (`--plural` sobrescreve) | `Clinic` / `Clinics` |
| `__modulo__` / `__modulos__` | minúsculas: rota do form, chave de resposta e rota de listagem | `clinic` / `clinics` |
| `__MODULO__` | UPPER_SNAKE para constantes | `CLINIC` |
| `__contexto__` | Pasta em `src/pages/<contexto>/` (argumento) | `clinics` |
| `__endpoint__` | Slug da API (`--endpoint`; padrão = `<modulo>`) | `clinic` |
| `__MODULO_LABEL__` / `__TITULO_PT_BR__` | Rótulo PT-BR singular (`--label`) / plural (`--label-plural`) | `Clínica` / `Clínicas` |
| `__registro_id__` | FK do filho e id do update: snake_case do plural + `_id` | `clinics_id` |
| `__Filho__` / `__filho__` / `__Filhos__` / `__filhos__` | Aba filha (`--filho`) | `Contact` / `contact` / `Contacts` / `contacts` |
| `__ModuloFilho__` | Interface do filho (a prop de id do modal é `__modulo____filho__id` → `cliniccontactid`) | `ClinicContact` |
| `__FILHO_LABEL__` / `__registro_filho_id__` | Rótulo do filho (`--filho-label`) / id de update do filho | `Contato` / `clinics_contacts_id` |

**Marcadores de bloco — lista fechada, ficam no arquivo gerado para você preencher** (sempre em
comentário, com um exemplo **declarado** logo abaixo que compila): `__CAMPOS__ __FILTROS__ __COLUNAS__
__CAMPOS_FILHO__ __VALORES__`. Qualquer outro `__X__` faz o script falhar (exit 2). O módulo
gerado com os blocos ainda vazios **passa tsc e eslint** (`--self-test`).

## Pré-requisitos — perguntar ANTES (se não houver plan.md SDD)

1. Identidade: contexto, Modulo, endpoint, rota lista (`/__modulos__`), rota form (`/__modulo__/:register/:id?`)
2. Campos: nome snake_case, tipo TS, obrigatório (Yup), máscara (CPF/CNPJ/celular/CEP/moeda),
   edição inline no grid (só boolean/is_active), coluna no grid, filtro `search_*`
3. Tipo de módulo: **A** CRUD simples | **B** tabs filhas (modal) | **C** filho com upload | **D** máscaras + APIs externas
4. Tabs filhas (B/C): nome, campos, upload?, detail panel?
5. Constants: enums → `src/constants/__Modulo__<Tipo>.ts`
6. Ordenação/filtros padrão

## Ordem de geração (template → destino) — é o que o scaffold produz

Destinos seguem o **canônico de Clínicas**: `types/` e `services/` **planos** (`types/clinics.types.ts`,
não `types/clinics/clinic.types.ts`), páginas em `pages/<contexto>/<Modulos>List/` e
`pages/<contexto>/<Modulo>Form…/`. ⚠️ Até 2026-09-11 esta tabela previa `types/__contexto__/…` e
`pages/__contexto__/__Modulo__/__Modulo__List/` — divergia da base (spec 085). Página v2 **não tem
`styles.ts`** — das 149 pastas que usam os componentes do `globalMaterialUi_v2`, nenhuma tem um
(11/09/2026). A tabela vive no script (`FRONTEND_DEST`); esta cópia é referência.

| # | Template | Destino em `frontend/<ws>/src/` |
|---|----------|----------------------------------|
| 1 | `types.ts.tpl` | `types/__modulos__.types.ts` |
| 2 | `service.ts.tpl` | `services/__modulos__.service.ts` |
| 3 | `constants.ts.tpl` *(só `--constants`)* | `constants/__Modulo__Type.ts` |
| 4 | `context-modal.tsx.tpl` *(só `--filho`)* | `context/__Modulo__ModalContext.tsx` |
| 5 | `list-index.tsx.tpl` | `pages/__contexto__/__Modulos__List/index.tsx` |
| 6 | `form-index.tsx.tpl` | `pages/__contexto__/__Modulo__Form/index.tsx` |
| 7 | `form-register-data-index.tsx.tpl` | `pages/__contexto__/__Modulo__FormRegisterData/index.tsx` |
| 8 | `child-list-index.tsx.tpl` *(só `--filho`)* | `pages/__contexto__/__Modulo__Form__Filho__/__Modulo__Form__Filhos__List/index.tsx` |
| 9 | `child-register-index.tsx.tpl` *(só `--filho`)* | `pages/__contexto__/__Modulo__Form__Filho__/__Modulo__Form__Filho__Register/index.tsx` |

## Regras críticas (nunca violar)

| Regra | Detalhe |
|-------|---------|
| DataGridPro | Sempre `DataGridPro`, nunca `DataGrid` |
| Formik | Sempre Formik + Yup. Nunca react-hook-form. Nunca useState para form (exceção: `isActive`) |
| enableReinitialize | Apenas quando `register === 'edit'` / `isEdit` |
| load<Entidade> | `useCallback` FORA do `useEffect`, chamada dentro |
| Erros HTTP | Sempre `ErrorMessage(err)` do `ErrorContext` |
| Toast | `toast.success('...', { position: toast.POSITION.TOP_CENTER })` |
| Delete | Sempre `window.confirm('Deseja realmente deletar este registro?')` |
| Imports | Relativos (`../../`). Nunca alias `@/` |
| Idioma | UI em PT-BR; código em inglês |
| Pós-insert | `history.push('/__modulo__/edit/${created.id}')` |
| Tab filha | `disabled={!isEdit}`; lista filha recarrega ouvindo `openModal` no useEffect |
| Router | v5: `useHistory`, `useParams`, `Switch`, `Route` (NÃO v6) |
| MUI v7 | `slotProps` (nunca `inputProps` — FE-009, hook bloqueia) |
| Máscaras | Limpar com `replaceSpecialChars` antes de enviar à API |
| Visual | **v2 sempre** — `styles/global_v2`, `styles/globalMaterialUi_v2`, tema de `src/theme.ts`. Ver a skill **`ui-v2`** |
| Tamanho de fonte | Piso de **1.2rem** (= 12px), FE-019 — o hook bloqueia. Escala e a dívida do `htmlFontSize` em `ui-v2/references/paleta.md` |

## Visual: a skill `ui-v2`

Layout, componentes, tokens, cores e montagem de tela **não moram aqui** — moram em
`.claude/skills/ui-v2/` (famílias, paleta, telas canônicas), que é redigida a partir do código e
conferida por `check-ui-v2-refs.py`. Esta skill trata do **módulo**: contrato, dados, fluxo.

Do que você mais vai precisar: grade de 12 colunas (`FormRow` + `FormCol span={n}`), a listagem
server-side, o modal de aba filha e a regra do modal fora do `<Form>`. Tudo em `ui-v2`.

⚠️ **O v1 não é referência.** `UlFormCol*`, as alturas `y1`/`y2` do filtro animado, `CssBox`,
`CssDateField`, `CssTextareaAutosize` e `CssAppBar` não existem no v2 — a tabela de equivalências
está em `ui-v2/references/familias.md`.

## Decisões — o que o scaffold NÃO decide por você

| Situação | Decisão |
|---|---|
| **Payload de create/update** — FE-025 | Espelha o `[Segments.BODY]` da rota, **campo a campo**. Espelhar a tela de outro módulo não espelha o contrato: o Joi é que reprova |
| **Tipo da resposta** — AG-022 | A interface é uma **afirmação**, não uma verificação: o `tsc` não confere nada contra o backend. Ao mudar um DTO lá, abrir o tipo daqui na mesma passada; ao auditar remoção, comparar campo a campo |
| **Validação Yup** — FE-014 | Erra para o lado **permissivo**: campo vazio passa. Quem reprova de verdade é o backend; um espelho mais rígido bloqueia o que o backend aceitaria |
| **`helperText` com erro** — FE-015 | `touched.x && typeof errors.x === 'string' && errors.x` — `errors.x` pode ser `FormikErrors` aninhado e não compila |
| **Listagem** — FE-016 | Server-side de verdade: `paginationMode`, `rowCount` **e** o par `paginationModel`/`onPaginationModelChange`. Só `rowCount` desenha o rodapé certo e deixa a 2ª página inalcançável |
| **Select sobre endpoint paginado** — FE-018 | `rowsperpage` explícito: o padrão de 25 corta a lista sem avisar |
| **Botão cujo gatilho é uma condição terminal** — FE-017 | Some para sempre depois da primeira vez. O gatilho é o estado que **permite** a ação, não o que ela produz |
| **Componente novo** — FE-013 | Tem de ser **montado**: `grep -rn "<Nome>" src/ --include=*.tsx` acha a definição **e** um import. Componente órfão passa no ESLint e torna o critério `[humano]` inalcançável |
| **Campo `type="number"` + conversor** — FE-022 | O `handleChange` do Formik converte para número: um campo declarado `string` chega ao submit como número e `.trim()`/`.replace()` lançam `TypeError` dentro do `try` do salvamento — a tela grava metade |
| **Troca de aba / `display` / condicional** — FE-020 | Estado construído por interação morre na remontagem. A tabela de decisão está em `ui-v2` |
| **Migrando uma tela** — FE-026 | Remover os comentários **de verdade** e conferir que a tela chama o backend. Tela com o corpo comentado já aconteceu três vezes no mesmo módulo |

## Convenções (absorvidas do `FRONTEND-ARCHITECTURE.md` §19, removido na spec 086)

- **Ordem de imports**: React → libs → Context → Services → Constants → Types → Componentes
  internos → Styles. Os templates do scaffold já vêm nessa ordem.
- **`useCallback` em todo handler** passado como prop, dependência de `useEffect` ou de outro
  `useCallback`/`useMemo`.
- **`load<Algo>` declarada fora do `useEffect`**, com `useCallback`; o efeito só a chama. Recarga
  após operação chama a mesma função.
- **Confirmações**: delete sempre `window.confirm('Deseja realmente deletar este registro?')`;
  update conforme criticidade (`'Tem certeza que deseja atualizar o cadastro?'`).
- **Navegação pós-criação**: `history.push('/<modulo>/edit/${created.id}')`.
- **Sem `any`**, exceto `FormModel` do Formik, handlers do DataGrid e mocks.
- **Imports relativos**, sem alias. UI em pt-BR, código em inglês.

## Hooks (`src/hooks/` — plural)

| Hook | Para quê |
|---|---|
| `useAuth()` ⚠️ | Acesso ao `AuthContext` — exportado de `src/context/AuthContext.tsx`, **não** de `src/hooks/` |
| `useChainedSearch` | Busca encadeada com debounce em select de mais de 100 itens. Recebe `endpoint`, `responseKey`, `paramsBuilder`; expõe `id`, `name`, `items`, `loading`, `open`, `handleId`, `handleName`, `openBox` |
| `usePdfParser` | Extração de texto de PDF (pdfjs-dist) |
| `useExtensions` | Extensões do editor TipTap |

## Upload de arquivo — exceção v1 declarada

A aba de Arquivos/Anexos **permanece no v1** em qualquer módulo, por decisão do usuário: está
pronta, não migra e **não conta como dívida**. Padrão: `<input type="file" hidden />` + label
estilizado com `MdUpload`; state `{ file, name }`; `FormData` no submit; na **edição** não se troca
o arquivo (só metadados) — para trocar, apagar e recriar; na listagem, coluna com `renderCell`
devolvendo link para `file.file_url`.

## Avisos manuais ao final

1. Rotas em `src/routes/index.tsx`:
   `<Route path="/__modulos__" exact component={__Modulo__List} isPrivate />`
   `<Route path="/__modulo__/:register/:id?" component={__Modulo__Form} isPrivate />`
2. Menu em `src/components/Header/menuItens.tsx`
3. Provider em `src/App.tsx` (se gerou context modal)
4. `cd frontend/<ws> && yarn lint:fix`

## Verificação final obrigatória

1. `grep -rn "<modulo_de_referencia>" src/pages/__contexto__/ src/types/__modulos__.types.ts src/services/__modulos__.service.ts` retorna VAZIO (AG-002).
   ⚠️ Use os caminhos **planos** reais (§Ordem de geração). Um grep sobre `pages/<contexto>/<Modulo>/`
   — a forma aninhada antiga — roda sobre diretório inexistente, devolve vazio e aprova sempre
2. Checklist: types com auditoria; service completo; List com filtro server-side (FE-016); Form com TabPanel/a11yProps;
   RegisterData com `enableReinitialize`/`innerRef`/auditoria só em edit; filho fecha modal após sucesso
3. Gate: `bash .claude/scripts/verify.sh frontend --feature <feature>`
