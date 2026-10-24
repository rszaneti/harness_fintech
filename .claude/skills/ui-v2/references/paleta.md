# Paleta e tokens do v2

> **Extraído do código, não de documento.** Cada linha traz a origem; `check-ui-v2-refs.py` reprova
> cor que não exista em `frontend/operador/src/theme.ts` nem nos tokens dos dois arquivos de estilo.
> Mudar um valor aqui sem mudar no código é criar a divergência que esta tabela existe para impedir.

## Paleta do tema — `src/theme.ts`

O tema é o do v2 (não existe `theme_v2.ts`). O que está nele vale para todo componente MUI; o que
é papel do tema **não se repete** nos styled — lê-se do `theme.palette`.

| Papel | `main` | `light` | `dark` | `contrastText` | Origem / porquê |
|---|---|---|---|---|---|
| `primary` | `#1a7f76` | `#4aa79d` | `#10635c` | `#ffffff` | `theme.ts:20-25`. Teal do modelo v2. Substituiu `#5ec4b6`, que dava 2.09:1 com branco — abaixo do mínimo AA de 4.5:1 e reprovava todo botão `contained`. Sobre `#1a7f76` dá ~4.9:1, e por isso o `contrastText` pôde virar branco |
| `secondary` | `#0D0D0D` | — | — | `#3d3d3d` | `theme.ts:26-29` |
| `info` | `#1976d2` | `#4791db` | `#115293` | `#ffffff` | `theme.ts:57-62`. **O azul de CONSULTA**: é o papel que `actionTone(theme, 'edit')` lê (`globalMaterialUi_v2.tsx:497`) — de onde saem o ícone de editar na grade **e** o fundo do `CssButton tone="edit"` ("Buscar pelo CEP/CNPJ"). Mexer aqui muda os dois |
| `success` | `#2CAA09` | `#56bb3a` | `#1e7606` | `#ffffff` | `theme.ts:63-68` |
| `warning` | `#d50000` | `#dd3333` | `#950000` | `#ffffff` | `theme.ts:69-74` |
| `error` | `#b3261e` | `#fbeceb` | `#8c1c16` | `#ffffff` | `theme.ts:80-85`. Antes desta linha o app caía no `#d32f2f` padrão do MUI, que não é cor de modelo nenhum. É o mesmo tom do asterisco de campo obrigatório |

| Token | Valor | Origem |
|---|---|---|
| `text.primary` / `secondary` / `disabled` | `#1c2321` / `#6b7573` / `#a7b0ad` | `theme.ts:86-90` |
| `divider` | `#e3e8e6` | `theme.ts:91` |
| `background.default` / `paper` | `#f5f5f5` / `#eeeeee` | `theme.ts:34-37` |
| `grey.50`…`grey.900` | escala padrão MUI | `theme.ts:38-49` |

**`components.MuiDataGrid`** (`theme.ts:93-110`): `fontSize: 1.4rem`; célula booleana `2rem`, verde
`#2CAA09` quando `true` e vermelho `#ff0000` quando `false`. Vale para `DataGrid`, `DataGridPro` e
`DataGridPremium`.

**Locale**: `ptBR` do core, do data-grid e dos pickers, aplicados na criação do tema (`theme.ts:112-114`).

## Tokens de layout — `styles/global_v2.tsx`

| Token | Valor | Papel | Origem |
|---|---|---|---|
| `FORM_MAX_WIDTH` | `1306px` | Largura útil padrão de um formulário (v1: repetido em 52 arquivos) | `global_v2.tsx:49` |
| `PAGE_INLINE_PADDING` | `15px` | Respiro lateral da área de conteúdo | `global_v2.tsx:52` |
| `PAGE_BLOCK_MARGIN` | `30px` | Respiro vertical da área de conteúdo | `global_v2.tsx:55` |
| `WORKFLOW_SECTION_GAP` | `16px` | Espaço entre as seções empilhadas de uma página de workflow | `global_v2.tsx:58` |
| `TITLE_COLOR` | `#3d3d3d` | Cor dos títulos. Literal porque não é papel nenhum do tema | `global_v2.tsx:61` |
| `CARD_BORDER` | `#d7dedb` | Borda de uma superfície (cartão da listagem, do formulário) | `global_v2.tsx:64` |
| `SURFACE_DIVIDER` | `#e3e8e6` | Linha que separa faixas **dentro** de uma superfície (barra de abas, rodapé). Mais clara que a `CARD_BORDER` de propósito: a externa fecha o cartão contra o fundo, a interna só organiza o que já está dentro | `global_v2.tsx:72` |

## Tokens de controle — `styles/globalMaterialUi_v2.tsx`

Não exportados: são internos do arquivo. Vêm do modelo `documentacao/Exemplos Frontend/Card/`.

| Token | Valor | Papel | Origem |
|---|---|---|---|
| `FIELD_BORDER` | `#cfd6d4` | Borda neutra de campo, botão secundário e toggle | `globalMaterialUi_v2.tsx:60` |
| `FIELD_HEIGHT` | `44px` | Altura de **todo** controle de entrada: campo, combo, aba. O botão é 4px mais baixo (40px), como o modelo desenha | `globalMaterialUi_v2.tsx:63` |
| `CONTROL_RADIUS` | `6px` | Raio de todo controle. O cartão que os contém usa `10px` | `globalMaterialUi_v2.tsx:66` |
| `LABEL_COLOR` | `#45504d` | Cor do rótulo de campo e de grupo | `globalMaterialUi_v2.tsx:69` |

## Escala de fonte

`:root { font-size: 62.5% }` no reset do `global_v2` → **1rem = 10px** (`global_v2.tsx:79-93`).
O v1 usava 60% abaixo de 768px e 62.5% acima, o que fazia `1.2rem` valer menos que o piso no mobile;
o v2 unifica em 62.5% nos dois casos.

| Uso | Tamanho |
|---|---|
| Corpo de texto, `body`, `button`, input | `1.6rem` |
| Grade / `DataGridPro` | `1.4rem` (vem do tema) |
| Rótulo de campo e de grupo (`CssTextField`, `CssFormLabel`) | `1.3rem`, peso 600, `letter-spacing .01em` |
| **Menor texto legível** (helper, legenda, chip, hora no cartão do board) | **`1.2rem`** |
| Abaixo disso | não existe — `.claude/hooks/font-size-floor.py` reprova |

Sempre em `rem`: `px` não acompanha a raiz e congela o tamanho no mobile.

⚠️ **Dívida conhecida (FE-019).** O comentário do reset diz que o `62.5%` é "par com
`typography.htmlFontSize` do `theme.ts`" — mas o `theme.ts` **não declara `typography`**
(conferido em 11/09/2026). Consequência: o MUI calcula `variant="caption"` e `variant="body2"`
supondo raiz de 16px enquanto a real é 10px, e eles rendem ~7,5px e ~8,75px. O hook não pega (não
há valor literal para ler). **No admin, texto pequeno se resolve com `fontSize` explícito ≥ 1.2rem
ou com os componentes do v2 — nunca com o `variant` cru.** Registrado como dívida em
`frontend/operador/CLAUDE.md`.

## Cor de status: derivar, nunca tabelar

`CssStatusChip` (`globalMaterialUi_v2.tsx:877`) e `CardChip` (`global_v2.tsx:1809`) **derivam**
fundo, borda e texto da cor sólida da etapa com `polished` (`darken`, `shade`, `tint`), com os
mesmos pesos. Os pesos foram escolhidos medindo contraste WCAG sobre as 17 cores de etapa reais dos
quatro boards — pior caso `#facc15` (amarelo) a 4.58:1, acima do mínimo AA de 4.5:1.

Derivar, em vez de manter uma segunda tabela de tons, é o que impede as duas paletas de status do
app de divergirem. O mesmo vale para `actionTone` (`globalMaterialUi_v2.tsx:497`): só `edit` sai do
tema (`palette.info`); as outras são derivadas. O `alpha 0.12` dos ícones de ação foi medido: a
0.08 o ícone ficava em 1.94:1 (editar) e 1.69:1 (excluir); a 0.12 sobe para 3.94:1 e 4.39:1, acima
do mínimo de 3:1 que a WCAG pede para elemento gráfico.

⚠️ **Sem `!important` em componente.** Medido em **código**, sem comentários (AG-013), em 11/09/2026:
o v1 tem **18** (11 no `globalMaterialUi.tsx`, 7 no `global.tsx`), e existem porque a especificidade
foi resolvida na força bruta. O v2 tem **7**, **todos no reset global** (`global_v2.tsx:111-143` —
`font-family`, `font-size` e `text-decoration` do `body`, onde disputam com folhas de terceiros) e
**zero no `globalMaterialUi_v2.tsx`**. Em componente, não se usa.
