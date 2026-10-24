# Lições Frontend — ERP Valor Fiscal

> Erros reais encontrados em sessões anteriores. Leia antes de gerar qualquer arquivo frontend.

---

### [FE-001] Context file copiado de outro módulo com imports errados

**Contexto**: Ao criar um novo context (ex: `ServiceInvoiceCreateModalContext`), o arquivo era uma cópia do context de outro módulo (`BankSlipCreateModalContext`) com os imports antigos mantidos.

**Erro cometido**: o novo context importava types e services do módulo errado:
```typescript
// ERRADO — context de NFSe importando tipos de bank_slip
import { IResolvedInstallment, IGroupedAccount } from '../../types/financial/bank_slip.types'
import { resolveInstallments, createBatch } from '../../services/functions/financial/bank_slip.service'
```

**Regra correta**: sempre criar o context do zero com os types e services do módulo correto. Nunca copiar e modificar — o risco de esquecer algum import antigo é alto.

---

### [FE-002] Hook re-exportando função errada

**Contexto**: Hook de context criado como cópia do hook de outro módulo.

**Erro cometido**:
```typescript
// src/hooks/financial/useServiceInvoiceCreateModal.ts — ERRADO
export { useBankSlipCreateModal } from '../../context/financial/BankSlipCreateModalContext'
//       ^^^^^^^^^^^^^^^^^^^^ exporta nome errado do módulo errado
```

**Regra correta**:
```typescript
// src/hooks/financial/useServiceInvoiceCreateModal.ts — CORRETO
export { useServiceInvoiceCreateModal } from '../../context/financial/ServiceInvoiceCreateModalContext'
```

**Verificação obrigatória**: ao criar um hook que re-exporta de um context, confirmar que:
1. O nome da função exportada corresponde ao módulo
2. O path do context está correto

---

### [FE-003] Arquivos de outro módulo criados dentro da pasta do novo módulo

**Contexto**: Ao criar o módulo `service_invoice`, foram criados arquivos `BankSlipActionsModal` e `BankSlipsList` dentro da pasta `service_invoice/` — pertenciam ao módulo `bank_slip`.

**Causa**: agente copiou a estrutura de pastas do módulo de referência sem limpar os arquivos do módulo original.

**Regra correta**: ao criar um módulo novo baseado em um existente como referência, verificar e **apagar** todos os arquivos que pertencem ao módulo original antes de criar os novos.

**Verificação**: após criar um módulo, listar os arquivos e confirmar que não há nomes de outros módulos:
```bash
find src/pages/financial/service_invoice -type f | sort
# Não deve conter "BankSlip", "bankslip", etc.
```

---

### [FE-004] Step do modal com nome diferente do especificado

**Contexto**: Modal com 4 steps onde o Step 2 deveria ser `Step2Config` mas foi criado como `Step2Review` (cópia do padrão bank_slip).

**Erro cometido**: usar o nome genérico do módulo de referência em vez do nome semântico do novo módulo.

**Regra correta**: usar nomes semânticos para os steps que reflitam o conteúdo real:
- `Step1Review` → revisão de parcelas
- `Step2Config` → configuração (competência, discriminação) — NFSe
- `Step2Review` → revisão de encargos — BankSlip (diferente!)
- `Step3Issuing` → loading de emissão
- `Step4Result` → resultado

Ao criar um modal de emissão para um novo tipo de documento, definir os nomes dos steps antes de criar os arquivos.

---

### [FE-005] Step4Result usando hook/types do módulo errado

**Contexto**: `Step4Result` do modal NFSe usando `useBankSlipCreateModal` e `IBankSlipBatchResponse`.

**Erro cometido**:
```typescript
// ERRADO — Step4Result de NFSe usando hook de bank_slip
import { useBankSlipCreateModal } from '../../../../../hooks/financial/useBankSlipCreateModal'
import { IBankSlipBatchResponse } from '../../../../../types/financial/bank_slip.types'
```

**Regra correta**:
```typescript
// CORRETO
import { useServiceInvoiceCreateModal } from '../../../../../hooks/financial/useServiceInvoiceCreateModal'
import { INfseBatchResponse } from '../../../../../types/financial/service_invoice.types'
```

**Verificação obrigatória**: antes de finalizar qualquer step de modal, fazer `grep` por imports de outros módulos:
```bash
grep -r "bank_slip" src/pages/financial/service_invoice/
# Deve retornar vazio
```

---

### [FE-006] State do context com campos específicos do módulo de referência

**Contexto**: `ServiceInvoiceCreateModalContext` com campo `companiesBankDetailsId` no state — campo que pertence ao fluxo de boletos (bank_slip), não de NFSe.

**Erro cometido**: copiar o shape do state sem adaptar para o novo módulo:
```typescript
// ERRADO — state de NFSe com campo de bank account
interface IServiceInvoiceCreateModalState {
  companiesBankDetailsId: string  // ← não existe em NFSe
  groupedByAccount: IGroupedAccount[]  // ← agrupamento bancário, não faz sentido para NFSe
}
```

**Regra correta**: ao criar um novo context, definir o shape do state baseado nos dados que o módulo REALMENTE precisa:
```typescript
// CORRETO — state limpo para NFSe
interface IServiceInvoiceCreateModalState {
  isOpen: boolean
  status: TServiceInvoiceModalStatus
  installmentIds: string[]
  companiesId: string   // ← apenas o ID da empresa, sem conta bancária
  resolvedInstallments: IResolvedInstallmentForNfse[]
  validInstallments: IResolvedInstallmentForNfse[]
  invalidInstallments: IResolvedInstallmentForNfse[]
  batchResult: INfseBatchResponse | null
  processedCount: number
}
```

---

### [FE-008] CssDateField não aceita `views`, `error` ou `helperText` como props diretas

**Contexto**: `CssDateField` é `styled(DateField)` — o componente `DateField` do MUI tem API diferente do `DatePicker`.

**Erros cometidos**:
- `views={['month', 'year']}` → prop não existe em `DateField` (só existe em `DatePicker`)
- `error={...}` → prop não existe em `DateField` como prop direta
- `helperText={...}` → prop não existe em `DateField` como prop direta

**Regra correta**: `DateField` passa `error` e `helperText` via `slotProps.textField`. A prop `views` não existe — para restringir mês/ano use apenas `format="MM/yyyy"`.

**Exemplo errado**:
```tsx
<CssDateField
  views={['month', 'year']}     // ← TS2322: views não existe
  error={Boolean(errors.field)} // ← TS2322: error não existe como prop direta
  helperText="mensagem"         // ← TS2322: helperText não existe como prop direta
  onBlur={handleBlur}
/>
```

**Exemplo correto**:
```tsx
<CssDateField
  format="MM/yyyy"              // ← controla o formato, não tem views
  onChange={(newValue) => setFieldValue('field', newValue)}
  slotProps={{
    textField: {
      onBlur: handleBlur,
      error: Boolean(errors.field),
      helperText: errors.field ? String(errors.field) : undefined,
    },
  }}
/>
```

---

### [FE-009] `inputProps` deprecated no MUI v7 — usar `slotProps.htmlInput`

**Contexto**: MUI v7 deprecou `inputProps` em favor de `slotProps`.

**Erro cometido**:
```tsx
<CssTextField inputProps={{ maxLength: 1000 }} />  // ← deprecated TS6385
```

**Regra correta**:
```tsx
<CssTextField slotProps={{ htmlInput: { maxLength: 1000 } }} />
```

---

### [FE-010] Hook chamado condicionalmente após early return

**Contexto**: Componente React com `if (!data) return null` antes de um `useMemo`/`useCallback`.

**Erro cometido**:
```tsx
const MyComponent = ({ flow }) => {
  const { bp } = flow

  if (!bp) return null          // ← early return ANTES do hook

  const items = useMemo(() => [...], [bp])  // ← ESLint ERROR: hook condicional
}
```

**Regra correta**: todos os hooks devem ser chamados **antes** de qualquer `return` condicional. Mover o hook para cima e tratar o `!bp` dentro do `useMemo`:
```tsx
const MyComponent = ({ flow }) => {
  const { bp } = flow

  const items = useMemo(() => {  // ← hook ANTES do early return
    if (!bp) return []
    return [...]
  }, [bp])

  if (!bp) return null           // ← early return depois dos hooks
}
```

---

### [FE-011] Importar hook/função sem usar gera erro `no-unused-vars`

**Contexto**: Ao copiar padrões de outros flows, importar `useRef`, `useMemo`, `useCallback` ou variáveis que não são usadas na implementação final.

**Regra correta**: após escrever o componente/hook, revisar os imports e remover tudo que não for referenciado no código. Sinais de alerta: `useRef` sem `useRef<...>()` no corpo, `useMemo` sem `useMemo(` no corpo, variável declarada e nunca lida.

---

### [FE-012] `useCallback` com dependência desnecessária (`flow` inteiro)

**Contexto**: `useCallback` com `flow` (objeto completo do hook) na dependency array quando apenas funções específicas do flow são usadas.

**Erro cometido**:
```tsx
const handleResend = useCallback(async () => {
  await flow.resendConfirmation()
}, [flow, loading, resendCooldown, resendConfirmation])
//  ^^^^ desnecessário — já temos resendConfirmation extraída
```

**Regra correta**: extrair as funções necessárias via desestruturação e listar apenas elas:
```tsx
const { resendConfirmation } = flow  // ← desestruturar fora do useCallback
const handleResend = useCallback(async () => {
  await resendConfirmation()
}, [loading, resendCooldown, resendConfirmation])  // sem `flow`
```

---

### [FE-007] Coluna de DataGrid mostrando dados do módulo errado

**Contexto**: `Step1Review` de NFSe mostrando colunas de bank_slip (agência, conta, banco) em vez de colunas de NFSe (tipo NFSe, município, observação).

**Regra correta**: ao criar um Step1Review para um novo tipo de emissão, listar as colunas específicas do domínio antes de escrever o código. Para NFSe:
- ✅ Status (válida/inválida)
- ✅ Parcela
- ✅ Cliente + Documento
- ✅ Valor
- ✅ Tipo NFSe (Padrão / Nacional)
- ✅ Observação (motivo inválido)
- ❌ Agência, Conta, Banco (campos de bank_slip, não NFSe)

---

### [FE-013] Componente novo criado e nunca montado — o hook de lint não pega

**Contexto**: spec 015. Foram criados `DonorRejectionModal` e `RejectDonorAction`, ambos corretos e
lintados sem erro. A task foi marcada `[x]` com verificação "hook pós-edição passou". Só que
`RejectDonorAction` **não era importado por ninguém** — o modal só era usado por ele, e ele por
nada. A feature inteira de frontend era código morto e o critério de aceite humano
correspondente era inatingível. Descoberto pelo `verifier`, não pelo hook.

**Por que o hook não pega**: ESLint valida o arquivo isoladamente. Um componente órfão é
sintaticamente perfeito. `no-unused-vars` só acusa dentro do arquivo, nunca entre arquivos.

**Regra correta**: para todo componente/página novo, a verificação da task é o **grep do nome no
arquivo que o renderiza** — nunca só "o hook passou":

```bash
# Não basta: hook pós-edição passou
# Obrigatório:
grep -rn "RejectDonorAction" src/ --include=*.tsx
# Precisa retornar a definição E pelo menos um import em outro arquivo
```

Vale para: componentes, páginas, abas de formulário, modais, rotas e contexts.
Ao escrever a task no `tasks.md`, a linha "Verificação:" de um componente novo já deve nascer
com esse grep, não com "hook pós-edição passou".

**Status de promoção**: DELEGADA → `verifier` (inspeção de diff: todo componente novo tem de ter
ao menos um import fora do próprio arquivo). Não é promovível ao hook pós-edição, que enxerga um
arquivo por vez.

---

### [FE-014] Espelho de regra no frontend deve errar para o lado PERMISSIVO

**Contexto**: spec 025, achado do `verifier`. Irmã da FE-013 — as duas são sobre o que a tela
faz sem o servidor saber.

**Erro cometido**: o formulário de protocolo travava (abas somente leitura + botão salvar
escondido) sempre que o submit falhava:

```typescript
} catch (err) {
  setIsLocked(true)   // ← qualquer erro, não só o da regra
  ErrorMessage(err)
}
```

A intenção era espelhar a RN-10 (protocolo em uso não se edita). O efeito real foi que **qualquer**
400 — nome duplicado, exame inexistente, erro de rede — travava a tela e mostrava um aviso falso
de "protocolo já usado em requisições". No modo de cadastro o botão de contorno nem existia, então
o usuário perdia as quatro coleções já digitadas e precisava recarregar a página.

**Regra correta**: quando a tela **espelha** uma regra que o backend já garante, o espelho erra
para o lado permissivo. Travar é responsabilidade de quem tem a verdade.

- *fail-open* (não travar na dúvida): o backend recusa, o usuário vê o toast, o trabalho continua.
- *fail-closed* (travar na dúvida): transforma erro recuperável em trabalho perdido.

E o espelho precisa saber **na carga**, não por tentativa e erro: o backend deve devolver o estado
(ex.: `is_in_use` no `show/:id`) para a tela abrir já no modo certo. Descobrir a trava só ao clicar
em salvar é a mesma falha vista de outro ângulo — o usuário edita tudo antes de saber que não podia.

**Se precisar distinguir a causa pela mensagem**: acople a uma mensagem que tenha teste no backend
asserindo o texto (padrão da BE-001). Aí reescrever a mensagem quebra um teste antes de degradar o
frontend em silêncio.

**Automatizável?**: não — exige entender qual regra a tela está espelhando e quem detém a verdade.
**Delegada ao `verifier`**: ao auditar tela que desabilita campos ou esconde ações por regra de
negócio, conferir (1) se o gatilho distingue a causa real e (2) se o estado é conhecido na carga.

---

### [FE-015] `helperText={touched.x && errors.x}` não compila — `errors.x` pode ser `FormikErrors` aninhado

**Contexto**: spec 049, aba DADOS do paciente e modal de observação.

**O erro**: escrever o par de erro do Formik como

```tsx
error={touched.name && Boolean(errors.name)}
helperText={touched.name && errors.name}
```

O `tsc` reprova com `TS2322: Type 'string | false | string[] | FormikErrors<any> | ... ' is not
assignable to type 'ReactNode'`. O tipo de `errors.name` inclui `FormikErrors<any>` e
`FormikErrors<any>[]` — formas que o Formik usa para erro de objeto e de array aninhados, e que
não são renderizáveis.

**Regra correta** — o padrão que o projeto já usa (`ClinicFormRegisterData/index.tsx:466`):

```tsx
helperText={
  touched.name && typeof errors.name === 'string' && errors.name
}
error={Boolean(errors.name && touched.name)}
```

A guarda `typeof === 'string'` estreita o tipo e é o que torna a expressão um `ReactNode` válido.

**Por que escapa do hook**: o `post-edit-check.sh` roda ESLint no arquivo, e ESLint não faz
type-checking. Só aparece no `tsc --noEmit` do gate — depois de o arquivo já estar salvo e o
módulo inteiro escrito.

---

### [FE-016] Paginação server-side sem `paginationMode`/`onPaginationModelChange` torna a partir da 2ª página inalcançável

**Contexto**: spec 049, listagem de pacientes. Detectado pelo `verifier`, não pelos gates.

**O erro**: montar o `DataGridPro` com `rowCount={total}` vindo do backend, mas mandar
`page: 1, rowsperpage: 25` **fixos** no fetch e não declarar `paginationMode="server"` nem
`onPaginationModelChange`. A grade exibe "1–25 de 312" e o clique em "próxima" não faz nada
útil: o backend nunca recebe outra página. Do 26º registro em diante, ninguém é alcançável pela
tela.

**Regra correta**:

```tsx
const [paginationModel, setPaginationModel] = useState({ page: 0, pageSize: 25 })
// ...no fetch — o DataGrid conta a partir de 0, a API a partir de 1:
page: paginationModel.page + 1,
rowsperpage: paginationModel.pageSize,
// ...na grade:
paginationMode="server"
paginationModel={paginationModel}
onPaginationModelChange={setPaginationModel}
pagination
```

E o handler de filtro precisa voltar para `page: 0` — senão filtrar estando na página 3 cai numa
faixa que o novo resultado provavelmente não tem.

**Atenção**: vários módulos existentes têm este defeito, inclusive `clinics`, que é o módulo de
referência de CRUD. Copiar a listagem de lá propaga o problema. Vale uma varredura à parte por
`rowCount=` sem `paginationMode="server"`.

**Automatizável?**: sim. Guard para o `post-edit-check.sh`: em `**/pages/**/*List/index.tsx`,
falhar quando o arquivo contiver `rowCount=` e **não** contiver `paginationMode`.

---

### [FE-017] Condição terminal como gatilho de ação apaga o botão para sempre

**Contexto**: descoberto em 2026-08-19 (spec 039), pelo `verifier`. Passou em lint, typecheck e
no gate do frontend — nenhum deles sabe o que é "estado terminal".

**Erro cometido**: o botão que dispara a transferência das amostras para o container limpo foi
condicionado ao inverso do estado de conclusão:

```tsx
{!loading && aprovada && !transferStatus?.is_transferred && ( ...botão... )}
```

`is_transferred` é derivado de "existe ao menos um raque do doador no container limpo". Basta a
primeira transferência para ele virar `true` — e ele **nunca mais volta a `false`**. Um doador que
inicie um segundo ciclo produz material novo em quarentena e não tem nenhuma ação na tela capaz de
transferi-lo. Pior: o painel continuava exibindo a contagem de raques pendentes, ou seja,
**informava o problema e escondia a solução**.

**Por que passa despercebido**: no caminho feliz de um doador novo a tela se comporta exatamente
como o esperado — o botão aparece, some depois do uso, e o teste manual confirma. O defeito só
existe na segunda passagem, que ninguém exercita ao construir a feature.

**Regra correta**: a condição de exibir uma ação é **"há trabalho a fazer?"**, nunca **"o trabalho
já foi feito alguma vez?"**. As duas coincidem enquanto o processo acontece uma única vez na vida
do registro, e divergem no dia em que ele se repete — que em processo clínico é a regra, não a
exceção. Aqui a condição certa é a contagem de itens elegíveis, que volta a ser positiva a cada
ciclo:

```tsx
{!loading && material?.is_confirmed && material.items.length > 0 && ( ...botão... )}
```

Ao escrever a condição, pergunte: *este valor pode voltar ao estado anterior?* Se não pode, ele
descreve história, e história não decide o que a tela oferece agora.

**Irmã da FE-014**: no mesmo componente, a habilitação também vinha de `rodadas.find(r => r.status
=== 'APROVADA')` — regra de negócio espelhada no front — enquanto o backend já devolvia
`is_confirmed` pronto e o cliente HTTP existia sem consumidor. As duas coincidem hoje; divergem no
dia em que "estar confirmado" ganhar revogação ou validade.

**Automatizável?**: parcialmente, e cabe ao `verifier`. Guard sugerido: sinalizar JSX cuja
renderização condicional dependa da negação de um campo booleano cujo nome esteja no particípio
(`is_transferred`, `is_approved`, `is_sent`, `is_published`) — quase sempre é história sendo usada
como permissão.

---

### [FE-018] Select/Autocomplete montado sobre endpoint paginado sem `rowsperpage` explícito

**Contexto**: spec 043 (2026-08-20). O Autocomplete de "Titular" do relatório de estoque era
alimentado por `fetchDonorsByStage()`, chamado sem argumento. O `DonorsController` tem
`rowsperpage = 15` por padrão, então o campo oferecia **os 15 primeiros doadores da base** — e o
filtro por doador, que é a pergunta mais frequente da equipe (RN-08) e o que a CA-12 nomeia, não
alcançava quase ninguém.

**Por que passa por todos os gates**: a requisição funciona, o componente renderiza, o typecheck
e o lint não têm o que reclamar, e o teste (se houvesse) mockaria o service. O defeito só aparece
com volume real de dados — e aparece como "o sistema não acha o doador", que o usuário reporta
como dado faltando, não como bug de paginação.

**Por que é diferente da FE-016**: lá o problema é a 2ª página ficar inalcançável num DataGrid,
onde o usuário ao menos VÊ que existe paginação. Aqui não há próxima página: o que não veio na
primeira resposta **não existe** para quem usa o campo, e nada na tela denuncia o corte.

**Regra correta**: toda lista de seleção alimentada por endpoint paginado informa `rowsperpage`
explicitamente E avisa quando o teto foi atingido.

```typescript
const OWNER_OPTIONS_LIMIT = 500

const options = await fetchDonorsByStage(undefined, OWNER_OPTIONS_LIMIT)

setNotice(
  options.length >= OWNER_OPTIONS_LIMIT
    ? `Mostrando os primeiros ${OWNER_OPTIONS_LIMIT}. Refine os demais filtros.`
    : null,
)
```

Se a lista puder passar do teto com folga, o campo precisa de busca server-side (`search_name`
enviado a cada digitação), não de um teto maior.

**Corolário para o service**: função de listagem cujo backend tenha default baixo deve **exigir**
ou ao menos expor `rowsperpage` na assinatura, com comentário dizendo o default do controller.
Quem lê `fetchDonorsByStage()` não tem como adivinhar que recebe 15.

**Pergunta de revisão**: *quantos registros este campo oferece com a base de produção cheia?* Se
a resposta for "os que couberem na primeira página", está errado.

**Automatizável?**: parcialmente, e cabe ao `verifier`. Guard sugerido: sinalizar chamada de
service de listagem cujo resultado alimente `options=` de `Autocomplete`/`Select` sem
`rowsperpage` no objeto de params.

**Instância aberta conhecida** (2026-08-20): `pages/donors_services/DonorsWorkflow/index.tsx:161`
chama `fetchDonorsByStage(filterStage || undefined)` sem `rowsperpage` e monta o quadro com
`setDonors(data)` — 15 doadores por raia, em silêncio. **Não** foi corrigido junto da spec 043 de
propósito: alterar comportamento de tela alheia dentro de uma correção de auditoria é a AG-016 se
repetindo. Fica registrado para quem tocar naquela tela — a lesson descreve um padrão vivo, não um
caso encerrado.

---

### [FE-019] Piso de legibilidade: nada abaixo de 1.2rem — e `rem` não valia a mesma coisa nos três SPAs

**Contexto**: pedido do usuário em 2026-08-20 — "não deixar que o font-size do frontend em sua
totalidade seja menor que 1.2rem".

**A armadilha, achada ao tentar escrever a regra**: `1.2rem` significava **duas coisas
diferentes** dependendo do SPA.

| Workspace | `:root` | quanto valia `1.2rem` |
|---|---|---|
| `frontend/admin` | `60%`, `62.5%` a partir de 768px | **11,5px – 12px** |
| `frontend/portal` | *(nenhum — 16px do browser)* | **19,2px** |
| `frontend/professional` | *(nenhum — 16px do browser)* | **19,2px** |

Uma regra literal de "mínimo 1.2rem" aplicada aos três teria imposto piso de **19,2px** no portal
e no professional — texto maior que o corpo de texto atual deles. A regra certa, escrita sem olhar
a base do `rem`, produziria duas telas quebradas.

**Regra correta**: os três SPAs rodam com `:root { font-size: 62.5% }`, então **1rem = 10px** e o
piso é **1.2rem = 12px** em todos. Vocabulário desta casa:

| Uso | Tamanho |
|-----|---------|
| Corpo de texto, input, select | `1.6rem` |
| Tabela / DataGrid | `1.4rem` |
| **Menor texto legível** (helper, legenda, chip, badge) | **`1.2rem`** |
| Abaixo disso | não existe |

**Como o portal e o professional foram alinhados sem mudar nada na tela**: `:root: 62.5%` sozinho
encolheria os dois para ~62%. O que os torna equivalentes é o **par** com `htmlFontSize: 10` no
`theme.ts` — ele diz ao MUI que a raiz mede 10px, e o resultado é aritmeticamente idêntico ao de
antes:

```
antes:  body1 = 1rem   × 16px = 16px  |  caption = 0.75rem × 16px = 12px
depois: body1 = 1.6rem × 10px = 16px  |  caption = 1.2rem  × 10px = 12px
```

**Nunca mexer em um sem o outro.** `:root` sem `htmlFontSize` encolhe o app inteiro; `htmlFontSize`
sem `:root` infla o app inteiro. Os dois `theme.ts` carregam esse aviso no comentário.

**Automatizável?**: **PROMOVIDO em 2026-08-20** — `.claude/hooks/font-size-floor.py`, chamado pelo
`post-edit-check.sh` em todo arquivo sob `frontend/*/src/`. Ele compara **números**, não texto: um
grep precisaria listar os valores proibidos (`'1.1rem'`, `'1rem'`, `11`, `'11px'`, ...) e erraria
no primeiro valor novo que alguém escrevesse. Cobre `fontSize:`/`font-size:` em `sx`, `style`,
objetos de estilo e styled-components, em `rem` e em `px`; ignora `em`/`%` (relativos ao pai,
indecidíveis estaticamente), os enums do MUI (`fontSize="small"`) e linhas de comentário — para
que esta lesson e os templates possam **mostrar** o valor proibido sem serem reprovados por isso.

13 violações existentes foram corrigidas para o piso na mesma passagem. 4 delas eram
`font-size: 11px`/`10px` em styled-components, que um grep por `fontSize:` não pegaria.

---

#### ⚠️ Dívida aberta desta lesson — leia antes de confiar no piso

O hook cobre **valor literal escrito no código**. Ele NÃO cobre a maior fonte de texto miúdo do
`frontend/admin`, porque lá não há valor nenhum para ler:

**O `frontend/admin/src/theme.ts` não define `htmlFontSize`.** O MUI então calcula os variants
supondo raiz de 16px, enquanto o `:root` real é 10px:

| Variant | rem calculado | renderiza |
|---------|---------------|-----------|
| `body1` | `1rem` | **10px** |
| `body2` | `0.875rem` | **8,75px** |
| `caption` / `overline` | `0.75rem` | **7,5px** |
| `button` | `0.875rem` | **8,75px** |

É por isso que existem `globalMaterialUi.tsx` (722 linhas de `sx` corrigindo componente a
componente) e ~155 `fontSize` inline no admin: são compensação manual, uma de cada vez, de um
default errado. Reforço de que é isso mesmo: os dois valores mais escritos à mão são `1.4rem`
(41×) e `1.6rem` (27×) — exatamente o que `body2` e `body1` produziriam com `htmlFontSize: 10`.

A correção é **uma linha** — `typography: { htmlFontSize: 10 }` — mas re-renderiza todo componente
MUI ainda não compensado (de ~10px para 16px) num ERP em produção. Decisão do usuário em
2026-08-20: **não agora**, fica registrado como dívida para ter janela própria. O portal e o
professional **já nascem com ela**.

**Segundo item aberto**: o `:root` do admin é `60%` abaixo de 768px (`62.5%` só a partir daí), o
que faz `1.2rem` valer **11,52px no mobile** — abaixo do próprio piso. Mudar `60%` → `62.5%`
alinharia, e também é mudança visual em produção. Não foi feito pelo mesmo motivo.

**Enquanto a dívida existir**, `<Typography variant="caption">` e `variant="body2"` no admin
rendem 7,5px e 8,75px **sem disparar o hook** — não há literal para ele ler. No admin, texto
pequeno se resolve com `fontSize` explícito (≥ `1.2rem`) ou com os estilos de
`globalMaterialUi.tsx`, não com o variant cru.

---

### [FE-020] Trocar o modo de montagem de um componente destrói ou congela estado — nos DOIS sentidos

**Contexto**: descoberto na spec 069 e repetido **três vezes na mesma feature**, em quatro
rodadas de auditoria. Nenhuma das três foi pega por lint, `tsc` ou testes.

**A pergunta que resolve as três**:

> *Que estado deste componente foi construído por INTERAÇÃO e não é reconstruído na MONTAGEM?*

Toda vez que o modo de montagem muda — renderização condicional ⇄ `display` ⇄ aba de `TabPanel` —
esse estado muda de destino, e o compilador não tem como saber.

**Ocorrência 1 — condicional → `display`: o efeito de mount passa a rodar cedo demais.**
Os passos de um wizard alternavam por renderização condicional; trocados por `display`, todos
passaram a montar junto com o pai. Um `useEffect` que lia o volume do diluído — escrito no passo
ANTERIOR — rodava **uma vez, antes de o dado existir**, e nunca mais. O campo ficava vazio para
sempre e a gravação era recusada com *"informe o volume do diluído"* logo depois de o operador
tê-lo informado.
→ Correção: efeito próprio, disparado por uma prop `visible`, separado do efeito de mount.

**Ocorrência 2 — `display` → condicional: estado derivado morre e ninguém o reconstrói.**
O painel de alocação passou a desmontar. Os mapas de opções de canister e raque eram populados
**só por interação**; remontado com as linhas preenchidas, os `<select>` nativos ficavam em
branco — valor sem `<option>` correspondente não renderiza. E o payload continuava íntegro:
gravaria material biológico num destino que a tela não mostrou, com toast de sucesso.
→ Correção: efeito de montagem que re-hidrata as opções a partir das linhas, **no próprio filho**,
para que ele fique correto independentemente de quem o monta.

**Ocorrência 3 — wizard → aba: agora quem morre é o estado do PAI.**
`TabPanel` renderiza `{value === index && children}` — sair da aba desmonta de verdade. Corrigir o
filho (ocorrência 2) deixou de bastar: o `useState` das linhas de alocação vivia no componente da
aba e não era reconstruído de lugar nenhum. Trocar de aba e voltar devolvia o formulário vazio —
justamente no caminho que a própria tela induz ("volte à aba anterior e complete o Diluído").

**Regra**:

1. Antes de mudar o modo de montagem, liste o estado do componente e classifique cada item:
   **vem do servidor** (recarrega sozinho), **derivado de props** (recalcula), ou **construído por
   interação** (morre, e ninguém o traz de volta).
2. O terceiro grupo é o perigoso. Ou ele sobe para um componente que sobrevive, ou é reconstruído
   num efeito de montagem, ou o requisito de sobrevivência precisa ser revogado **explicitamente**.
3. `<select>` nativo com `value` sem `<option>` correspondente **renderiza vazio**. Um campo em
   branco enquanto o payload leva o id certo é pior que um erro: a tela discorda do que vai gravar.
4. Efeito que lê dado escrito em OUTRO passo/aba não pode ficar no mesmo `useEffect` dos que leem
   dado estático (catálogos, listas de apoio).

**Por que passa despercebido**: é estado de tempo de execução. `tsc` compila, ESLint não vê,
e o teste só pega se alguém **montar o componente com o estado já preenchido** — que é
exatamente o cenário que ninguém escreve por não parecer um caso.

**Como travar**: teste de montagem com `@testing-library/react` entregando props já preenchidas,
e **teste de mutação** para provar que ele é portador de carga. Precedente:
`DonorCollectionFormFreezingAllocation/index.spec.tsx` — neutralizando a re-hidratação, 3 de 4
casos ficam vermelhos.

**Automatizável?** **Parcialmente, e vale promover ao `verifier`**: num diff que troque
renderização condicional por `display` (ou o inverso), ou que mova um componente para dentro de um
`TabPanel`, auditar cada `useState` do componente afetado contra a pergunta do topo. O gate
mecânico não pega — três rodadas de auditoria provaram isso.

⚠️ **Esta lesson nasceu tarde de propósito registrado**: as duas primeiras ocorrências ficaram
anotadas só no `tasks.md` da feature, como "lição candidata". A terceira aconteceu porque
`tasks.md` de uma spec não alcança a spec seguinte. **Lição que não sobe para cá não existe.**

---

## FE-021 — O harness não estava pronto para teste de componente, e o vermelho mentia de três jeitos [PROMOVIDA (parcial) → hook]

**Contexto**: a spec 069 precisou do primeiro teste que RENDERIZA uma tela deste projeto. Os
testes existentes eram de função pura ou de formulário simples. Três obstáculos apareceram em
sequência, nenhum deles no código que se queria testar — e os três produzem vermelho (ou verde)
que aponta para o lugar errado.

### 1. `resetMocks: true` do CRA apaga a implementação dos mocks

`react-scripts/scripts/utils/createJestConfig.js:68` liga `resetMocks`. Implementação declarada
**dentro da factory do `jest.mock`** é apagada antes de cada teste:

```ts
// ❌ a implementação NÃO sobrevive ao início do teste
jest.mock('../../services/x.service', () => ({
  __esModule: true,
  fetchX: jest.fn().mockResolvedValue({ x: [] }),   // vira jest.fn() => undefined
}))

// ✅ declara vazio, implementa no beforeEach
jest.mock('../../services/x.service', () => ({
  __esModule: true,
  fetchX: jest.fn(),
}))
beforeEach(() => {
  ;(fetchX as jest.Mock).mockResolvedValue({ x: [] })
})
```

**O que custa**: o componente quebra em todo lugar que consome o service, com erros do tipo
`Cannot read properties of undefined`. Na spec 069 foram **cinco** falhas simultâneas que não
tinham nada a ver com o defeito investigado — e por pouco não levaram a "corrigir" o componente
errado.

### 2. `TextEncoder` não existe no jsdom, e `DataGridPro` não sobe sem ele

`@mui/x-internals/hash` usa `TextEncoder` no topo do módulo. Sem polyfill, **nenhuma suíte que
renderize `DataGridPro` sequer carrega** — morre no import, antes de qualquer asserção. Como este
projeto lista tudo com `DataGridPro`, a alternativa seria mockar a grade em cada spec, o que
testaria o mock e não a tela. O polyfill vem do `util` do Node, sem dependência nova, e vive em
`src/setupTests.ts`.

### 3. Vermelho intermitente que é TEMPO, não código

Sintoma: os specs passam isolados, ficam vermelhos em conjunto, **e não nos mesmos casos a cada
rodada**. Causa: o `asyncUtilTimeout` do Testing Library é 1000ms; telas com Formik + MUI + vários
efeitos de carga levam mais que isso quando o Jest paraleliza.

**Diagnóstico, que é a parte durável desta lição**:

> Vermelho que muda de caso entre rodadas + `--runInBand` verde ⇒ é tempo, não código.

⚠️ **Ao elevar, eleve OS DOIS números.** O `testTimeout` do Jest é 5000ms e o CRA não o expõe no
`package.json`: um `asyncUtilTimeout` acima disso é inalcançável, e o vermelho volta com o genérico
"Exceeded timeout of 5000 ms" em vez da mensagem do RTL, que diz QUAL elemento não apareceu. Um
número escrito e inalcançável é pior que o número antigo — ele mente para quem o lê.

**Por que isso importa mais do que parece**: teste instável **ensina a ignorar vermelho**. Um
vermelho legítimo, na rodada seguinte, seria descartado como "flaky" — e a auditoria perderia o
achado. Teste instável é pior que teste nenhum.

**Automatizável?** **O item 1 sim, e foi promovido ao hook**: é sintático — `.mockResolvedValue(`
ou `.mockReturnValue(` dentro da factory de um `jest.mock(`, em `*.spec.tsx`. Sem falso positivo
plausível, e pega o erro no ato de escrever. Os itens 2 e 3 são de configuração única, já resolvidos
em `src/setupTests.ts`; o que fica aqui deles é o **diagnóstico**, que exige julgamento.

---

## FE-022 — Assinatura de função não descreve o comportamento em runtime: leia o CORPO

**O erro**: numa varredura por um defeito conhecido, classifiquei cinco arquivos como
"tem/não tem o defeito" pelo **nome e pela assinatura** da função (`toNumberOrNull(value: string)`).
Reportei ao usuário que uma tela estava quebrada. **Não estava** — o corpo daquele arquivo fazia
`Number(value)` direto, sem nenhum método de string. E o arquivo que estava de fato quebrado, e era
o mais grave dos dois, **não estava na minha lista**.

**A raiz concreta**: o `handleChange` do Formik **converte para número** o valor de todo input
`type="number"`. Um campo declarado `string` no `IValuesForm` chega ao submit como número. Chamar
`.trim()` nele lança `TypeError` — dentro do `try` do salvamento, antes da chamada seguinte, que
nunca acontece. O sintoma na tela é "salvou uma parte e a outra não", e o recorte da parte perdida
é exatamente a linha em que a exceção caiu.

**Regra**:

1. Assinatura `(value: string)` **não garante** que chega string. Se um `type="number"` do Formik
   alimenta o campo, chega número — e o `tsc` não pega, porque quem quebra a promessa é a
   biblioteca em tempo de execução.
2. Numa varredura, **leia o corpo de cada ocorrência**. Mesmo nome e mesma assinatura não são o
   mesmo comportamento; o que decide é se o corpo chama método de string.
3. **O escopo do grep é o workspace, não o arquivo editado** (AG-017). Nesta mesma varredura eu
   registrei "0 campos `type="number"`" para um arquivo cujo campo numérico vivia num componente
   FILHO. O movimento concreto: `grep -rn 'type="number"' <pasta do componente>` — pai **e**
   filhos — e depois seguir o `onChange` de cada acerto.
4. Ao concluir que algo é seguro, registre o **motivo certo**. Aquele arquivo é seguro porque o
   `onChange` **não é o do Formik** (callback próprio, e `HTMLInputElement.value` é sempre string) —
   e não por "não ter campo numérico". Trocar o callback pelo do Formik, um dia, quebra sem que nada
   acuse. Motivo errado registrado é armadilha para o próximo.

**Automatizável?** **Não com confiança**: exige cruzar `type="number"` (possivelmente num
componente filho) com o conversor que recebe aquele campo. Um grep que ligasse os dois teria falso
positivo demais para servir de gate. **Delegado ao `verifier`**: em diff que toque conversor
numérico ou campo `type="number"` de formulário Formik, conferir corpo × origem do valor.

---

## FE-023 — Crase dentro de comentário CSS fecha o template do `styled` [PROMOVIDA → hook (`styled-template-backtick.py`)]

**Contexto**: bloco `MODAL` novo no `styles/global_v2.tsx` (migração da aba Contatos da clínica).

**O erro**: um comentário CSS *dentro* do template de um styled-component citava um componente
entre crases, do jeito que os JSDoc do arquivo fazem:

```tsx
export const ModalSurface = styled.div`
  /* A sombra é mais funda que a do `FormSurface` … */   // ⛔ a crase FECHA o template
```

Dentro do template, o comentário não é comentário de JS: é **texto da string**. A crase termina o
template literal ali, e o resto do arquivo passa a ser interpretado como código.

**Por que virou hook próprio, já que o ESLint pega**: porque a mensagem dele **não descreve a causa
e aponta o lugar errado**:

```
1146:37  error  Parsing error: ',' expected
```

A linha 1146 é a do comentário e a coluna 37 é a crase — mas "`,` expected" manda procurar erro de
sintaxe em objeto/argumento, que é onde não está. Perde-se tempo relendo a interface e o genérico
do `styled.div<Props>`.

**Regra**: comentário dentro do template ou **escreve o nome puro**, ou **escapa a crase** (`` \` ``)
— as duas compilam. O `global_v2.tsx` já usa a segunda no reset, para citar
`` \`typography.htmlFontSize\` ``. Só os JSDoc de FORA do template usam crase solta.

**Promovida** para `.claude/hooks/styled-template-backtick.py`, chamado pelo `post-edit-check.sh`
em qualquer `.ts`/`.tsx` que contenha `styled`. O detector varre o template de um styled e, ao achar
`/*`, procura o primeiro `*/` ou crase **não escapada**: se a crase vier antes, ela fechou o
template dentro do comentário. Validado contra o caso real e contra os 3 SPAs inteiros — zero falso
positivo. A mensagem dá a linha do comentário que abriu e a da crase, **antes** de o ESLint imprimir
o `Parsing error`.

⚠️ **O escape era o ponto cego da primeira versão desta lesson**, que dizia "comentário dentro do
template não cita código com crase". É falso: escapada, cita. Descobri escrevendo o detector — ele
reprovou o `global_v2.tsx`, que estava certo. **Regra escrita a partir de um único caso tende a ser
mais restritiva que a verdade**; o detector é que obriga a enunciar a condição exata.

**A lição maior**: eu escrevi esta lesson e **repeti o erro na edição seguinte**, no mesmo arquivo.
Ler a lesson não protegeu; o hook protege. É a razão de a política do README mandar promover.

Registrado também no `documentacao/Ui_Ux/PADRAO-UI-V2.md` §3.

---

## FE-024 — `slots={{ backdrop: Backdrop }}` põe o escurecimento NA FRENTE do modal [PROMOVIDA → hook]

**Contexto**: primeiro modal do padrão v2 (`ModalSurface` + `CssModalForm`), na aba Contatos da
clínica. Copiei o `slots={{ backdrop: Backdrop }}` da chamada v1 sem perguntar o que ele fazia.

**O sintoma**: o cartão do modal inteiro cinza, como se estivesse *atrás* do backdrop — e só os
campos de texto brancos, por cima. Título, divisórias e botões visíveis, mas acinzentados.

**A causa**: `@mui/material/Modal` tem backdrop próprio —
`const ModalBackdrop = styled(Backdrop)({ zIndex: -1 })` — e o usa por padrão
(`BackdropComponent = ModalBackdrop`). Passar `slots={{ backdrop: Backdrop }}` troca esse componente
pelo `Backdrop` **cru**, cujo root é `position: fixed` **sem `z-index`**.

Sem o `-1`, a ordem de pintura do CSS (Apêndice E) decide assim:

| Passo | O que pinta | Quem, aqui |
|---|---|---|
| 3 | fundo de descendentes em fluxo, **não posicionados** | o cartão (`ModalSurface`, `position: static`) |
| 6 | descendentes **posicionados** de `z-index: auto` | o backdrop, e depois os inputs |

O backdrop sobe do passo 2 (onde o `-1` o punha) para o 6, ficando acima do cartão. Os inputs do MUI
são `position: relative` e vêm **depois** no DOM, então ficam acima do backdrop — daí só eles
parecerem brancos.

**Por que o v1 não mostrava isso**: `CssBoxModalForm` declara `position: 'relative'`. Isso levava o
cartão para o passo 6 também, à frente do backdrop. Ou seja: o `position: relative` do v1 era o
remendo de um bug que as 62 chamadas carregam.

**Regra**: **não passar `slots` para o backdrop do `Modal`**. `slotProps={{ backdrop: { timeout } }}`
funciona sozinho — é mesclado no slot padrão. Nas 62 migrações do v1, o `slots={{ backdrop: Backdrop }}`
e o `import { Backdrop }` **saem**.

**Automatizável?** **Sim — PROMOVIDA → hook**, em duas barreiras:

1. O `CssModalForm` v2 repõe o `-1` (`'& > .MuiBackdrop-root': { zIndex: -1 }`): quem trouxer o
   override do v1 ainda renderiza certo.
2. O `post-edit-check.sh` reprova `slots={{ backdrop:` em arquivo que importe do
   `globalMaterialUi_v2` — é a barreira que **ensina**, porque faz o override sair do código em vez
   de ficar lá sendo neutralizado em silêncio.

⚠️ A primeira versão da regra rodava sobre o arquivo cru e **reprovou a própria aba de contatos** —
que cita o antipadrão num comentário justamente para explicar por que não usá-lo. É a BE-022 de
novo, e o hook já avisava: *"as checagens rodam sobre o CÓDIGO, não sobre o arquivo cru"*. A regra
agora filtra linhas de comentário antes do grep.

**A lição maior**: nenhum gate pega o bug original. ESLint e `tsc` passaram, o webpack compilou, o
bundle continha tudo. **Só a tela mostrou.** Prop copiada de código v1 sem se perguntar o que faz é
dívida que atravessa a verificação mecânica inteira — e é por isso que ela virou hook.


---

## FE-025 — Espelhar uma tela de outro módulo NÃO espelha o contrato da rota

**Contexto**: reconstrução das abas filhas de `carriers` a partir das de `providers`. Os dois
módulos têm as mesmas entidades filhas (contato, endereço, observação), os mesmos envelopes de
resposta e as mesmas telas. Gerei `carriers` por substituição de nomes sobre `providers`.

**O erro**: veio junto um comentário — e o payload correspondente — dizendo que o `PUT` de endereço
**não leva** o id do pai. Isso é verdade em `providers` e **falso em `carriers`**:

| rota | `PUT` de endereço |
|---|---|
| `providersAddresses.routes.ts` | `Joi.object().keys({ providers_addresses_id, ...addressBody })` — **sem** `providers_id`, e sem `.unknown()`: mandá-lo devolve 400 |
| `carriersAddresses.routes.ts` | `carriers_id: Joi.string().uuid().required()` — **omiti-lo** devolve 400 |

São exigências **opostas**, em módulos que parecem gêmeos. O update de endereço da transportadora
teria falhado com 400 em toda edição.

**Por que nenhum gate pegaria**: ESLint e `tsc` passam — o payload é `object`, e nenhum tipo do
frontend descreve o schema Joi do backend. Só a tela mostra, e só se alguém editar um endereço.

**Regra**: ao espelhar uma tela de outro módulo, **abrir o `*.routes.ts` dos dois** e comparar
`[Segments.BODY]` chave a chave, para cada verbo. O que se copia é a FORMA da tela; o contrato é de
cada módulo e não viaja junto. Vale especialmente para comentário copiado: ele afirma algo sobre o
backend, e afirmação copiada de outro módulo é palpite.

**Automatizável?** **Não com confiança.** Exigiria ligar o payload de uma chamada do frontend ao
schema Joi da rota correspondente no outro workspace — os dois têm `.git` próprio e nenhum tipo
compartilhado. **Delegado ao `verifier`**: em diff que crie/edite chamada de `create`/`update` de
service, conferir as chaves do payload contra o `[Segments.BODY]` da rota.

### ⚠️ Emenda (spec 092, 2026-09-14) — a lesson existia e não impediu a 2ª ocorrência

`storage_containers` e `storage_canisters` repetiram o erro **na íntegra**, copiando de `clinics`:
o `PUT` mandava `status` (chave que a rota não declara) e omitia `is_active` (que ela exige como
`required`). Duplo motivo de 400, em **toda** edição de container e de canister — e o mesmo copiar
levou o modal do canister a nunca enviar `reed_unit_volume_ml`/`vial_unit_volume_ml`, de modo que
todo canister nascia sem volume, em silêncio, porque no Joi eles são `optional`.

Ou seja: **quatro defeitos**, um deles silencioso, numa classe que já tinha lesson escrita. A lesson
não falhou por estar errada — falhou porque está delegada ao `verifier`, e a feature que introduziu
o `status:` não rodou `verifier`. Regra que depende de alguém lembrar de invocá-la protege apenas
quem já ia acertar.

**O caminho de automação que esta lesson não considerava**: a razão de o `tsc` não pegar nada disso
está declarada no próprio frontend —

```ts
export async function update(payload: object): Promise<IStorageContainer> {
```

`payload: object` aceita qualquer coisa. Tipar os payloads de `create`/`update` dos services HTTP
com interfaces que espelhem o `[Segments.BODY]` põe a checagem **dentro de um único workspace**, sem
precisar cruzar os dois `.git` — que é exatamente a objeção que o parágrafo acima levanta. Não
resolve divergência de valor (um `is_active` escrito certo e com semântica errada), mas mata a
classe inteira de "chave que a rota não conhece" e "chave obrigatória omitida", que é onde os 4
defeitos caíram.

Fora do escopo da 092 (mudaria assinatura usada por outras telas), e registrado aqui como a pergunta
a fazer na próxima revisão desta lesson: **promover a FE-025 de `verifier` para `tsc`.**

---

## FE-026 — Módulo com telas comentadas: `carriers` já fez isso três vezes

**Contexto**: ao migrar as abas filhas de `carriers` para o padrão v2, as três estavam **inertes** —
`load`, `create`, `update` e `delete` inteiramente dentro de `/* */`, com um
`// eslint-disable-next-line @typescript-eslint/no-unused-vars` sobre o state para calar o aviso que
sobrava. A tabela renderizava sempre vazia. O backend existia e funcionava.

**É a terceira ocorrência no mesmo módulo**: o cabeçalho de `types/carriers.types.ts` registra a
listagem ("renderizava uma linha fictícia fixa e tinha a chamada de API comentada") e o §7 do
PADRAO-UI-V2 registra o `CarriersFormRegisterData` ("o `initialValues` era `{}` e o `onSubmit`
estava comentado").

**A armadilha de detecção**: um `grep -v` de linhas que *começam* com `//` ou `*` **não** encontra
isso. Dentro de um bloco `/* */`, as linhas de código mantêm a indentação normal e não começam com
marcador nenhum. Meu primeiro levantamento deu "3 de 3 chamadas ativas" para um arquivo em que
**nenhuma** estava. Só um removedor de comentários de verdade (varrer `/* */`, `//`, strings) mostrou
o estado real.

**Regra**:

1. Antes de migrar uma tela, **verificar que ela funciona**. Migrar o visual de uma tela morta
   entrega algo que *parece* pronto — e o estado vazio do padrão passa a mentir, dizendo "nenhum
   registro cadastrado" quando nada foi buscado.
2. Para checar, **remover comentários de verdade**, não filtrar linhas por prefixo.
3. Em `carriers`, **presumir** que pode haver código comentado até provar o contrário.
4. Tela morta encontrada é **decisão do usuário**: reconstruir, migrar só o visual, ou pular. Não é
   escolha de quem implementa.
