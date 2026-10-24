---
name: ui-v2
description: Padrão visual v2 (herdado do ERP de origem; revisão nas specs 010/011) — o que usar, quando e com qual token. Consultar antes de escrever ou revisar qualquer tela dos frontends (listagem, formulário, aba filha, modal, workflow).
---

# Skill: ui-v2 — o padrão visual do `frontend/operador`

> ⚠️ **Padrão herdado do ERP Vida Fértil** (spec 001). As telas canônicas e os arquivos de estilo
> citados aqui são do ERP de origem e ainda não existem em `frontend/operador`; o padrão é revisto
> nas specs 010/011. Até lá, o `check-ui-v2-refs.py` sai 65 (não rodou), não 0.

**Toda tela nova é v2.** O v1 (`styles/global`, `styles/globalMaterialUi`) é legado: 152 páginas
ainda o usam, nenhuma serve de modelo. O `App.tsx` monta os dois estilos globais de propósito, para
a migração conviver.

## Precedência

```
código (*_v2 + theme.ts) > skill ui-v2 > frontend/operador/CLAUDE.md
```

O que compila é o que vale. Esta skill traz o **acionável** e cita `arquivo:linha`; o `CLAUDE.md` do
workspace traz o estado da migração e o que está fora do padrão. Divergência entre eles é defeito
da fonte de menor precedência — reportar, não contornar. `check-ui-v2-refs.py` reprova componente
ou cor citados aqui que não existam no código.

| Onde | O quê |
|---|---|
| [`references/familias.md`](./references/familias.md) | Catálogo: uma linha por export dos dois arquivos de estilo, com a armadilha de cada um |
| [`references/paleta.md`](./references/paleta.md) | Cores do `theme.ts`, tokens, escala de fonte, regra de derivar status |
| [`references/telas-canonicas.md`](./references/telas-canonicas.md) | As 6 telas reais que demonstram o padrão — e o que **não** copiar delas |

Os dois arquivos de estilo: `frontend/operador/src/styles/global_v2.tsx` (divs de layout, wrappers,
textos — 72 exports em 9 famílias) e `globalMaterialUi_v2.tsx` (o que embrulha componente do MUI —
19 exports). Tema: `src/theme.ts` (não existe `theme_v2`).

## As 9 famílias

| Família | Para quê | Canônica |
|---|---|---|
| **Tokens** | Medidas e cores repetidas. Valor em dois lugares vira token antes de virar divergência | — |
| **Reset** | Raiz de 10px (`62.5%`), corpo em `1.6rem` | — |
| **Tipografia** | `TitleH1`…`TitleH6`. `TitleH1` é o título de página, **sem props** | todas |
| **Containers de página** | `ContainerList` · `ContainerForm` · `ContainerSection` (aba/modal) · `ContentHeader` | todas |
| **Listagem** | `ListSurface` › `ListFilterBar`+`FilterGrid`+`FilterActions` › `CssDataGrid`; `StatGrid` (domínio) | `ClinicsList` |
| **Formulário** | `FormSurface` › `FormTabsBar` › `FormBody` › `FormRow`/`FormCol span` › `FormFooter` | `ClinicForm` + `ClinicFormRegisterData` |
| **Modal** | `CssModalForm` › `Fade` › `ModalSurface` › `ModalHeader`+`FormBody`+`FormFooter` | `ClinicFormContactsList` |
| **Workflow** | `ContainerWorkflow` › `ContentWorkflow` › `ContentHeader`+`Search`+`BoardSurface`; `TimelineItem` | `PatientsWorkflow` ⚠️ |
| **Card do board** | `Card` › `CardAccent`+`CardBody` (header, chip, divider, actions) | `KanbanCard` (v1) ⚠️ |

## Montagem — as quatro telas

**Listagem**: `ContainerList` › `ContentHeader` (título + ação principal) › [`StatGrid`] ›
`ListSurface` (filtro Formik + `CssDataGrid`). Paginação e ordenação **no servidor** (FE-016):
`paginationMode="server"`, `sortingMode="server"`, `rowCount`, `paginationModel` +
`onPaginationModelChange`, `sortModel` + `onSortModelChange`. `page` do grid é 0-based, o backend é
1-based. "Limpar filtros" faz `resetForm()` **e** recarrega. Filtrar volta à página 1.

**Formulário**: `ContainerForm` › `ContentHeader` (título + "Voltar") › `FormSurface` ›
`FormTabsBar` › `TabPanel`. Aba filha só habilita em edição (`disabled={!isEdit}`). O corpo de cada
aba dá o próprio respiro — `TabPanel` não tem padding. `enableReinitialize` **só** em edição;
`innerRef` quando algo preenche campos de fora (busca de CEP/CNPJ). Auditoria só em edição.

**Aba filha**: `ContainerSection` › `FormBody` › `ButtonsDiv` + `ListSurface` › `CssDataGrid` com
`slots={{ noRowsOverlay: GridEmptyStateNoRecords }}`. O modal tem o componente de cadastro (`<Modulo>Form<Filho>Register`) como conteúdo; a
superfície é do pai. A lista recarrega ouvindo o estado de abertura do modal.

**Workflow**: `ContainerWorkflow` › `ContentWorkflow` › `ContentHeader` + `Search` + `BoardSurface`.
Board, coluna e cartão ainda vêm de `components/KanbanBoard/` (v1) — ver a ressalva nas canônicas.

### Modal dentro de formulário — a armadilha que custa caro

Quando a grade fica **dentro do `<Form>`** da aba Dados, o modal tem de ficar **fora** dele, como
irmão, com o `id` trafegando pelo contexto. `CssModalForm` é `styled(Modal)` sem `disablePortal`:
no DOM o modal sai para o `body`, **mas eventos atravessam portal pela árvore do React** — o submit
do modal subiria e salvaria o registro pai inteiro. Referência: `ClinicFormSampleEmailModal` e o
comentário do fragmento em `ClinicFormRegisterData`.

### Estado que sobrevive à troca de aba (FE-020) — decidir ANTES de montar

Trocar **renderização condicional ⇄ `display` ⇄ aba de `TabPanel`** destrói ou congela estado. Ao
desenhar a tela, listar cada `useState`/`useRef` e classificar:

| Origem do estado | Ao remontar |
|---|---|
| vem do servidor | recarrega sozinho — ok |
| derivado de props | recalcula — ok |
| **construído por interação** | **morre, e ninguém o traz de volta** |

O terceiro grupo precisa de decisão explícita: subir para um componente que sobrevive, reconstruir
num efeito de montagem, ou ter o requisito revogado **por escrito**. E o inverso: um `useEffect` que
lê dado escrito em outra aba não pode dividir efeito com os que leem dado estático — passa a rodar
no mount do pai, antes de o dado existir. ⚠️ `<select>` nativo com `value` sem `<option>`
correspondente **renderiza vazio**: tela em branco com o payload certo é pior que erro.

Esta checagem é **de projeto**, não de auditoria: no `plan.md` da feature ela é a tabela "onde vive
o estado" do § Telas.

## Componentes por tipo de campo

| Campo | Componente |
|---|---|
| Texto, número, data, datetime | `CssTextField` com `type=` adequado |
| Texto longo | `CssTextField multiline minRows={n}` |
| Seleção (estática ou dinâmica < 100) | `CssAutocomplete` + `ISelectOption`, com `renderInput` devolvendo `CssTextField` |
| Seleção dinâmica > 100 | `useChainedSearch` (`src/hooks/`) |
| Moeda | `CurrencyInput` (`src/components/inputs/`) |
| Booleano | `CssCheckBox` + `CssFormControlLabel` |
| Grupo de opções | `CssFormControl` + `CssFormLabel` + `CssRadioGroup` + `CssRadio` |
| Status em célula/campo | `CssStatusChip` |
| Ação | `CssButton` — `contained` principal, `outlined` secundária, `tone="edit"` consulta no formulário |

⚠️ Não existem no v2: `CssDateField`, `CssDatePicker`, `CssTextareaAutosize`, `CssBox`,
`CssBoxTable`, `CssAppBar`, `CssBoxModalForm`, `CssIconButtonTableHeader`, `UlFormCol*`. A tabela de
equivalências está no fim de [`familias.md`](./references/familias.md).

## Proibições que o hook já reprova

| Código | Regra |
|---|---|
| FE-009 | `inputProps={...}` (deprecated no MUI v7) → `slotProps={{ htmlInput: {…} }}` |
| FE-019 | Nada abaixo de `1.2rem` — em `sx`, `style`, styled, `rem` ou `px` |
| FE-023 | Crase dentro de comentário CSS de `styled` fecha o template ali |
| FE-024 | `slots={{ backdrop: Backdrop }}` no `Modal` — o escurecimento pinta na frente do cartão |

Não repetir a regra ao lado do código: o hook devolve a mensagem com o motivo.

## Exceções declaradas — não são dívida

- **Aba de Arquivos/Anexos**: permanece v1 em qualquer módulo, por decisão do usuário. Está pronta,
  não migra, **não abrir achado**.
- **Board kanban** (`components/KanbanBoard/`): v1 enquanto a família `Card*` do v2 não for adotada.
- **152 páginas v1**: legado. Migram quando a feature as tocar — nunca "de passagem", e nunca servem
  de modelo.
- **`typography.htmlFontSize` ausente no `theme.ts`** (FE-019): `variant="caption"`/`"body2"` rendem
  ~7,5px e ~8,75px. Texto pequeno com `fontSize` explícito ≥ `1.2rem`, nunca com o variant cru.
  Registrado como dívida em `frontend/operador/CLAUDE.md`.

## Antes de fechar uma tela

1. Nenhum import de `styles/global` ou `styles/globalMaterialUi` sem `_v2`.
2. Todo `Css*`/componente importado existe — `python3 .claude/scripts/check-ui-v2-refs.py` cobre a
   documentação; no código, quem cobre é o `tsc`.
3. Componente novo está **montado** em algum lugar (FE-013): `grep -rn "<Nome>" src/ --include=*.tsx`
   tem de achar a definição **e** pelo menos um import.
4. Estado que sobrevive à troca de aba: a tabela acima foi preenchida.
5. Nada abaixo de `1.2rem`; sem `!important`.
