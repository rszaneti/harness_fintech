# Lições para Agentes — ERP Vida Fertil

> Erros específicos que acontecem quando agentes geram múltiplos arquivos de uma vez.
> Agentes: leia este arquivo inteiro antes de criar qualquer arquivo no projeto.

---

### [AG-001] Criar módulo completo quando foi pedido apenas stub

**Contexto**: Quando o prompt diz "crie uma referência a um módulo que outro programador está fazendo", o agente criou o módulo DDD completo (DTOs, repository, services, controller, routes) em vez de apenas a entity stub.

**Regra correta**: se o prompt diz que outro programador está criando o módulo, criar APENAS:
```
src/modules/parameters/<modulo>/infra/typeorm/entities/<Entity>.ts  ← apenas isso
```

Nunca criar repository, services, controller ou routes para módulos de outros.

---

### [AG-002] Copiar arquivos de módulo de referência sem limpar

**Contexto**: Ao criar o módulo `service_invoice` usando `bank_slip` como referência, o agente trouxe junto `BankSlipActionsModal` e `BankSlipsList` para dentro da pasta `service_invoice/`.

**Regra correta**: usar o módulo de referência APENAS para entender padrões e estrutura. Nunca copiar arquivos — criar cada arquivo do zero com os nomes e imports corretos do novo módulo.

**Checklist antes de finalizar**:
```bash
# Nenhum desses comandos deve retornar resultado
grep -r "bank_slip" src/pages/financial/service_invoice/ 2>/dev/null
grep -r "BankSlip" src/pages/financial/service_invoice/ 2>/dev/null
```

---

### [AG-003] Hook re-exportando função do módulo errado

**Contexto**: Agente criou `useServiceInvoiceCreateModal.ts` re-exportando `useBankSlipCreateModal` do context de bank_slip.

**Regra correta**: ao criar um hook que re-exporta de um context, verificar que:
1. O nome da função exportada corresponde ao módulo (`useServiceInvoiceCreateModal`, não `useBankSlipCreateModal`)
2. O path de import aponta para o context correto

**Padrão obrigatório**:
```typescript
// src/hooks/financial/use<ModuloXxx>CreateModal.ts
export { use<ModuloXxx>CreateModal } from '../../context/financial/<ModuloXxx>CreateModalContext'
//        ^^^^^^^^^^ nome DEVE bater com o módulo
```

---

### [AG-004] Import de AppError em service que não lança AppError

**Contexto**: Services que usam try/catch para APIs externas (PlugNotas, Bradesco) — o agente sempre importa `AppError` por hábito, mesmo quando o service nunca lança `new AppError()`.

**Regra correta**: Só adicionar `import AppError from '@shared/errors/AppError'` se o arquivo contém `throw new AppError(...)` em algum lugar.

**Verificação rápida antes de salvar cada service**:
- Se tem `throw new AppError` → manter o import
- Se NÃO tem `throw new AppError` → remover o import

---

### [AG-005] Variável inicializada e sobrescrita (no-useless-assignment)

**Contexto**: Em services que chamam APIs externas com try/catch, o agente declara variáveis com valor inicial vazio que é sempre sobrescrito.

**Regra correta**: Declare sem inicializar quando o try e o catch sempre atribuem o valor:

```typescript
// ERRADO
let result: Record<string, unknown> = {}  // ESLint: no-useless-assignment

// CORRETO
let result: Record<string, unknown>
```

**Condição**: só omitir a inicialização se AMBOS try e catch atribuem o valor. Se houver código antes do try que pode retornar early (sem atribuir), manter a inicialização.

---

### [AG-006] Ordem de imports e registros de rotas

**Contexto**: Rotas de webhook público sendo registradas depois do `routes.use(ensureAuthenticated)`.

**Regra obrigatória** ao modificar `src/shared/infra/http/routes/index.ts`:

```typescript
// SEMPRE nesta ordem:
// 1. Rotas públicas (webhooks, sessões)
routes.use('/webhook/plugnotas/nfse', webhookRoutes)   // ← ANTES do auth
routes.use('/sessions', sessionsRoutes)                  // ← ANTES do auth

// 2. Middleware de auth
routes.use(ensureAuthenticated)

// 3. Rotas privadas
routes.use('/serviceinvoice', serviceInvoicesRoutes)
```

**Verificação**: após adicionar rotas, confirmar com `grep -n "ensureAuthenticated\|webhook"` que webhooks aparecem em linhas com número MENOR que o `routes.use(ensureAuthenticated)`.

---

### [AG-007] State do context com campos do módulo de referência

**Contexto**: Context de NFSe criado com campos de bank_slip (`companiesBankDetailsId`, `groupedByAccount`).

**Regra correta**: definir o shape do state baseado no NOVO módulo, não no módulo de referência. Sempre partir do zero para o state, não copiar e modificar.

**Para modais de emissão em lote**, o state mínimo é:
```typescript
interface IXxxCreateModalState {
  isOpen: boolean
  status: 'idle' | 'resolving' | 'review' | 'issuing' | 'result'
  errorMessage: string | null
  installmentIds: string[]
  companiesId: string
  resolvedInstallments: IResolvedXxxItem[]
  validInstallments: IResolvedXxxItem[]
  invalidInstallments: IResolvedXxxItem[]
  batchResult: IXxxBatchResponse | null
  processedCount: number
}
```

Adicionar apenas campos que o NOVO módulo realmente precisa.

---

### [AG-008] Tamanho de prompt e contexto em agentes

**Regra prática**: agentes com prompt muito longo (>800 linhas) tendem a perder precisão nos últimos arquivos. Para tarefas com 50+ arquivos, preferir dividir em dois agentes sequenciais:
1. Primeiro: backend (migrations, entities, repositories, services, controllers, routes)
2. Segundo: frontend (types, services HTTP, contexts, components, pages, routes)

---

### [AG-010] Service de batch retornando array bruto em vez de objeto com metadados

**Contexto**: Services de emissão em lote que processam múltiplos itens sequencialmente.

**Erro cometido**: o service retornou `IBatchResult[]` (array direto), mas o frontend esperava `{ total, success_count, failure_count, results }`. Causou `Cannot read properties of undefined (reading 'map')` no Step4Result ao tentar acessar `batchResult.results`.

**Campo também errado**: o campo de erro no item foi gerado como `error` mas o frontend esperava `error_message`.

**Regra correta**: services de batch SEMPRE devem retornar o objeto estruturado:
```typescript
interface IBatchResponse {
  total: number
  success_count: number
  failure_count: number
  results: IBatchResult[]
}

// No final do execute():
const success_count = results.filter((r) => r.success).length
const failure_count = results.filter((r) => !r.success).length
return { total: results.length, success_count, failure_count, results }
```

**Campo de erro**: padronizar como `error_message` (não `error`) para alinhar com o frontend.

**Defesa no frontend**: sempre usar `(batchResult.results ?? []).map(...)` para evitar crash se o backend retornar formato inesperado.

---

### [AG-009] Verificar com find antes de declarar sucesso

**Regra obrigatória**: ao finalizar a geração de um módulo, SEMPRE executar:
```bash
find src/modules/<contexto>/<modulo> -type f | sort
```

E conferir que TODOS os arquivos esperados foram criados antes de declarar o trabalho concluído.

---

### [AG-011] Corrigir um bug sem confirmar que o estado corrigido é ALCANÇÁVEL

**Contexto**: spec 029. Seis rodadas de auditoria, seis achados ALTOS — e **quatro deles foram
introduzidos ou perpetuados pela própria correção da rodada anterior**. Nenhum foi pego por
ESLint, typecheck ou testes: todos passavam nos três gates.

**O erro, em uma frase**: escrever a correção contra o estado que torna a hipótese verdadeira, em
vez do estado que o fluxo real produz.

**As três formas que ele assumiu** (todas na mesma feature):

1. **Filtrar um status inalcançável.** A fase travava porque uma aprovação de rodada anterior
   contava para sempre. A correção filtrou requisições `CANCELADA` — só que a requisição que
   recebeu o laudo fica em `LAUDO_RECEBIDO`, estado **terminal**, e o serviço de cancelamento
   recusa explicitamente ("Requisição com laudo recebido não pode ser cancelada"). O filtro cobria
   um estado que o fluxo que gerou o bug nunca produz. **O bug seguiu intacto por mais uma rodada.**

2. **Gravar a marca num ramo que a UI não percorre.** A correção seguinte marcava a rodada como
   encerrada no endpoint de decisão da própria feature. Só que a tela reprova pelo modal de
   rejeição compartilhado, que fala com outro endpoint — decisão de escopo registrada no próprio
   `tasks.md` da spec. **No produto entregue a marca nunca era escrita.**

3. **Asserir o que confirma a hipótese.** Três testes seguidos, em três rodadas, asseriam
   `has_rejection === false` — a métrica que já estava resolvida — em vez de `is_complete === true`,
   que é o que o teste dizia no nome ("fecha a fase") e o que o usuário precisa. Acrescentar a
   asserção que faltava fazia o teste falhar imediatamente.

**Regra correta** — ao corrigir um bug, antes de escrever a correção, responder por escrito:

| Pergunta | Por que ela pega o erro |
|----------|-------------------------|
| Qual **fluxo real** produz o bug? | Força enumerar os passos, e é onde aparece que o estado assumido não ocorre |
| O estado que estou filtrando/marcando é **alcançável por esse fluxo**? | Pega o caso 1 |
| **Quem escreve** o dado que a correção lê? Esse caminho é percorrido pela UI? | Pega o caso 2 |
| Se a correção fosse revertida, **qual asserção do meu teste falharia**? | Pega o caso 3 — se a resposta for "nenhuma", o teste não prova nada |

A última é a mais barata e a que mais rende: **um teste que passa com e sem a correção não é
teste da correção.**

**Sinal de alerta específico**: quando o cenário do teste precisa de um estado que o fluxo não
consegue atingir (uma requisição cancelada que não pode ser cancelada, um usuário sem permissão
que a tela não deixa existir), o teste está descrevendo a hipótese, não o sistema.

**Automatizável?**: **não** por hook nem por ESLint — exige entender qual fluxo produz o estado,
que é julgamento de domínio. **DELEGADA ao `verifier`**: ao auditar correção de bug, exigir que
(a) o estado que a correção trata seja demonstravelmente alcançável pelo fluxo que gerou o bug, e
(b) exista ao menos uma asserção que falharia se a correção fosse revertida. Ambas as checagens
foram o que reprovou as rodadas 4, 5 e 6 desta spec.

---

### [AG-013] Auditoria por grep não distingue código de comentário — e o comentário que ADVERTE contra a regra dispara o próprio grep

**Contexto**: spec 037. O plan previa guardas por grep para duas proibições absolutas
(`sample_purpose` nunca escrito; criosobrevida nunca comparada com o parâmetro de referência). Os
arquivos documentam essas proibições em comentários de cabeçalho — que é justamente a boa prática
deste projeto.

**O erro**: `grep -rn "sample_purpose" <modulo>` acusa o arquivo **por documentar a proibição**.
Aconteceu duas vezes na mesma spec: antes disso, o grep de imports proibidos num helper puro casou
com o comentário que dizia quais imports eram proibidos.

**Por que é grave, e não só chato**: o resultado é ambíguo nos dois sentidos. Um auditor apressado
lê "1 ocorrência" e reprova código correto; ou, pior, acostuma-se a ver ocorrências "que são só
comentário" e deixa passar a ocorrência real no meio delas. A guarda deixa de guardar.

**Regra correta**: todo grep de auditoria filtra linhas de comentário.

```bash
grep -rnE "<padrão>" <caminho> | grep -vE ':[0-9]+: *(//|\*|/\*)'
```

E, quando o que se audita é **semântico** e não textual, o grep textual não serve de guarda
nenhuma: para permissão de rota, audite `accessControl([...])` e não a string do nome da permissão
— na spec 037, `grep donors_update` acusava dois comentários que advertiam contra usá-la, enquanto
o `grep accessControl` mostrava as 7 rotas usando os nomes certos.

**Relação com a [BE-001]**: aquela lesson diz que o comentário não deve citar literalmente o token
que o hook procura — é o mesmo fenômeno visto do lado de quem escreve. Esta é o lado de quem
audita, e as duas juntas fecham o problema: se o token PRECISA aparecer no comentário (porque o
comentário existe para advertir), então é o grep que tem de ser preciso.

**Promovível**: sim — **delegar ao `verifier`**, que já executa auditorias por grep; o filtro de
comentários vira parte do procedimento padrão dele. O caso semântico (permissão, e outros em que o
token aparece em contexto diferente do auditado) **permanece aqui**: exige julgamento sobre o que
realmente prova a regra.

---

### [AG-012] `verify.sh | tail` reporta o exit code do `tail` — gate reprovado vira "aprovado"

**Contexto**: spec 057, ao rodar o gate de conclusão do backend.

**Erro cometido**: rodar o gate como

```bash
bash .claude/scripts/verify.sh backend src/modules/users/users | tail -25
```

e tratar o `exit code 0` reportado como aprovação. Aconteceu **duas vezes seguidas**, e nas duas
o gate estava de fato **reprovado** (`❌ backend: eslint`, `❌ backend: typecheck`).

**Causa raiz**: em pipeline, o `$?` do shell é o da **última** etapa. `tail` sai 0 praticamente
sempre — inclusive quando o comando à esquerda falhou. O `set -u` do `verify.sh` e o seu
`exit != 0` não chegam a ser observados. Pior: em execução longa em background, a saída do
pipe pode chegar vazia, e aí não há nem o texto `GATE REPROVADO` para contradizer o exit code.

**Regra correta**: **nunca** encanar o gate para `tail`/`head`/`grep` quando o objetivo é decidir
se ele passou. Redirecionar para arquivo e capturar o `$?` do próprio script:

```bash
bash .claude/scripts/verify.sh backend <modulo> > /tmp/gate.log 2>&1; echo "EXIT=$?"
sed -n '/RESUMO DO GATE/,$p' /tmp/gate.log
```

Se por algum motivo o pipe for inevitável, ler `${PIPESTATUS[0]}` — nunca `$?`.

**Sinal de alerta**: um gate que costuma levar minutos "passar" em segundos, ou terminar com
arquivo de saída vazio. Gate silencioso não é gate verde — o `verify.sh` **sempre** imprime as
linhas `▶ <etapa>` e o bloco `RESUMO DO GATE`. Ausência do resumo = você não viu o resultado.

**Vale igualmente** para `yarn test`, `tsc --noEmit` e `eslint` rodados à mão para decidir
conclusão de task.

**Automatizável?**: parcialmente. Um hook não vê como o comando foi encanado, mas a regra é
mecânica e verificável na revisão: **exigir que a evidência de gate colada no `tasks.md` contenha
o bloco `RESUMO DO GATE`**, não apenas um "exit 0". **DELEGADA ao `verifier`**: recusar task
marcada `[x]` cujo gate não tenha o resumo textual como prova.

---

### [AG-014] Gerador que casa assinatura em linha única falha em silêncio depois do prettier

**Contexto**: spec 054 (2026-08-18), ao acrescentar `createWithItems` aos 6 repositórios
de bloco por script.

**Erro cometido**: o script fazia `s.replace("  create(data: ICreateXDTO): Promise<X>", ...)`.
A assinatura tinha sido escrita assim, mas um `eslint --fix` anterior já a havia
reformatado em várias linhas:

```typescript
  create(
    data: ICreatePatientCollectionMotilityBlockDTO,
  ): Promise<PatientCollectionMotilityBlock>
```

O `replace` não casou nada. **O script imprimiu "atualizado" para os 6 módulos e não
alterou nenhum** — `str.replace` sem match não é erro, devolve a string intacta. Só o
`tsc` acusou, com 12 erros de "incorrectly implements interface".

**Regra correta**:

1. Ancorar em **marcador estável e curto** — `'  public async save('`, `'export default'` —
   e inserir por índice (`s[:i] + novo + s[i:]`), em vez de casar a assinatura inteira.
2. **Todo `replace` de gerador precisa verificar que casou**: `assert old in s` antes,
   ou comparar `s != original` depois. Sem isso o script mente sobre o que fez.
3. Rodar o gerador **antes** do `eslint --fix`, não depois — ou aceitar que o formato
   já não é o que você escreveu.

**Por que é pior que um erro comum**: o script reporta sucesso. Sem o typecheck no fim,
o defeito chega ao commit com 6 arquivos silenciosamente incompletos.

**Automatizável?**: parcialmente — o `assert`/verificação de match é disciplina de quem
escreve o gerador. O que **vale sempre** é rodar `tsc --noEmit` logo após qualquer
geração em lote, antes de marcar a task.

---

### [AG-015] Mock com aparência de dado real mascara o defeito que o teste deveria pegar

**Contexto**: spec 054 (2026-08-18). O teste do laudo FR08 usava
`double_checked_by_users_id: 'user-conferente'` e asseria
`expect(vars.double_checked_by).toBe('user-conferente')`.

O teste **passava** e provava a coisa certa pela metade: que o dado vinha da coluna certa
(origem). Era cego ao que importava tanto quanto — que o valor impresso no laudo é um **UUID**,
não um nome. `'user-conferente'` parece um nome, então a asserção não tinha como falhar.

**Por que é insidioso**: o mock foi escrito para ser legível. Um valor "bonitinho" no fixture
faz o teste descrever um mundo que não existe — em produção aquela coluna guarda
`request.user.id`.

**Regra correta**: o fixture precisa ter o **formato real** do dado de produção.

- Coluna que guarda UUID → mock com UUID de verdade (`'3f2c8a10-9ab1-4c7e-8f21-6b0d5e4a1c93'`).
- E, quando o formato É a regra, asserir o formato:
  ```typescript
  expect(vars.double_checked_by).not.toMatch(
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
  )
  ```

**Pergunta de revisão**: *este teste passaria com o bug presente?* Se a resposta for "sim,
porque o mock não se parece com o dado real", o teste é decorativo.

**Automatizável?**: não — exige saber o que a coluna guarda de fato.
**Delegada ao `verifier`**: ao auditar spec que cobre formato/apresentação de dado, conferir se
o fixture tem o formato de produção.

---

### [AG-016] Correção de achado de auditoria é código novo — e chega sem auditoria

**Contexto**: spec 054 (2026-08-18). A 1ª auditoria devolveu 6 achados. As 6 correções foram
feitas, os gates passaram, e a 2ª auditoria encontrou **2 defeitos ALTA introduzidos pelas
próprias correções** (BE-024 e BE-025 acima) — ambos do mesmo tipo que o `verifier` já vinha
apontando: caminho que nunca é percorrido, artefato errado em produção.

**A armadilha**: corrigir sob pressão de "fechar o gate" faz tratar a correção como conserto
pontual, não como código novo. Mas ela é código novo — nasce sem teste, sem revisão e sem o
cuidado que o código original teve, e ainda por cima em cima de um sistema que o autor acabou
de reler apressado.

**Regra correta**: toda correção de achado passa pelo mesmo crivo do código original.

1. Escrever o teste que **falha** com o defeito presente, ANTES de corrigir.
2. Perguntar de cada correção: *qual caminho de produção percorre esta linha?* (é a AG-011)
3. Reauditar **sempre** depois de corrigir — nunca marcar `[x]` com base na própria correção.
4. Ao criar rota/service para tornar algo "alcançável", conferir que ficou mesmo alcançável:
   a correção do `files_id` da spec 054 criou uma rota que retornava 400 em 100% das chamadas.

**Automatizável?**: não. **Delegada ao processo**: o `/finish-task` só aceita parecer de
auditoria posterior à última alteração de código.

---

### [AG-017] "Removi X" conferido por grep do texto NOVO — o texto velho sobrevive

**Contexto**: spec 043 (2026-08-20), duas vezes na mesma sessão; **spec 067 (2026-08-23/24), mais
três vezes na mesma feature** — a lesson já existia e foi cometida assim mesmo, o que diz algo
sobre confiar no texto para evitá-la.

1. Relatei "`VAZIO` removido do filtro de situação". O select da UI foi limpo; o Joi continuou com
   `...Object.values(StorageStockStatus)`, que inclui `VAZIO`. A auditoria pegou: com
   `search_status=VAZIO` nenhum filtro era aplicado, a rota devolvia tudo e o cabeçalho do PDF
   ainda estampava "situação: VAZIO" — recorte afirmado que não houve.
2. Relatei "corrigi a frase que dizia que em `OCULTO` os campos de conteúdo vêm nulos". O bloco
   novo entrou 40 linhas abaixo; a frase antiga permaneceu, passando a **contradizer** o bloco
   novo. Quem parasse na primeira escreveria `rack.reeds_quantity ?? '—'`, que não trata o caso.

**A causa é sempre a mesma**: para confirmar uma remoção, foi feito `grep` do **texto que
substitui** — que existe, porque acabou de ser escrito. O grep passa, a conclusão é "removido", e
o texto velho continua no arquivo. É a AG-013 aplicada a si mesma: **grep confirma presença, nunca
ausência.**

**Por que é insidioso**: adicionar e remover parecem um ato só na cabeça de quem edita ("troquei
X por Y"), mas são dois. Quando a edição é feita por `replace` de bloco, os dois acontecem juntos;
quando é feita acrescentando o novo e *pretendendo* apagar o velho, só o primeiro acontece — e a
verificação natural (procurar o novo) não distingue os dois casos.

**A remoção tem CASCATA, e o grep para na fronteira do módulo** (spec 067, 2026-08-24). Ao
remover um botão de um componente, a limpeza seguiu certa dentro do arquivo — bloco JSX, props da
interface, destructure, imports — e **parou ali**. O hook que *produzia* o dado (`hasFailure`)
continuou exportando o campo com um JSDoc dizendo "a trilha mostra o botão de tentar de novo".
Ficaram: um campo sem nenhum consumidor, a maquinaria que só existia para calculá-lo, e um
comentário falso no lugar mais caro — o contrato que o próximo dev lê antes de decidir se pode
mexer. Nem ESLint nem `tsc` pegam propriedade de objeto que ninguém lê.

**Regra correta**: afirmação de remoção verifica-se por **ausência do termo removido**, o grep tem
de ser pelo termo VELHO, e o escopo do grep é **o workspace, não o arquivo editado**. Quem consome
o que você removeu pode estar em qualquer lugar; quem *produz* o que só existia para ele, também.

```bash
# ❌ confirma que o novo existe — não diz nada sobre o velho
grep -n "StorageStockStatus.ATIVO, StorageStockStatus.BLOQUEADO" rotas.ts

# ✅ confirma a remoção
grep -n "Object.values(StorageStockStatus)" rotas.ts && echo "AINDA PRESENTE" || echo "removido"
```

Vale para: valor tirado de enum/lista, campo tirado de DTO, método tirado de contrato, frase
corrigida em comentário, import removido. E como o termo velho costuma sobreviver legitimamente
**dentro do comentário que explica por que ele saiu**, a leitura do resultado exige AG-013 —
conferir se o hit é código ou prosa antes de concluir.

**Pergunta de revisão**: *qual comando eu rodaria para provar que X NÃO está mais lá?* Se a
resposta for "rodei o grep do que entrou no lugar", não está provado.

**Automatizável?**: **não como hook pós-edição** — confirmado em 2026-08-24 lendo o
`post-edit-check.sh`: ele recebe apenas `tool_input.file_path`, sem diff e sem conteúdo anterior.
Não há como saber o que saiu.

**PROMOVIDA para o template de tasks** (mesma estratégia da BE-007: o hook audita a saída, o
template molda a entrada). `_templates/tasks.md` passa a exigir, em toda feature que REMOVE um
mecanismo, uma task dedicada cuja verificação é o grep do termo VELHO no workspace inteiro.

**Delegada ao `verifier`**: tratar "removi X" como não verificado até grep por X — e conferir se a
cascata atravessou a fronteira do módulo (consumidores E produtores).

---

### [AG-018] O filtro de comentários da AG-013 não cobre comentário JSX — e num `.tsx` isso dá falso "limpo"

**Contexto**: spec 068 (2026-08-24), task de conferência de remoção. A AG-013 prescreve filtrar
linhas de comentário antes de julgar um grep de auditoria:

```bash
grep -rnE "<padrão>" <caminho> | grep -vE ':[0-9]+: *(//|\*|/\*)'
```

O filtro casa linha cujo conteúdo **começa** com `//`, `*` ou `/*`. Comentário JSX não começa com
nada disso: o corpo dele são linhas de prosa cruas dentro de `{/* … */}`.

```tsx
{/*
  ⚠️ NÃO HÁ MAIS BOTÃO "ATUALIZAR" AQUI. Ele era exibido quando
  `hasFailure` — alguma das chamadas da trilha tinha falhado — e servia
  ...
*/}
```

**O que aconteceu**: os cinco greps de remoção voltaram limpos, exceto um hit nessa linha do
`DonorCollectionProgressTrail`. Como o filtro tinha "funcionado" nos outros arquivos, a tentação era
ler o hit como ruído do mesmo tipo. Não era: o comentário mandava procurar `hasFailure` no hook, e
`hasFailure` tinha sido apagado na task anterior — exatamente o defeito que a AG-017 chama de "o
comentário falso no lugar mais caro".

**Por que é insidioso**: o falso negativo é silencioso e assimétrico. Em `.ts` o filtro funciona; em
`.tsx` ele deixa passar justamente a prosa mais longa e mais explicativa do arquivo — a que o
próximo dev lê antes de decidir se pode mexer. E o resultado *parece* mais limpo, não mais sujo.

**Regra correta**: em arquivo `.tsx`, o filtro de comentário **não substitui a leitura**. Trate cada
hit sobrevivente como "a classificar por leitura", nunca como "provavelmente comentário". Se quiser
um filtro que ajude sem enganar, filtre apenas o que é seguramente código:

```bash
# ❌ em .tsx, dá falso "limpo" — a prosa de {/* … */} escapa
grep -rnE "hasFailure" src | grep -vE ':[0-9]+: *(//|\*|/\*)'

# ✅ separa em dois baldes e obriga a olhar o segundo
grep -rnE "hasFailure" src | grep -E ':[0-9]+: *[A-Za-z_{(<]' # candidatos a código
grep -rnE "hasFailure" src                                     # tudo — ler o resto
```

**Relação com a [AG-013]**: aquela lesson diz "todo grep de auditoria filtra comentário". Esta
delimita até onde o filtro dela vale. As duas juntas: **o filtro reduz o volume, não decide** — e em
`.tsx` reduz menos do que parece.

**Automatizável?**: **não**. Distinguir "comentário que explica a remoção" (legítimo) de "comentário
que afirma o mecanismo como vigente" (defeito) é julgamento sobre o sentido da frase, não sobre a
sintaxe. Nenhum padrão de grep decide isso.

**Delegada ao `verifier`**: ao auditar remoção em workspace de frontend, não aceitar grep filtrado
como prova de ausência em arquivos `.tsx` — ler os hits.

---

### [AG-019] Gate vermelho que acusa o AMBIENTE não é gate reprovado — é gate que não rodou

**Contexto**: spec 069 (2026-08-25), reconfirmação dos gates antes do `/finish-task`.

**Erro evitado por pouco**: rodar

```bash
bash .claude/scripts/verify.sh frontend
```

a partir do shell do **Windows**, sobre o caminho UNC do WSL (`\\wsl.localhost\...`), e receber:

```
❌ frontend: eslint
⚠️ frontend: typecheck PULADO
❌ GATE REPROVADO — a task NÃO pode ser concluída. Corrija e rode novamente.
```

O impulso natural diante disso é abrir o código e procurar o que quebrou. Não havia nada quebrado:
dentro do WSL o mesmo gate passa **4/4**.

**Causa raiz**: o `yarn` invoca `cmd.exe`, que não suporta caminho UNC. Ele **avisa** e troca o
diretório corrente por `C:\Windows`:

```
CMD.EXE foi iniciado tendo o caminho acima como pasta atual.
Não há suporte para caminhos UNC. Padronizando para pasta do Windows.
'eslint' não é reconhecido como um comando interno ou externo
```

Fora do workspace, o `eslint` do `node_modules` local não existe. O `verify.sh` fez o certo — leu
um comando que falhou e reprovou. O veredito é verdadeiro sobre a execução e **falso sobre o
código**.

**O que torna isso perigoso**: o resumo do gate é *idêntico* ao de uma reprovação legítima. Ele
traz o bloco `RESUMO DO GATE` que a [AG-012] ensina a exigir como prova — ou seja, passa no teste
de "o gate chegou a imprimir o resumo" e ainda assim não avaliou uma linha de código. E o
`⚠️ typecheck PULADO` na linha seguinte reforça a leitura errada, sugerindo ambiente meio
quebrado em vez de comando que nunca entrou no diretório certo.

**Regra correta**: antes de tratar um gate vermelho como veredito sobre o código, ler **o texto do
erro**, não só o símbolo. Se ele fala de *binário não encontrado*, *caminho padronizado*,
*conexão recusada*, *permissão negada* ou *módulo ausente*, o gate **não rodou** — corrigir a
invocação e repetir. Só depois de o gate executar de fato é que vermelho vira defeito a corrigir.

Neste monorepo, sobre caminho UNC, atravessar para dentro do WSL:

```bash
wsl.exe -d Ubuntu-24.04 -- bash -lc 'cd /home/eadconcept/www/vidafertil && bash .claude/scripts/verify.sh frontend; echo "EXIT=$?"'
```

**Dois corolários da mesma sessão**:

- **`exit 127` com `Wsl/Service/0x8007274c` é a ponte `wsl.exe` caindo — não é teste vermelho, e
  não é contenção.** A primeira leitura desta sessão culpou o paralelismo (três `wsl.exe` pesados
  ao mesmo tempo). **Falsificada minutos depois**: um `wsl.exe -d Ubuntu-24.04 -- bash -lc 'echo
  ALIVE'`, sozinho, com nada mais rodando, devolveu o mesmo 127. Rodar em série é boa prática por
  outros motivos, mas **não previne isto**.
  O diagnóstico que separa os casos: `wsl.exe -l -v` mostra a distro `Running` e o
  compartilhamento `\\wsl.localhost\...` continua legível — ou seja, a distro está viva e só o
  canal de execução morreu. Recuperação: `wsl.exe --terminate <distro>` (reinicia só ela;
  `--shutdown` derruba também `docker-desktop`). ⚠️ Qualquer uma das duas **mata o que estiver
  rodando dentro do WSL** — dev server, banco. Pedir ao usuário antes.
- **`mv` de pasta dentro do compartilhamento UNC falha com `Device or resource busy`.** Usar
  `cp -p` + `diff` + `rm`, nessa ordem: a conferência da cópia **antes** de remover a origem. Um
  `mv` que falha deixa tudo no lugar; um `cp` não conferido seguido de `rm` perde o arquivo.

**Relação com a [AG-012]**: aquela lesson diz *"o número que você leu pode não ser o do gate"*
(o `$?` era do `tail`). Esta diz *"o gate pode ter rodado e mesmo assim não ter avaliado o
código"*. As duas são a mesma família: **tomar por veredito sobre o código um resultado que veio
de outro lugar** — ali do encanamento, aqui do ambiente. Juntas: exigir o `RESUMO DO GATE`
(AG-012) **e** confirmar que as etapas do resumo falharam por motivo de código (AG-019).

**Automatizável?**: **parcialmente**. O `verify.sh` poderia abortar cedo com mensagem própria ao
detectar que o binário esperado não está no `node_modules` local, distinguindo mecanicamente
"ambiente errado" de "código errado" — hoje ele reprova igual nos dois casos. Fica registrado
como melhoria candidata do script. A leitura do texto de erro em si é julgamento.
**→ Realizada na spec 084 (11/09/2026)**: `verify.sh` v2.0 sai com **exit 65 `TOOLCHAIN AUSENTE`**
e grava a lista em `missing` na evidência; o `verifier` lê `rc`/`missing` em vez do texto do erro.

**DELEGADA ao `verifier`**: ao conferir evidência de gate no `tasks.md`, não aceitar como
reprovação — nem como aprovação — resumo cujas etapas falharam por erro de ambiente. Exigir a
reexecução no ambiente correto.

---

## AG-020 — Valide o detector contra um caso CONHECIDO antes de anunciar varredura

**O erro, cometido TRÊS VEZES na spec 069, na mesma sessão**:

1. Classifiquei uma tela como quebrada pelo NOME e pela ASSINATURA da função, sem ler o corpo.
2. Anunciei "24 cláusulas sem guarda em 8 repositórios" — e o usuário **autorizou corrigir os
   oito**. Era falso alarme: o regex não reconhecia a guarda ternária (`x ? 'col ILIKE :p' : '1=1'`)
   e ainda varria 240 caracteres à frente, atravessando para outra cláusula.
3. Refiz e reportei "2 sem guarda". Também falso: as duas tinham `if (x)` imediatamente antes.

O número certo era **zero** — só um repositório tinha o defeito, e a prova dele nunca foi de
padrão: foi medição contra o banco.

⚠️ **A raiz NÃO é "regex ruim".** É ter anunciado um achado sistêmico **sem validar o detector**.
Um detector que devolve `0` pode significar duas coisas opostas — "não há defeito" ou "não sei
detectar" — e nada na saída as distingue.

**Regra — a pergunta da AG-011, aplicada à FERRAMENTA:**

> Se eu apontar meu detector para o defeito que EU JÁ SEI que existe, ele acusa?

Se **não acusa**, o `0` não vale nada. Se **acusa**, o `0` é medição.

O caso conhecido quase sempre está à mão: é o defeito que originou a varredura. Quando ele já foi
corrigido, `git show HEAD:<arquivo>` devolve a versão com o defeito — e foi assim que o `verifier`
validou o classificador dele nesta mesma spec, encontrando as duas cláusulas do `UserRepository`
pré-correção. **Custa um comando.**

**Corolários:**

- **Anunciar escala é diferente de anunciar um caso.** "Achei um defeito aqui" custa uma correção;
  "achei em 8 módulos" custa a decisão do usuário sobre escopo — e ele decide com o SEU número.
- **Ao varrer, leia alguns acertos e alguns não-acertos à mão.** Se o idioma dominante do repositório
  não aparece na sua amostra, o detector não conhece o repositório.
- **Registre o motivo CERTO de cada não-acerto.** Nesta spec eu registrei que um arquivo era seguro
  por "não ter campo `type="number"`" — tinha, num componente filho; ele é seguro por outro
  mecanismo. Motivo errado registrado é armadilha para quem vier depois.

**Automatizável?** **Não** — é disciplina de método, não padrão de texto. **Delegado ao `verifier`**:
diante de qualquer achado que afirme escala ("N ocorrências em M arquivos"), exigir a validação do
detector contra um caso conhecido antes de aceitar o número.

---

## AG-021 — Gate rodado em background com `&` não é gate

**Erro real (spec 074, 2026-09-01)**: a suíte do backend foi disparada duas vezes com
`nohup ./node_modules/.bin/jest --silent > saida.txt 2>&1 &`. As duas vezes o harness
reportou **exit 0** e o `tail` da saída mostrou só linhas `PASS` — e as duas vezes a
Fase 6 foi dada como aprovada em cima disso.

Nenhuma das duas execuções tinha terminado. O `exit 0` era do **wrapper** (`nohup … & echo`),
não do jest; o arquivo tinha 38 linhas e **nenhuma linha `Test Suites:`**; e os dois jest
continuavam vivos, disputando CPU um com o outro. Rodada em primeiro plano, a mesma suíte
devolveu `1 failed, 707 passed` — um teste que o modelo novo tinha tornado obsoleto.

**Regra**: um gate só conta quando:
1. rodou em **primeiro plano** (ou o exit code lido é o do processo, não o do disparo); **e**
2. a saída tem a **linha de resumo** (`Test Suites: … total`) — é ela que prova que a
   execução chegou ao fim; **e**
3. o `FAIL` foi contado no arquivo inteiro, não no `tail`.

`tail` de saída de jest é enganoso por construção: as últimas linhas escritas são sempre
`PASS`, porque as falhas já rolaram para cima.

**Antes de disparar**, conferir que não há execução anterior viva (`pgrep -f "bin/jest"`) —
duas suítes concorrentes deixam as duas lentas e nenhuma confiável.

**Promovível?** Parcialmente. A checagem "a saída tem linha de resumo e zero `FAIL`" cabe
num script de gate; o `verify.sh` já roda em primeiro plano. O que fica de julgamento é a
disciplina de não aceitar `tail` como prova.

---

## AG-022 — Tipo do frontend NÃO é conferido contra o que o backend responde

**Erro real (spec 074, 2026-09-01)**: o `T-RM-FE` encontrou duas interfaces do
frontend descrevendo respostas que o backend tinha deixado de mandar:

- `IDonorFreezingTestReserve` declarava `test_units_quantity`,
  `test_units_consumed`, `test_units_remaining` e `warning`. O service do backend
  passara a responder `has_test_batch`, `test_units_total`, `test_units_in_stock`,
  `test_units_used` — e **nenhum `warning`**. Sintoma: o aviso da RN-02 no modal
  de descongelamento nunca aparecia, porque `testReserve.warning` era `undefined`.
- `storage-reports.types.ts` declarava `storage_stock_id` em três interfaces; o
  backend renomeara o campo para `rack_key`.

**Nos dois casos o `tsc` do frontend estava LIMPO**, o ESLint também, e os testes
de componente mockam o service — nada podia pegar. A interface é uma AFIRMAÇÃO
sobre a resposta, e afirmação não é verificação.

**Regra**: ao mudar a forma de uma resposta no backend — renomear campo, trocar o
conjunto de campos, mudar a chave do `response.json` —, **abrir o tipo
correspondente no frontend na mesma passada**. E ao auditar remoção (AG-017),
comparar campo a campo o DTO do backend com a interface do frontend, não só
procurar o termo velho: o defeito (2) só apareceu porque o termo velho estava
lá; o defeito (1) precisou de comparação, porque os nomes novos não eram
pesquisáveis a partir dos antigos.

**Sinal de alerta**: campo que o backend nunca preenche e a tela nunca mostra não
produz erro nenhum — produz uma funcionalidade que sumiu em silêncio. Foi
exatamente o caso do aviso da RN-02.

**Promovível?** Parcialmente. Um script que compare os campos de um DTO do
backend com os da interface homônima do frontend pegaria o caso (2) e boa parte
do (1). O que fica de julgamento é decidir de que lado a correção vai — no (1) a
frase de aviso voltou para o BACKEND, porque montá-la na tela duplicaria a
redação da regra em dois lugares que ninguém compara.

---

### [AG-023] Relação nova adicionada só no repositório do "dono", não em todo repositório que lê o mesmo agregado por outra porta

> ⚠️ **Era `AG-020` até 12/09/2026** (spec 087): o código estava duplicado com a lição de método
> "valide o detector contra um caso conhecido", que ficou com o número por ser a mais citada
> (`verifier.md`, `lessons/README.md` e 5 registros de execução). Specs antigas que dizem `AG-020`
> e falam de RELAÇÃO referem-se a esta.

**Contexto**: spec 075 (2026-09-03), achado do `verifier`. Múltipla escolha real no questionário
do doador exigiu uma tabela de junção nova (`donors_answers_options`) e uma relação `OneToMany`
nova em `DonorAnswer` (`donoransweroption`).

**Erro cometido**: a relação nova foi adicionada aos `leftJoinAndSelect`/`relations` do
`DonorAnswerRepository` (módulo `donors_answers`) — `findBySubmissionIdWithRelations`,
`findByIdRelations`, `findAllDonorsAnswers`. Mas a tela que de fato lê a resposta ao reabrir uma
submissão (`DonorReview`, revisão da equipe interna) não chama nenhuma rota de `donors_answers` —
chama `GET /donorsubmission/show/:id`, que é servida por `DonorSubmissionRepository` (módulo
**vizinho**, `donors_submissions`), cujo `findByIdRelations` também lista
`'donoranswer.donorquestion'`/`'donoranswer.donorquestionoption'` — uma cópia própria da mesma
lista de relations, desatualizada. Resultado: `getAnswerLabel` no frontend estava correto e o
dado estava gravado certo no banco, mas `answer.donoransweroption` chegava `undefined` por esse
caminho, e a tela sempre mostrava "—" para respostas de múltipla escolha.

**Por que passa despercebido**: `tsc`, ESLint e os testes unitários (que mockam
`IDonorAnswerRepository` diretamente) não têm como alcançar isso — o defeito é de **outro**
repositório, que só existe através de uma chamada HTTP real. É a mesma classe de bug do AG-017
("grep para na fronteira do módulo"), só que do lado da LEITURA em vez da remoção: a relação nova
foi propagada para dentro do módulo que a possui, não para todo lugar que consulta o mesmo
agregado por um caminho diferente.

**Regra correta**: ao adicionar uma relação nova (`OneToMany`/`ManyToOne`) numa entity, `grep` por
`relations:\s*\[` e por `leftJoinAndSelect` no projeto inteiro procurando outras cópias da mesma
lista — não só no repositório do módulo dono da entity. Um agregado consultado por telas
diferentes (aqui: `donors_answers` e `donors_submissions`, servindo a mesma tela de revisão)
tende a ter mais de um lugar que monta a árvore de relations, e cada cópia precisa da mesma
atualização.

**Automatizável?**: parcialmente. Um `grep -rn "donoranswer\." --include="*.ts"` fora do módulo
`donors_answers` teria achado a segunda lista. Fica **delegada ao `verifier`**: ao auditar uma
relação nova, localizar TODO `relations:`/`leftJoinAndSelect` que referencie a entity pai (aqui,
`DonorAnswer`) em qualquer módulo, não só no repositório onde a relação foi declarada.

---

### [AG-024] Renomeação em lote a partir de módulo-molde atropela identificador que não é do domínio [PROMOVIDA → hook (variante a) / verifier (variante b)]

> ⚠️ **Era `AG-021` até 12/09/2026** (spec 088): o código estava duplicado com "Gate rodado em
> background com `&` não é gate", que ficou com o número por ser a mais antiga (spec 074,
> 2026-09-01) e a mais citada (`verifier.md`, `scaffold/README.md`, `HARNESS.md` e 6 registros de
> execução). Specs antigas que dizem `AG-021` e falam de RENOMEAÇÃO referem-se a esta. É o mesmo
> defeito que a 087 corrigiu no `AG-020` → `AG-023`.


**Contexto**: specs 080/081/082 (2026-09-11) — três catálogos de `parameters/` gerados por cópia
do molde `positions` com renomeação por tabela de substituições ordenada.

A renomeação acerta o domínio e continua andando. Duas vítimas reais, ambas invisíveis para
ESLint e `tsc`:

**(a) Chave de opção de biblioteca.** `position: toast.POSITION.TOP_CENTER` virou
`sampletype: toast.POSITION.TOP_CENTER` em 15 pontos. O react-toastify recebe
`Partial<ToastOptions>`: chave desconhecida é **ignorada em silêncio**. O toast aparece, só que
no canto errado, e nada acusa — nem o tipo, porque a chave extra é aceita.

**(b) Nome de tabela no `@Entity`.** `@Entity('sample_types')` virou `@Entity('sampletypes')`,
divergindo da tabela que a migration cria. Compila, linta, e quebra na primeira query.

**Regra**: toda renomeação em lote a partir de módulo-molde precisa de **allowlist de
identificadores que não são do domínio** — chaves de opção de biblioteca, nomes de tabela,
constantes importadas. E o grep anti-vazamento do AG-002 **não pega isto**: ele procura o nome do
molde (`position`), e o defeito é justamente o nome do molde tendo **sumido** de onde devia ficar.
Inverta o grep: depois de renomear, procure o nome NOVO em contexto onde ele não deveria estar.

**Promovível**: parcialmente, e a parte que não é foi medida antes de decidir.

- **(a) → hook**: `post-edit-check.sh` rejeita `<qualquer>: toast.POSITION.` quando o
  identificador não é `position`. Detector validado nos dois sentidos — pega o texto exato do
  defeito, não acusa o texto corrigido, e no repo inteiro dá **0 falso positivo contra 648 usos
  legítimos**.
- **(b) → verifier**, não hook. Os dois detectores óbvios são ruidosos demais para regra
  bloqueante: `@Entity` × nome da pasta acusa **63 de 203 entities (31%)**, porque entity-filha
  mora legitimamente na pasta do pai (`customers_addresses` em `address/`); `@Entity` × tabela
  criada por migration acusa **35 de 203 (17%)**, que são tabelas legadas anteriores ao histórico
  de migrations. Hook que erra 1 em 3 deixa de ser lido — a distinção entre filha legítima e erro
  de renomeação exige contexto, então é do `verifier`.

---

## AG-025 — Edição por `sed`/heredoc não dispara o hook: o gravador escolhe se o harness roda

**Erro real (piloto do harness v2, 2026-09-11/12)**: o `PostToolUse` de `settings.json` tem
matcher `Edit|MultiEdit|Write`. Gravar o mesmo arquivo `.ts` por `sed -i`, `cat > arquivo <<'EOF'`,
`python -c "open(...).write(...)"` ou `tee` **não dispara hook nenhum** — nem o ESLint por arquivo,
nem BE-001, BE-007, BE-016, BE-023, FE-009, FE-024, nem o `protect-migrations.sh`.

**Por que isso acontece justamente em modo automático**: a instrução de "modo automático" da
sessão pede para trabalhar por Bash sempre que Bash resolver — `cat`, `sed`, heredoc. Ela é boa
para ler e para arquivo de texto, e **desastrosa para `.ts/.tsx`**: o agente obedece, o arquivo é
gravado, nada acusa, e a camada mais barata do harness fica desligada sem deixar rastro. Essa
instrução também chega aos **subagentes**.

**O sintoma é a ausência de sintoma.** Não há erro, não há aviso, e o gate seguinte pode até passar:
`verify.sh --scope` roda ESLint e `tsc` sobre o diff, então pega parte — mas as regras de lessons
promovidas vivem **só** no hook, e essas somem inteiras.

**Regra**:

| Arquivo | Como gravar |
|---|---|
| `.ts`, `.tsx` | **`Edit` / `Write`, sempre.** Nunca `sed -i`, heredoc, `tee` ou `python -c` |
| `.md`, `.json`, `.sh`, `.py` do harness | Bash é aceitável (o hook não age neles de qualquer forma) |
| gerado por script (`scaffold.py`) | exceção legítima — o passo seguinte é **reabrir o gerado com `Read`/`Edit`** antes de preencher |

Os três agentes que escrevem código (`backend-builder`, `backend-test-author`,
`frontend-builder`) trazem esta regra em CAIXA ALTA no início do corpo, com a frase que resolve o
conflito: *a instrução de modo automático não vale para `.ts/.tsx`; esta regra vence.*

**Automatizável?**: ⚠️ **SIM — e eu errei ao escrever que não.** O texto original dizia "não pelo
hook, o ponto é exatamente que o hook não é chamado". O que não é chamado é o **`PostToolUse`**; o
**`PreToolUse` de `Bash`** é, e vê o comando antes de ele rodar.

**PROMOVIDA (spec 090) → `.claude/hooks/block-shell-write-ts.py`**, `PreToolUse` matcher `Bash`:
recusa `>`, `>>`, `>|`, `sed -i`, `tee`, `cp`, `mv` com alvo `.ts/.tsx` **dentro dos workspaces**,
resolvendo `cd` em qualquer posição e ignorando corpo de heredoc. Escape declarado para o
`scaffold.py`, como comando executado (mencioná-lo não basta).

**Limites, nomeados no docstring** e todos com medição: não detecta `python -c` com
`open(...,'w')`, `dd of=`, `perl -i`, `xargs`, variável com prefixo do workspace, `cd` em subshell,
`cp` para diretório, nem tag de heredoc com hífen. A regra **reduz** a rota, não a fecha — e os
zeros dizem "ninguém fazia assim", não "ninguém fará": o corpus é anterior ao hook.

**O que o hook NÃO substitui**: `verify.sh` e `check-module.py` continuam sendo a defesa que **lê o
disco** em vez de confiar em quem escreveu. Quem contorna por uma porta declarada faz uma escolha.

---

## AG-026 — Pasta passada ao gate é REGEX de caminho, não prefixo de diretório

**Erro real (spec 062, 2026-09-13, no piloto da 088)**: o `backend-lead` rodou
`verify.sh backend src/modules/donors/donors --scope` e recebeu **rc=1**, por uma suíte de
`donors_freezings` que a spec 074 tornou obsoleta. O diagnóstico dele — "falha pré-existente,
alheia à feature" — estava certo, e foi levado ao usuário como decisão pela regra crítica 7. O
usuário autorizou concluir com exceção registrada.

**A exceção não era necessária.** O argumento de pasta do `verify.sh` vira `jest <pattern>`, e o
pattern do jest é **regex de caminho**. Sem barra final, `src/modules/donors/donors` casa também
`src/modules/donors/donors_freezings/...`, `donors_collections/...`, `donors_reviews/...`:

```
jest --listTests "src/modules/donors/donors"    → 282 suítes
jest --listTests "src/modules/donors/donors/"   →  12 suítes
```

Uma barra final. Com ela, `rc=0` — o teste obsoleto nunca pertenceu ao escopo da feature.

**Escala, medida antes de afirmar (AG-020)**: dos 176 módulos, **15 são vítimas reais** — o gate
sem barra varre suítes de outro módulo. Os piores: `donors` (12 → 282), `patients` (9 → 77),
`donors_collections` (13 → 72), `donors_freezings` (29 → 59), `laboratories` (6 → 36).

⚠️ **O detector óbvio erra.** "Nome que é prefixo de um irmão" dá **22** módulos — e `companies`
está entre eles sem ser vítima: `companies_bank_details` e irmãos **não têm `.spec.ts`**, então
os dois patterns casam a mesma coisa. Não-caso conferido: `clinics` → 13 e 13, idêntico. O que
importa não é o nome ser prefixo, é **existir suíte no irmão**.

**Regra**: pasta passada ao gate (ou a qualquer `jest`/`eslint` que receba pattern) termina em
**`/`**. Sem ela, você não está rodando o escopo do módulo — está rodando o de todos os módulos
cujo nome começa igual, e um teste vermelho de qualquer um deles reprova a sua feature.

**A consequência que dói mais**: o vermelho alheio é **convincente**. Ele vem com nome de arquivo,
nome de teste e uma spec anterior a quem culpar — e o caminho natural é registrar a exceção, gastar
uma decisão do usuário e deixar dívida para outra feature. Antes de declarar "falha pré-existente,
alheia ao escopo", **confira se o escopo é o que você pensa que é**: `jest --listTests <pattern>`
com e sem a barra, e compare a contagem.

**Automatizável?**: sim, e **PROMOVIDA (spec 090) → `verify.sh`**, nas duas formas previstas: o
argumento de pasta é **normalizado** com `/` final — inclusive caminho absoluto — e o resumo
**declara** que normalizou; o step passou a carregar **quantas suítes** o pattern casou, o que
torna o desvio visível sem ninguém procurar.

**Limite**: a normalização só alcança pasta que **existe** como diretório. `donors/donorss/`
(inexistente) segue passando com 0 suítes e `--passWithNoTests` — e isso pertence a outro achado,
aberto: **54 dos 176 módulos não têm suíte nenhuma**, então um escopo verde pode não ter rodado
nada. Está registrado no `HARNESS.md` para virar spec própria.

---

## AG-027 — `--scope` sobre workspace limpo: diff vazio, gate verde, nada verificado

**Erro real (spec 092, 2026-09-14)**: no `/finish-task`, com o código já commitado pelo usuário, o
`--check-evidence` acusou `desatualizada` nos dois workspaces. O reflexo é rodar
`verify.sh <ws> --feature <f>` de novo — que é `--scope` por padrão, e `--scope` é
`git diff HEAD` + untracked. **Com o workspace limpo esse diff é vazio**: o hash calculado foi
`e3b0c44298fc`, que é o sha256 da string vazia. ESLint receberia 0 arquivos, `jest --findRelatedTests`
receberia 0 arquivos, e só o `tsc` avaliaria algo. O gate ficaria **verde sem ter verificado a
entrega**.

**Por que é grave, e não apenas inútil**: a evidência gravada não distingue as duas coisas. Um
`rc: 0` com `steps` todos `ok` sobre diff vazio é byte a byte tão convincente quanto um sobre a
feature inteira — e o `--check-evidence` de quem vier depois devolve `válida`. O verde não mente
sobre o que rodou; ele silencia sobre o que **não** rodou.

**É a explicação mais provável de um defeito que ficou 2 semanas invisível**: o teste
`donors_freezings/tests/donorDonatableAvailability.spec.ts` quebrou quando a **spec 074** reescreveu
`donorDonatableAvailability.ts` (commit `a96be04`, 31/08) sem atualizar o spec que afirma o conteúdo
do SQL. O `--findRelatedTests` **teria** encontrado esse spec, porque ele importa o helper — desde
que o helper estivesse no diff. Se o gate rodou depois do commit, não estava.

**Regra**: antes de ler um gate `--scope` como aprovação, **olhe quantos arquivos ele processou**. O
resumo do `verify.sh` diz (`eslint (N arquivo(s) do diff)`). `N = 0` não é aprovação — é ausência de
medição. Quando o alvo já está commitado, use `--since <ref anterior>` para reconstituir o diff, ou
`--full`. Ver [[AG-028]], que é a regra operacional que decorre desta.

**Automatizável?**: **sim, e vale a pena.** O `verify.sh` já conhece o tamanho da lista: basta
recusar (ou marcar a evidência como não-conclusiva) quando o modo é `scope` e o conjunto de arquivos
é vazio, em vez de gravar um `rc: 0` indistinguível. Enquanto não for promovida, a defesa é humana e
frágil — é preciso *lembrar* de conferir o `N`.

---

## AG-028 — Fechamento de feature roda `--full`, nunca `--scope`

**Erro real (spec 092, 2026-09-14)**: corolário do [[AG-027]], mas com uma lição própria, porque o
`--full` não só evita o vazio — ele **encontra o que o `--scope` é incapaz de ver por construção**.

No fechamento da 092 o `--full` reprovou duas vezes, e **nenhuma das duas** por causa da feature:

| O que reprovou | Idade | Por que o `--scope` não via |
|---|---|---|
| `donorDonatableAvailability.spec.ts` afirmando `vials_quantity`/`packaging_type`, removidos pela spec 074 | 14 dias | `donors_freezings` nunca entrou no diff de uma feature de `storage` |
| `Header/index.tsx` lendo `.name` sem estreitar a união `MenuEntry` | ~2 minutos | refatoração de outra sessão, fora do diff da feature — ver [[AG-029]] |

**A assimetria que importa**: `--scope` é o gate certo **durante** a execução, quando o diff É a
entrega e o ciclo precisa ser rápido. No **fechamento** o diff deixou de descrever a entrega (ou
está vazio, ou foi commitado junto com trabalho alheio), e o que se quer provar mudou de "o que
escrevi está são" para "**o repositório está são com o que escrevi dentro**". São perguntas
diferentes; só a segunda encerra uma feature.

**Regra**: no `/finish-task`, rodar `verify.sh <ws> --full --feature <f>` nos workspaces tocados.
Se o `--full` reprovar por defeito **alheio e anterior**, não contornar com um gate mais fraco:
provar a anterioridade (`git log` do arquivo × commit da feature), reportar ao usuário e **pedir
orientação** — corrigir código fora do escopo é decisão dele, não do executor.

⚠️ **Não adianta "tentar o `--scope` para ver se passa"**: desde a spec 090 a evidência guarda o
**pior** `rc` de todas as rodadas do mesmo `diff_hash`. Um vermelho já gravado não é apagado por um
verde posterior no mesmo diff. A proteção funciona — e é ela que transforma "rodar de novo até
passar" em erro detectável.

**Automatizável?**: **sim, parcialmente** — o passo 2 do `.claude/commands/finish-task.md` já manda
reconferir a evidência; falta ele dizer `--full` em vez de repetir o comando da task, que é
`--scope`. É mudança de uma linha no comando, e fecha o caminho que esta sessão percorreu por
tentativa.

---

## AG-029 — Duas sessões no mesmo workspace: o gate lê arquivo a meio de edição

**Erro real (spec 092, 2026-09-14)**: o `tsc --noEmit` do gate do frontend reprovou com
`src/components/Header/index.tsx(246,53): Property 'name' does not exist on type 'MenuEntry'`.
Ao investigar, o arquivo tinha **216 linhas** — o erro apontava a linha 246 de uma versão que já não
existia no disco. Os `mtime` explicaram: outra sessão Claude estava refatorando o menu lateral
naquele minuto (`types.ts` 14:32:01, `menuItens.ts` 14:32:48, `Header/index.tsx` 14:33:51), e o gate
rodou às 14:33:5x. O `menuItens.tsx` antigo ainda coexistia com o `.ts` novo.

**Por que é insidioso**: o erro é **verdadeiro** — aquele estado intermediário realmente não
compilava — mas não é atribuível a ninguém e não é reproduzível. Diagnosticá-lo como defeito da
própria feature leva a "corrigir" código alheio no meio da edição de outra sessão; diagnosticá-lo
como flake leva a reexecutar até passar, que é o hábito que o [[AG-028]] proíbe. O sinal que
distingue é barato: **o número da linha não existe no arquivo**.

**Regra**: gate que reprova em arquivo que a feature não tocou pede três medições, nesta ordem —
(1) `git log --oneline -2 -- <arquivo>` e `git show --stat <commit da feature> | grep <arquivo>`,
para estabelecer anterioridade; (2) `wc -l` contra a linha acusada, para detectar leitura de estado
intermediário; (3) `ls -la --time-style` na pasta, comparando `mtime` com o horário do gate. Se for
sessão concorrente: **não mexer no trabalho dela e não pedir que pare** — reportar ao usuário, que é
quem sabe o que está aberto nas outras janelas, e re-rodar quando estabilizar.

**Distinto do [[AG-021]]**, que é sobre gate disparado em background com `&` pela *mesma* sessão.
Aqui a sessão fez tudo certo: o gate rodou em primeiro plano, com exit code lido direto. O que
mudou embaixo dela foi o **disco**.

**Automatizável?**: **não com confiança.** Um `git stash` defensivo mexeria em trabalho alheio, e
comparar `mtime` com o início do gate produziria falso positivo em toda feature que edita e verifica
em seguida — que é o caso normal. O que **é** promovível é a regra de leitura: quando o `tsc` acusa
uma linha que não existe no arquivo, o relatório do gate poderia dizê-lo. Fica com o julgamento
humano, e com o registro de que o AG-021 original — "nunca duas features ao mesmo tempo no mesmo
workspace" — tem uma consequência mais concreta do que disputa de CPU.

## AG-030 — `.gitignore` sem âncora ignora em qualquer profundidade — e nenhum gate olha o que o git rastreia

**Erro real (spec 001 da plataforma de pagamentos, 2026-10-24)**: na preparação do commit inicial
da raiz, `git status --short -uall` listava **98** arquivos onde deveria haver **183**. O
`.gitignore` tinha `backend/` e `frontend/` (herdados do ERP) e `tools/` (acrescentado na própria
001) **sem a barra inicial**. Padrão de diretório sem `/` no começo casa em **qualquer
profundidade**: ficavam fora do commit os templates do scaffold (`.claude/scaffold/templates/backend/`
e `frontend/`) e as fixtures dos hooks financeiros (`.claude/scripts/tests/<hook>/backend/api/…`).
`git check-ignore -v` confirmou 4 de 4.

**Por que é insidioso**: tudo funciona **localmente** — os arquivos existem no disco, o gate do
harness rodou verde 14 etapas, três rodadas de `verifier` aprovaram. O defeito só aparece em outro
clone, onde o `scaffold.py` não acha template e os self-tests dos hooks não acham fixture. E a
intenção do padrão (ignorar o workspace na raiz) é óbvia para quem o escreveu, então ninguém relê.
Quem pegou foi a **contagem**: 98 arquivos num commit inicial de harness é pouco.

**Regra**: diretório de workspace no `.gitignore` da raiz é **sempre ancorado** (`/backend/`,
`/frontend/`, `/tools/`). Antes de qualquer commit que acrescente arquivo ao harness, cruzar o que
existe com o que o git vê:
`comm -23 <(find .claude -type f -not -path "*/__pycache__/*" | sort) <(git ls-files -co --exclude-standard .claude | sort)`
— o que sobrar tem de ser exatamente as exclusões declaradas (`_backup_*`, `gate/*.json`,
`settings.local.json`).

**Automatizável?**: **sim — candidata a etapa do `verify.sh harness`**: reprovar quando algum arquivo
de `.claude/` (fora das exclusões declaradas) é ignorado pelo git (`git check-ignore` sobre a
lista do `find`). Não implementada na 001 (achado durante o `/finish-task`, que não gera código); a
promoção fica para uma spec própria.
