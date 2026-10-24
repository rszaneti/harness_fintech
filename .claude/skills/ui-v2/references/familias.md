# Famílias do v2 — o catálogo

> Uma linha por export dos dois arquivos de estilo, com o papel e a armadilha que a doc do próprio
> export registra. **A doc no código é a fonte**: aqui há o resumo e o ponteiro (`arquivo:linha`).
> Quando divergirem, o código vence — e a divergência é defeito deste arquivo.
>
> `frontend/operador/src/styles/global_v2.tsx` — divs de layout, wrappers e textos (styled-components).
> `frontend/operador/src/styles/globalMaterialUi_v2.tsx` — tudo que embrulha um componente do MUI.
>
> O `globalMaterialUi_v2` **cresce sob demanda**: entra o componente que a próxima tela migrada
> precisar, não um catálogo escrito de antemão (`globalMaterialUi_v2.tsx:9-13`). O v1 tem 9 exports
> que nenhuma página usa e um que gera CSS inválido desde a migração do MUI v4 — é o que se evita.

---

## 1. TOKENS

Medidas e cores repetidas por mais de um componente. Valores e origem em
[`paleta.md`](./paleta.md). Um valor que aparece em dois lugares vira token **antes** de virar
divergência (`global_v2.tsx:42-46`).

## 2. RESET GLOBAL

`export default createGlobalStyle` (`global_v2.tsx:79`). Raiz de 10px (`62.5%`), `body`/`button` em
`1.6rem`, ícone nativo de calendário escondido (o date picker é o do MUI). Montado no `App.tsx`
junto com o do v1 enquanto a migração convive.

## 3. TIPOGRAFIA

| Export | Papel | Linha |
|---|---|---|
| `TitleH1` | **Título de página** — o mesmo em toda tela: listagem, formulário, workflow, relatório. **Não recebe props na prática** (o comentário do código diz 132 chamadas puras; medido em 11/09/2026: 126 de 127 — a única com props é o exemplo v1 dentro do próprio comentário), e é assim que deve continuar. Margem de 30px abaixo quando é filho direto do container; dentro de `ContentHeader` quem dá o espaço é o cabeçalho | `257` |
| `TitleH2` `TitleH3` `TitleH4` `TitleH5` `TitleH6` | Escala de seção. `TitleH3` é o título de bloco dentro de formulário e de modal — tira a cor do tema | `262` `290` `310` `321` `331` |

Props existem (`color`, `fontsize`, `margintop`…) mas são para fora da curva: **se você está prestes
a usar uma, provavelmente o default é que precisa mudar — para todo mundo** (`global_v2.tsx:200-210`).

⚠️ `fontsize` recebe **valor CSS completo** (`"3.5rem"`), não `"35"`. No v1 o número sem unidade
gerava declaração inválida que o browser descartava — 52 títulos renderizavam no padrão do agente
sem ninguém notar. `tracking` acompanha o tamanho: níveis grandes espaçam, pequenos ficam `normal`.

## 4. CONTAINERS DE PÁGINA

| Export | Papel | Linha |
|---|---|---|
| `ContainerList` | Raiz da tela de **listagem** | `372` |
| `ContainerForm` | Raiz da tela de **formulário** (largura útil `FORM_MAX_WIDTH`) | `400` |
| `ContainerSection` | Raiz do conteúdo de uma **aba filha** e do corpo de modal. Aceita `padding` | `430` |
| `ContentHeader` | Faixa "título à esquerda, ação à direita". Zera a margem do título — quem dá o respiro é a faixa. Props `flexwrap`, `gap`, `marginbottom` para o caso do workflow | `467` |

## 5. LISTAGEM

| Export | Papel | Linha |
|---|---|---|
| `StatGrid` `StatTile` `StatLabel` `StatValue` | Faixa de métricas acima do cartão. `StatGrid` aceita `columns` (default 4, o das 8 listagens; 3 no saldo do congelamento, para o quarto lugar não ficar vazio) e `StatValue` aceita `color`. **Específico de domínio** — o scaffold não gera | `535` `557` `573` `581` |
| `ListSurface` | **O cartão branco da listagem**: envolve filtro, grade e rodapé. `overflow: hidden` é o que faz a grade respeitar o raio nos cantos de baixo — a `CssDataGrid` não tem borda nem raio próprios justamente porque quem os dá é ele | `597` |
| `ListFilterBar` | Faixa de filtros, primeira seção dentro do `ListSurface`; a linha de baixo a separa da grade | `609` |
| `FilterGrid` | Grade dos campos de filtro. Colunas **fluidas** (mín. 210px). Difere do `FormGrid` de propósito: num formulário a ordem dos campos é significativa, no filtro o que importa é aproveitar a largura | `626` |
| `FilterActions` | Faixa dos botões do filtro ("Limpar filtros" + "Pesquisar") | `633` |
| `FilterSurface` | Variante do filtro fora do `ListSurface` (workflow) | `667` |
| `ListEmptyState` `ListEmptyTitle` `ListEmptyText` | Estado vazio. Entra como `slots.noRowsOverlay` da `CssDataGrid`, **que já o traz por padrão** — a listagem não monta nada | `684` `712` `719` |
| `Search` | Painel de busca do **workflow**. O painel fica sempre visível: filtrar é operação normal, não algo a se revelar (o v1 tinha altura calculada por nº de campos, e qualquer campo a mais cortava o painel sem avisar) | `753` |

⚠️ **As alturas `y1`/`y2` do filtro animado do v1 não existem no v2.** Se você está calculando
altura de filtro, está no arquivo errado.

## 6. FORMULÁRIO

| Export | Papel | Linha |
|---|---|---|
| `FormSurface` | **O cartão do formulário.** `overflow: hidden` para a barra de abas e o rodapé encostarem nas bordas arredondadas | `953` |
| `FormTabsBar` | Faixa das abas: abas à esquerda, nota contextual à direita ("Salve os dados para liberar as outras abas"). A nota fica aqui porque explica o estado **das abas** | `969` |
| `FormBody` | Corpo do formulário: **a pilha de linhas**. Não é grid — quem é grid é o `FormRow`, um por linha. A diferença não é cosmética: um `FormBody` de grid único com todos os campos como filhos diretos foi o que produziu o defeito de responsividade | `1009` |
| `FormRow` | Uma linha da grade de **12 colunas**. Prop `invisible` esconde a linha inteira (substitui o `display={cond ? 'none' : 'grid'}` do v1) | `1061` |
| `FormCol` | Uma célula: `span={n}` de 1 a 12. `alignself="end"` é o caso do botão ao lado de um campo ("Buscar pelo CEP") — sem ele o botão de 40px centraliza na altura do campo (rótulo + 44px) e desalinha da base | `1093` |
| `FormGrid` | **Caminho de migração do v1**: `UlFormCol1/2/3/4` → `<FormGrid cols={n}>`, filhos `<li>`; `template="6fr 3fr 3fr"` para larguras desiguais; `invisible` para bloco condicional. Colapsa para 1 coluna abaixo de 768px (a de 4 passa por 2 em 1024px). **Tela nova usa `FormRow`/`FormCol`** | `816` |
| `FormSectionHint` | Linha de contexto sob um título de seção. Sem props: o v1 oferecia sete de cor e margem, todas para reproduzir este mesmo desenho | `1126` |
| `FormRowSpacer` | Respiro entre blocos do formulário | `1143` |
| `FormFooter` | Faixa dos botões no rodapé do cartão. Substitui o `<ButtonsDiv align="center">` solto, em que os botões flutuavam sobre o fundo a uma distância que variava por tela. "Voltar" primeiro; ação principal com `sx={{ marginLeft: 'auto' }}` | `1162` |
| `FormCallout` | Aviso em caixa dentro do formulário. Passe margem explícita quando for filho direto de `ContainerForm` | `1205` |
| `FormIndicationCallout` | Aviso de **indicação clínica** de dois estados de igual peso: `indicated` verde (`success`), senão âmbar. Geometria do `FormCallout`; filhos: ícone + `<span>`. Abas Vitalidade e Leucócitos da coleta. Não use para alerta — para isso é o `FormCallout` | `1234` |
| `FormFooterAlert` | Mensagem de erro **no rodapé**, resposta ao clique em Salvar — o olho já está na faixa do botão. Cor de `palette.error.main` | `1268` |
| `ButtonsDiv` | Faixa de botões avulsa (topo de aba filha, por exemplo). ⚠️ Props com **unidade**: v1 `margintop="20"` → v2 `margintop="20px"` | `884` |
| `DetailSurface` | Camada interna do cartão para uma sub-tabela (`CssDataGrid density="compact" hideFooter`) | `918` |

## 7. MODAL

Anatomia (`global_v2.tsx:1276-1287`): `CssModalForm` › `Fade` › `ModalSurface` › `ModalHeader` +
`FormBody` + `FormFooter` — **o corpo e o rodapé são os mesmos do formulário de página**.

| Export | Papel | Linha |
|---|---|---|
| `ModalSurface` | O cartão flutuante. O corpo rola e as faixas de dentro dele **não encolhem** (`> * { flex-shrink: 0 }`): sem isso, um filho com `overflow` não visível — o `ListSurface` de uma grade — tem mínimo automático zero e absorve todo o déficit de altura, achatando a tabela em vez de rolar | `1327` |
| `ModalHeader` | Faixa de título com o ✕ à direita. Zera a margem do título | `1402` |
| `ModalCloseButton` | O ✕. Repete os números do botão-ícone da grade (30px, raio 7px, borda cinza, cor da marca só no hover) em vez de inventar desenho próprio | `1432` |

## 8. WORKFLOW

| Export | Papel | Linha |
|---|---|---|
| `ContainerWorkflow` | Tela de fundo do kanban. **Não colapsa** com o `ContentWorkflow`: este carrega fundo e `min-height`, aquele carrega `margin-block`; fundidos, a margem deixaria os 30px do topo sem fundo | `1499` |
| `ContentWorkflow` | Área útil, largura toda; empilha cabeçalho, busca, board e timeline com `gap` | `1514` |
| `BoardSurface` | Superfície branca que envolve o board. **Só a superfície** — board, coluna e cartão vivem em `components/KanbanBoard/styles.ts` (v1) e continuam lá | `1537` |
| `TimelineItem` `TimelineIcon` `TimelineContent` | Entrada do histórico de etapas no modal de timeline. `TimelineIcon` recebe `color` (de `WORKFLOW_STAGE_COLORS[stage]`), com fallback `#757575` | `1561` `1577` `1587` |

> ⚠️ Aba filha de workflow (`TentantFormWorkflow`) **não** usa `ContainerWorkflow` — usa
> `ContainerSection`, como qualquer aba.

## 9. CARD DO BOARD KANBAN

Casca do cartão; quem monta é `components/KanbanBoard/KanbanCard.tsx`. Anatomia em
`global_v2.tsx:1600-1621`: `Card` › `CardAccent` + `CardBody` › (`CardHeader` › `CardIdentity`
[`CardTitle` `CardSubtitle`] + `CardTimestamp` [`CardTimestampDate` `CardTimestampTime`]) +
`CardChip` [`CardChipDot`] + `CardDivider` + `CardActions` [`CardActionButton`].

| Export | Linha | | Export | Linha |
|---|---|---|---|---|
| `Card` | `1693` | | `CardChip` | `1809` |
| `CardAccent` | `1726` | | `CardChipDot` | `1824` |
| `CardBody` | `1733` | | `CardEyebrow` | `1836` |
| `CardHeader` | `1743` | | `CardBadges` | `1848` |
| `CardIdentity` | `1751` | | `CardBadge` | `1862` |
| `CardTitle` | `1759` | | `CardMeta` | `1886` |
| `CardSubtitle` | `1777` | | `CardDivider` | `1900` |
| `CardTimestamp` | `1785` | | `CardActions` | `1909` |
| `CardTimestampDate` `CardTimestampTime` | `1794` `1802` | | `CardActionButton` | `1916` |

`CardActionButton` aceita `tone="danger"` (hover vermelho para ação destrutiva) e `hovercolor`
quando a ação tem significado próprio — o caso do board de doadores, em que cada ação já tem cor
semântica. `hovercolor` vence o `tone`.

---

## 10. Componentes MUI — `globalMaterialUi_v2.tsx`

| Export | Papel e armadilha | Linha |
|---|---|---|
| `CssTextField` | **Campo de texto do app** — formulário e filtro. A API do `TextField` fica inteira (`select`, `multiline`, `helperText`). O embrulho fixa `shrink: true`: o rótulo é estático, mas o MUI usa esse estado para decidir se mostra o `placeholder` — sem ele, todo placeholder do app só apareceria com o campo preenchido. Mescla `InputLabelProps` (trocar a chave quebraria o `id`/`htmlFor` que o `renderInput` do `Autocomplete` entrega). Rótulo diz o **nome**; placeholder diz o que acontece se ficar vazio ("Todas as cidades") ou o formato. `required` gera o asterisco vermelho. `masked` para campo com máscara. `multiline` não herda a altura fixa | `262` |
| `ISelectOption` | O par `{ value, label }` que as listas de opção usam — as constantes de `src/constants/` já vêm nesse formato | `296` |
| `CssAutocomplete` | **Seleção**, estática ou dinâmica. `renderInput={(params) => <CssTextField {...params} … />}`; `value` é o objeto (`OPTIONS.find(o => o.value === v) ?? null`), `onChange` devolve a opção. ⚠️ Memoize `options` quando derivar de constante: o componente compara por referência ao decidir se reabre a lista, e recriar o array a cada render fecha o popup enquanto se digita | `345` |
| `TActionTone` `actionTone` `ACTION_TONES` | Tons de ação (`edit`, `delete`…). Só `edit` sai do tema (`palette.info`); os outros são derivados por `polished`. `alpha 0.12` nos ícones: medido para 3.94:1 e 4.39:1, acima do mínimo WCAG de 3:1 para elemento gráfico | `437` `497` `509` |
| `CssButton` | Botão da tela. `variant="contained"` = ação principal, `variant="outlined"` = secundária, `tone="edit"` = **consulta dentro do formulário** ("Buscar pelo CEP/CNPJ"), que pertence ao campo ao lado. 40px de altura (4px a menos que o campo). Não redefine cor de texto — `primary.contrastText` já é branco | `548` |
| `CssCheckBox` `CssRadio` `CssRadioGroup` `CssFormControlLabel` `CssFormControl` `CssFormLabel` | Seleção booleana e grupos. `CssFormControlLabel` zera o `marginLeft: -11px` do MUI, que desalinharia o rótulo da coluna do grid. `CssFormLabel` repete a tipografia do rótulo de campo (1.3rem/600) — é o mesmo papel | `671` `676` `689` `703` `718` `730` |
| `CssTabs` `CssTab` | Abas do formulário. Vão **dentro** do `FormSurface`, sobre a linha do cabeçalho (`marginBottom: -1px` faz o indicador cobrir a linha). **Não usa `AppBar`** (o v1 usava, e ele só acrescentava uma segunda superfície com sombra). Aba bloqueada: `disabled` + ícone de cadeado, `iconPosition="start"` | `759` `779` |
| `CssModalForm` | `styled(Modal)` do modal de aba filha. ⚠️ **Nunca passar `slots={{ backdrop: Backdrop }}`** (FE-024): o `Backdrop` cru perde o `z-index: -1` do slot padrão e o escurecimento pinta **na frente** do cartão. `slotProps={{ backdrop: { timeout: 500 } }}` funciona sozinho | `853` |
| `CssStatusChip` | Etiqueta de status. `statuscolor` é a cor sólida; fundo, borda e texto são derivados por `polished` | `877` |
| `GridEmptyStateNoRecords` | Estado vazio **sem filtro** (aba filha): o default fala em "remova os filtros aplicados", que aponta para algo que não existe ali. Entra como `slots={{ noRowsOverlay: GridEmptyStateNoRecords }}` | `951` |
| `CssDataGrid` | A grade. Sem borda nem raio próprios (quem os dá é o `ListSurface`). **Não define comportamento**: `paginationMode`, `rowCount`, `sortingMode`, `paginationModel` e os handlers continuam por página — são contrato com o backend, não aparência. Ícone de ação pela classe `action-edit`/`action-delete`, **sem cor no ícone** | `1162` |

## 11. O que **não** existe no v2

`CssBox`, `CssBoxTable`, `CssBoxModalForm`, `CssAppBar`, `CssIconButtonTableHeader`,
`CssDatePicker`, `CssTextareaAutosize`, `CssDateField`, `UlFormCol1`…`UlFormCol4`, `Buttons`,
`Paragraph`. Equivalências:

| v1 | v2 |
|---|---|
| `CssBox` / `CssBoxTable` | `ListSurface` + `CssDataGrid` |
| `CssBoxModalForm` | `ModalSurface` |
| `CssAppBar` | `FormTabsBar` + `CssTabs` |
| `CssIconButtonTableHeader` | `GridActionsCellItem className="action-edit\|action-delete"` |
| `UlFormCol*` | `FormRow`/`FormCol span` (tela nova) ou `FormGrid cols/template` (migração) |
| `Buttons` | `ButtonsDiv` (props com unidade) ou `FormFooter` |
| `Paragraph` | `FormSectionHint` |
| `CssDateField` / `CssDatePicker` | `CssTextField type="date"` / `type="datetime-local"` |
| `CssTextareaAutosize` | `CssTextField multiline minRows={n}` |
