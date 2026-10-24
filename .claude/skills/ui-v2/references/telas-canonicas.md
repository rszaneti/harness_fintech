# Telas canônicas do v2

> Telas **reais** do repositório que demonstram o padrão. Ler a tela é mais barato que ler a regra;
> por isso cada seção diz **o que ela demonstra** e, principalmente, **o que não copiar** — o que é
> domínio dela e não padrão.
>
> Módulo de referência: **Clínicas** (specs 073–077), feito inteiro no v2 com o harness atual.
> ⚠️ Copiar tela para gerar módulo novo é AG-002/FE-001..007 — vazamento de imports e campos.
> Módulo novo nasce do `scaffold.py`, cujos templates saíram destas telas. Aqui se **consulta**.

---

## Listagem — `frontend/operador/src/pages/clinics/ClinicsList/index.tsx` (517 linhas)

**Demonstra**: `ContainerList` › `ContentHeader` (título + "Cadastrar") › `StatGrid` › `ListSurface`
(`ListFilterBar` com Formik + `FilterGrid` + `FilterActions`, depois `CssDataGrid`).
Paginação e ordenação **server-side** (`paginationMode`, `sortingMode`, `paginationModel`,
`onPaginationModelChange`, `sortModel`, `onSortModelChange`, `rowCount`); `page` do grid é 0-based e
o backend é 1-based — a conversão fica no `load` (FE-016). "Limpar filtros" chama `resetForm()` **e**
recarrega: o `type="reset"` do v1 só limpava o DOM e a lista continuava filtrada. Filtrar volta à
primeira página. Edição inline de `status` por `processRowUpdate` + `onProcessRowUpdateError`.
Ações da linha com `GridActionsCellItem` **sem cor no ícone** — quem pinta é a classe
`action-edit`/`action-delete`.

**Não copiar**: as métricas de alvará (`getClinicLicenseStatus`, as constantes de alvará,
`fetchClinicsForMetrics`) — são domínio, e a chamada de métricas carrega a tabela até um teto
(`CLINIC_METRICS_LIMIT = 2000`) porque o backend não expõe agregados; é **dívida consciente**
registrada no próprio service, não padrão a espalhar.

## Formulário com abas — `pages/clinics/ClinicForm/index.tsx` (189 linhas)

**Demonstra**: `ContainerForm` › `ContentHeader` (título + "Voltar") › `FormSurface` ›
`FormTabsBar` (`CssTabs`/`CssTab`) › `TabPanel` por aba. Abas filhas com `disabled={!isEdit}` — o
registro precisa existir. `TabPanel` **sem caixa nem padding**: o respiro é do conteúdo de cada aba
(a versão anterior embrulhava tudo num box com padding e somava dois respiros). O provider do
contexto de modal envolve a página inteira.

⚠️ O `Link` **envolve** o `CssButton` em vez de `component={Link}`: `styled()` apaga a tipagem
polimórfica do `Button` e a prop `component` deixa de existir para o TypeScript.

## Aba Dados — `pages/clinics/ClinicFormRegisterData/index.tsx` (1.659 linhas)

**Demonstra**: `Formik` com `innerRef` e `enableReinitialize={register === 'edit'}`; `FormBody` ›
`FormRow` › `FormCol span={n}` (grade de 12); auditoria (`user_created`, `created_at`…) só em
edição, campos `disabled`; `FormFooter` com o botão principal em `sx={{ marginLeft: 'auto' }}`;
`helperText={touched.x && typeof errors.x === 'string' && errors.x}` (FE-015); Yup **permissivo** —
campo vazio passa, quem reprova é o backend (FE-014); máscaras limpas com `replaceSpecialChars`
antes de enviar; `CssButton tone="edit"` para "Buscar pelo CEP/CNPJ", com `FormCol alignself="end"`.

⚠️ **O fragmento que tira o modal de dentro do `<Form>`** (comentário em `857-873`, montagem fora
do `</Form>` em `1644-1651`) é o caso mais importante
desta tela: o modal de e-mail de amostras tem `<Form onSubmit>` próprio, e dentro da subárvore
deste `<Form>` o evento subiria até aqui e salvaria a clínica inteira a cada e-mail cadastrado.
`CssModalForm` é `styled(Modal)` sem `disablePortal` — no DOM o modal sai para o `body`, **mas
eventos atravessam portal pela árvore do React**. A grade fica dentro do `<Form>`; o modal, fora; o
`id` da linha em edição liga os dois pelo contexto.

**Não copiar**: BrasilAPI/CNPJ, QSA do sócio, os 40 campos do FR30, o bloco `partner_*`. É domínio.

## Aba filha — `pages/clinics/ClinicFormContact/` (lista 231 + register 416 linhas)

**Demonstra**: `ContainerSection` › `FormBody` › `ButtonsDiv margintop="0px"` + `ListSurface` ›
`CssDataGrid` com `slots={{ noRowsOverlay: GridEmptyStateNoRecords }}` (a aba não tem filtro: o
estado vazio default mandaria "remova os filtros aplicados", que aponta para algo inexistente).
A lista recarrega ouvindo `openContactModal` no `useEffect` — fechar o modal após salvar é o
gatilho. O `id` do registro em edição fica num `useState` **local** (aqui há um pai por onde
descer). O `ClinicFormContactRegister` é o **conteúdo** do modal (`ModalHeader` + `FormBody` + `FormFooter`); a
superfície (`ModalSurface`) é do pai, e o rodapé fica dentro do `<Formik>` para submeter sem
levantar estado.

⚠️ **Sem `slots={{ backdrop: Backdrop }}`** (FE-024): as chamadas do v1 passam esse slot (o comentário do código diz 62; medido em 11/09/2026: 42 em código), e o
`Backdrop` cru perde o `z-index: -1` do slot padrão — o escurecimento pinta na frente do cartão.

## Modal irmão da grade — `pages/clinics/ClinicFormSampleEmail/ClinicFormSampleEmailModal/index.tsx` (61 linhas)

**Demonstra**: o modal **sozinho** num componente, montado fora do `</Form>` da aba Dados, com o
`id` trafegando pelo `ClinicModalContext` (`sampleEmailId`). É a saída para o caso acima: grade e
modal como **irmãos**, não pai e filho. `ClinicModalContext` documenta por que só este dos três
guarda o id no contexto — os outros têm pai por onde descer.

## Workflow / kanban — `pages/patients/PatientsWorkflow/index.tsx` (762 linhas)

**Demonstra**: `ContainerWorkflow` › `ContentWorkflow` › `ContentHeader flexwrap gap` › `Search` ›
`BoardSurface`; `TimelineItem`/`TimelineIcon`/`TimelineContent` no modal de histórico; cor de etapa
vinda de `WORKFLOW_STAGE_COLORS[stage]`.

⚠️ **Ressalva — é a canônica possível, não uma tela 100% v2.** Nenhuma das quatro páginas de
workflow migrou por completo (conferido em 11/09/2026): esta importa **também**
`components/KanbanBoard/styles` (v1) e `KanbanCard`. **O que é v1 nela não é padrão**: board,
coluna e cartão ainda moram no v1 por decisão do `BoardSurface` ("aqui é só a superfície"), e a
família `Card*` do `global_v2` existe como casca v2 do cartão. Para tela de workflow nova: usar a
estrutura acima do `global_v2` e a família `Card*`; consultar esta tela para o **fluxo** (drag,
etapas, timeline), não para o estilo.

---

## Onde o v1 ainda manda — e por quê

- **152 páginas** importam só v1 (`styles/global`, `styles/globalMaterialUi`). São legado: nunca
  servem de modelo, e o `App.tsx` monta os dois estilos globais de propósito para a migração conviver.
- **Migração parcial existe e não é o alvo**: 351 arquivos importam algo do `global_v2`, mas só
  **202 pastas de página** usam os componentes do `globalMaterialUi_v2` — e são essas as migradas de
  fato. As outras pegaram um container ou um título e seguem com estilo próprio. Ao tocar uma
  dessas, migrar por inteiro é o caminho; deixar meio a meio é o que produziu os `styles.ts`
  remanescentes em pasta que já importa v2 — hoje **11**, contra os 92 de 11/09/2026.

> ⚠️ **Os números de 11/09/2026 que estavam aqui ("42 páginas v1 puras", "330 pastas", "149
> migradas", "92 `styles.ts`") não se reproduzem** com nenhuma medição de 21/09/2026, e o método
> daquela contagem não ficou registrado — o de v1 puras em particular estava uma ordem de grandeza
> abaixo. Os acima vêm de `grep -rl … src --include=*.tsx` (por arquivo) e do mesmo grep restrito a
> `src/pages/**/index.tsx` reduzido por `dirname` (por pasta). Ao atualizar, repita um dos dois e
> diga qual.
- **Aba de Arquivos/Anexos**: permanece v1 em qualquer módulo por **decisão do usuário** — está
  pronta, não migra e **não conta como dívida**. Não abrir achado de auditoria sobre ela.
- **Board kanban** (`components/KanbanBoard/`): v1 por ora, como acima.
