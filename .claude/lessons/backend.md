# Lições Backend — ERP Valor Fiscal

> Erros reais encontrados em sessões anteriores. Leia antes de gerar qualquer arquivo backend.

---

### [BE-001] Import de AppError sem uso

**Contexto**: Services que tratam erros via try/catch e relançam sem usar `AppError` diretamente.

**Erro cometido**: importar `AppError` por hábito, mesmo quando o service não lança `new AppError()`.

**Regra correta**: só importar `AppError` quando o arquivo **instancia** `new AppError(...)`.

> **Refinado em 2026-08-01 (spec 014)**: a regra original exigia `throw new AppError`. Isso gerava
> falso positivo em middlewares e callbacks do Express, onde o erro é **encaminhado** e não
> lançado — `next(new AppError(...))` e `callback(new AppError(...))` (ex.: `fileFilter` do
> multer). O hook passou a checar `new AppError`, que continua pegando o caso real da lesson
> (importar e nunca referenciar).
>
> **Nota em 2026-08-03 (spec 015)**: o hook barra `*.spec.ts` que importa `AppError` só para
> `expect(...).rejects.toBeInstanceOf(AppError)`. **Não refinar o hook por causa disso** — a
> saída correta é melhor que o atalho: asserir a **mensagem em português**
> (`rejects.toThrow('Motivo da rejeição é obrigatório.')`) testa o que o usuário realmente lê e
> pega uma regressão de texto que o teste de tipo deixaria passar. O bloqueio empurra para o
> teste mais forte; mantê-lo é intencional.
>
> Cuidado relacionado: se você escrever a regra num **comentário** do arquivo, o `grep` do hook
> encontra o token e a verificação passa sem que o código a cumpra. Comentário não pode citar
> literalmente o que o guard procura — um guard que a própria prosa derrota não verifica nada.

**Exemplo errado**:
```typescript
import AppError from '@shared/errors/AppError' // ← nunca usado
import ICryptoProvider from '...'

class CreateServiceInvoiceService {
  public async execute(data: IRequest): Promise<ServiceInvoice> {
    try {
      const result = await axios.post(...)
    } catch (err) {
      // erro relançado sem AppError
    }
  }
}
```

**Exemplo correto**:
```typescript
// Sem o import de AppError se não for usar throw new AppError()
import ICryptoProvider from '...'
```

---

### [BE-002] Variável inicializada e imediatamente sobrescrita em try/catch

**Contexto**: Qualquer service que usa try/catch para chamar APIs externas e precisa de variáveis de resultado.

**Erro cometido**: declarar variável com valor inicial (`= {}` ou `= ''`) que é sempre sobrescrita dentro do try e do catch — ESLint acusa `no-useless-assignment`.

**Regra correta**: declarar sem inicializar quando try e catch sempre atribuem um valor antes do uso.

**Exemplo errado**:
```typescript
let responseData: Record<string, unknown> = {}   // ← inicial nunca usado
let plugnotas_id: string = ''                     // ← inicial nunca usado

try {
  responseData = await axios.post(...)
  plugnotas_id = result.id
} catch (err) {
  responseData = err?.response?.data ?? {}
  plugnotas_id = `ERR_${Date.now()}`
}
```

**Exemplo correto**:
```typescript
let responseData: Record<string, unknown>    // sem inicialização
let plugnotas_id: string                     // sem inicialização

try {
  responseData = await axios.post(...)
  plugnotas_id = result.id
} catch (err) {
  responseData = err?.response?.data ?? {}
  plugnotas_id = `ERR_${Date.now()}`
}
```

---

### [BE-003] Rota pública de webhook registrada APÓS ensureAuthenticated

**Contexto**: Webhooks recebidos de terceiros (PlugNotas, Bradesco, D4Sign) são rotas públicas sem JWT.

**Erro cometido**: registrar a rota de webhook depois de `routes.use(ensureAuthenticated)`, bloqueando todas as chamadas do terceiro.

**Regra correta**: rotas de webhook **DEVEM** ser registradas **antes** do `routes.use(ensureAuthenticated)` em `src/shared/infra/http/routes/index.ts`.

**Exemplo errado**:
```typescript
routes.use(ensureAuthenticated)  // linha 139
routes.use('/webhook/plugnotas/nfse', webhookRoutes)  // ← BLOQUEADO
```

**Exemplo correto**:
```typescript
routes.use('/webhook/plugnotas/nfse', webhookRoutes)  // ← pública, linha 136
routes.use(ensureAuthenticated)  // linha 139
routes.use('/serviceinvoice', serviceInvoicesRoutes)  // ← protegida
```

---

### [BE-004] Stub de entity referenciada por outro programador — não gerar módulo completo

**Contexto**: Quando uma entity depende de outra que ainda não existe no projeto (criada por outro programador).

**Regra correta**: criar apenas o arquivo mínimo da entity (stub) para que o TypeScript compile, sem criar o módulo DDD completo. O stub deve ter: PK, campos básicos, `created_at`, `updated_at`. Sem auditoria de `user_created`/`user_updated`.

**Exemplo correto (stub mínimo)**:
```typescript
import { Entity, Column, PrimaryGeneratedColumn, CreateDateColumn, UpdateDateColumn } from 'typeorm'

@Entity('fiscal_cnaes')
class FiscalCnae {
  @PrimaryGeneratedColumn('uuid')
  id: string

  @Column('varchar')
  code: string

  @Column('varchar')
  name: string

  @CreateDateColumn({ type: 'timestamp' })
  created_at: Date

  @UpdateDateColumn({ type: 'timestamp' })
  updated_at: Date
}
export default FiscalCnae
```

---

### [BE-005] yarn install antes de yarn lint:fix após adicionar novos arquivos

**Contexto**: Após criar novos módulos com novos arquivos TypeScript, o lockfile pode ficar desatualizado.

**Regra correta**: se `yarn lint:fix` retornar erro de lockfile, rodar `yarn install` primeiro.

```bash
cd backend/admin
yarn install   # só se necessário
yarn lint:fix
```

---

### [BE-006] FK de tabelas inexistentes em migrations

**Contexto**: migrations que referenciam tabelas criadas por outro programador.

**Regra correta**: criar as FKs normalmente na migration. Se a tabela referenciada não existir ainda no banco, a migration vai falhar — o outro programador deve rodar a sua migration primeiro. Documentar essa dependência com comentário na migration.

```typescript
// DEPENDÊNCIA: esta migration requer que as tables 'fiscal_cnaes' e 'fiscal_tax_codes'
// já existam. Rodar após as migrations dos módulos fiscal_cnaes e fiscal_tax_codes.
```

### [BE-010] Campos sensíveis (api_key, senha) precisam de CryptoProvider no Create E no Update

**Contexto**: Services que salvam chaves de API ou outros dados sensíveis no banco.

**Erro cometido**: `CreateCompanyInvoiceConfigService` e `UpdateCompanyInvoiceConfigService` foram gerados sem injetar `CryptoProvider`. A `plugnotas_api_key` foi salva em texto puro. Ao tentar descriptografar no `CreateServiceInvoiceService`, falhou com "Formato de texto criptografado inválido."

**Regra correta**: qualquer service que salva dado sensível DEVE:
1. Injetar `CryptoProvider` com `@inject('CryptoProvider') private cryptoProvider: ICryptoProvider`
2. Chamar `this.cryptoProvider.encrypt(plainText)` ANTES de salvar
3. No Update: só re-criptografar se o campo foi fornecido E não está vazio

```typescript
// CreateService — sempre criptografa
const encrypted = this.cryptoProvider.encrypt(data.api_key)
await repo.create({ ...data, api_key: encrypted })

// UpdateService — só criptografa se campo foi alterado
if (api_key !== undefined && api_key !== '')
  reg.api_key = this.cryptoProvider.encrypt(api_key)
```

**Frontend**: nunca pré-popular campo de chave/senha com valor do banco (mesmo criptografado). Mostrar vazio com label "deixe em branco para manter a atual". Só enviar o campo no payload se o usuário digitou algo.

---

### [BE-007] PK de tabelas em migrations

**Contexto**: migrations que tem o id uuid como pk.

**Regra correta**: a coluna `id` NÃO recebe `default` de geração no banco, e NÃO
recebe `generationStrategy: 'uuid'`. O UUID vem da APLICAÇÃO, no `create` do
repositório (`id: uuidv4()`).

**Vale para QUALQUER função de geração**, não só a nomeada: `uuid_generate_v4()`,
`gen_random_uuid()` ou o que vier depois. O ponto não é qual função — é que a
geração não é do banco.

**Erro real cometido (2026-08-13, spec 049)**: as migrations
`1785948040503/504/505-CreateTablePatients*` traziam
`default: 'gen_random_uuid()'` comentado como *"função exigida pela lesson
[BE-007]"* — leitura invertida, provocada por esta lesson nomear só a outra
função. `gen_random_uuid()` NÃO EXISTE neste PostgreSQL (é do pgcrypto), então as
três migrations nunca rodaram e travaram a fila inteira para todas as features
seguintes. Ver o comentário em `1785948040480-CreateTableCarriers.ts:41`, que já
registrava a ausência da função.

**Promovível**: sim — um hook pode rejeitar `default:` e `generationStrategy` na
coluna `id` de qualquer migration nova, sem depender de leitura correta do texto.

> **Terceira ocorrência da MESMA causa, em 2026-08-19 (spec 041)**: o
> `.claude/specs/_templates/plan.md` trazia, na linha de exemplo da tabela de
> entidades, `| `id` | `uuid` PK | não | `gen_random_uuid()` |`. Todo plan gerado
> por `/spec-plan` herdava a orientação proibida **antes de qualquer código
> existir** — e o hook não pega, porque ele audita migrations, não specs. O plan
> da 041 nasceu com o defeito e só não virou migration porque foi lido antes de
> executar.
>
> **A correção foi na ORIGEM**: o template agora traz a regra no lugar do valor
> errado. Vale a generalização — *quando uma lesson promovida a hook se repete, o
> primeiro lugar a olhar não é o hook, é o material que o desenvolvedor (ou o
> agente) copia*. Hook audita a saída; template molda a entrada, e uma entrada
> envenenada produz o erro em toda feature futura de uma vez.
>
> **Automatizável?**: sim, e barato — o mesmo grep do hook aplicado a
> `.claude/specs/_templates/*.md` e aos `plan.md` gerados. Enquanto não houver,
> fica **delegada ao `verifier`**: ao auditar uma feature, conferir se o `plan.md`
> propõe `default`/`generationStrategy` na PK.

---

### [BE-008] Service de integração com API externa — erros antes do try-catch não salvam no banco

**Contexto**: Services que chamam APIs externas (PlugNotas, Bradesco) e depois salvam no banco.

**Erro cometido**: código que pode lançar exceção (decrypt, validações) foi colocado ANTES do try-catch. Se lança, nada é salvo na tabela — a exceção propaga para o caller sem persistir o estado de erro.

**Regra correta**: qualquer código que pode falhar e que deveria resultar em um registro de ERRO no banco deve estar DENTRO do try-catch, ou deve ter validação explícita antes:

```typescript
// ERRADO — decrypt antes do try-catch
const apiKey = this.cryptoProvider.decrypt(encryptedKey)  // ← se lança, nada salva
try {
  const resp = await axios.post(...)
} catch (err) {
  status = 'ERRO'
  // salva no banco...
}
await repository.create({ status, ... })

// CORRETO — validar antes e descriptografar dentro do try-catch
if (!encryptedKey) {
  throw new AppError('Configuração de API não encontrada.', 400)
}
try {
  const apiKey = this.cryptoProvider.decrypt(encryptedKey)  // ← dentro do try
  const resp = await axios.post(...)
} catch (err) {
  status = 'ERRO'
}
await repository.create({ status, ... })
```

---

### [BE-009] Formato de competência — split por separador errado

**Contexto**: Service que recebe competência no formato `yyyy-MM` do frontend.

**Erro cometido**:
```typescript
// Frontend envia 'yyyy-MM' (ex: '2025-05')
const [year, month] = competence.split('/')  // ← split por '/' mas formato usa '-'
// resultado: year='2025-05', month=undefined
const date = `${year}-${month}-01`  // ← '2025-05-undefined-01' INVÁLIDO
```

**Regra correta**: verificar qual separador o frontend usa. Se frontend envia `yyyy-MM`:
```typescript
const competenceDate = `${competence}-01`  // '2025-05-01' CORRETO
```

---

### [BE-011] Claude API retorna JSON envolto em markdown code fences

**Contexto**: Qualquer provider que chama a API do Claude (`POST /v1/messages`) e faz `JSON.parse()` na resposta.

**Erro cometido**: fazer `JSON.parse(response.data.content[0].text)` diretamente. Mesmo com "Retorne APENAS um JSON válido" no prompt, o Claude frequentemente envolve a resposta em ` ```json ... ``` `, causando:
```
Unexpected token '`', "```json\n{..." is not valid JSON
```

**Regra correta**: sempre limpar os code fences antes de parsear:

```typescript
const textContent = response.data.content[0].text as string

const cleanedContent = textContent
  .replace(/^```(?:json)?\s*/i, '')
  .replace(/\s*```\s*$/, '')
  .trim()

const result = JSON.parse(cleanedContent)
```

**Aplicar em**: todo provider/service que chama a Claude API e espera JSON como resposta.

---

### [BE-012] Typecheck do backend pode "passar"/"falhar" sem ter checado nada (TS6059)

**Contexto**: gate `verify.sh` backend (tsc --noEmit). Descoberto em 2026-07-12 ao concluir tasks: o typecheck estava inoperante desde março.

**Erro cometido**: o `tsconfig.json` não tinha `include`, então `coverage/` (gerado por jest --coverage), `babel.config.js`, `jest.config.ts` e `eslint.config.cjs` entravam no programa e violavam o `rootDir: ./src` (TS6059). **Erros de configuração fazem o tsc abortar ANTES da checagem de tipos** — o gate ficava vermelho por ruído e nenhum erro real de `src/` era reportado. Quando corrigido, afloraram 335 erros mascarados (302 em fakes mortos + 33 reais), incluindo specs copiados entre módulos com imports quebrados.

**Regra correta**:
1. `tsconfig.json` do backend DEVE manter `"include": ["src"]` (aplicado em 2026-07-12 — não remover).
2. Se o typecheck falhar só com `TS6059`/erros de config, NÃO tratar como "pré-existente ignorável": o tsc não checou nada — corrigir a config e medir o que estava mascarado antes de concluir qualquer task.
3. Ao criar módulo novo por cópia (scaffold), NUNCA copiar a pasta `tests/` do módulo de origem — escrever specs do módulo novo. (Imports quebrados agora são pegos mecanicamente pelo typecheck do gate.)
4. `jest.config.ts` fica fora do projeto TS — está no `ignores` do `eslint.config.cjs` (parser type-aware não o cobre).

**Status de promoção**: parcialmente PROMOVIDA → a regra 1 é a própria correção; regras 2–3 são julgamento (permanecem textuais); violações de import agora falham mecanicamente no `verify.sh` (typecheck ativo).

---

### [BE-014] Rota literal registrada DEPOIS de rota `/:param` — o Express sombreia [PROMOVIDA → hook]

**Contexto**: descoberto em 2026-08-04 (spec 016), pelo `verifier` — não pelos gates.

**Erro cometido**: no módulo `donors_collections_others`, as rotas de imagem (`POST /file`,
`DELETE /file`) foram registradas **depois** de `PUT /:id` e `DELETE /:id`. O Express casa
handlers na **ordem de registro**, então:

```
DELETE /donorcollectionother/file?id=...&files_id=...
  → cai em DELETE '/:id' com id='file'
  → celebrate: 400 {"message":"\"id\" must be a valid GUID"}
  → o controller de arquivo NUNCA é alcançado
```

A remoção da imagem era inalcançável em runtime. **Nenhum gate pega isso**: ESLint não sabe de
roteamento, o typecheck compila normalmente e o teste unitário testa o service, não a rota.

**Por que nunca apareceu antes**: todos os outros módulos com upload (`donors_photos`,
`customerfiles`, `employeefiles`, `productsFiles`) só têm `/file` — nenhum tem `/file` e `/:id`
no mesmo verbo. O conflito só nasce quando os dois coexistem.

**Regra correta**: dentro de um `*.routes.ts`, rotas de **caminho literal** vêm sempre **antes**
das rotas com parâmetro do mesmo verbo.

**Exemplo errado**:
```typescript
routes.delete('/:id', ...)     // ← casa primeiro
routes.delete('/file', ...)    // ← inalcançável
```

**Exemplo correto**:
```typescript
routes.delete('/file', ...)    // ← literal primeiro
routes.delete('/:id', ...)
```

**Automatizável?**: sim — **PROMOVIDA** para `.claude/hooks/post-edit-check.sh`. O hook extrai os
pares (verbo, caminho) de qualquer `*.routes.ts` na ordem de registro e falha se um primeiro
segmento literal aparecer depois de um `/:param` do mesmo verbo. Validada contra os 121 arquivos
de rota do projeto: **zero** falso positivo, e reproduz o bug original quando a ordem é invertida.

**Limites do guard** (caracterizados na auditoria — não confie nele como cobertura total):

- **Falso negativo em segmento profundo**: o hook compara apenas o **primeiro** segmento do
  caminho. `get('/show/:id')` seguido de `get('/show/all')` é sombreamento real e passa batido.
  Colisão em segmento profundo continua sendo trabalho do `verifier` e da revisão humana.
- **Falso positivo teórico**: `delete('/:id/note')` antes de `delete('/file/:files_id')` dispara o
  hook sem haver sombreamento. É benigno — a correção que o hook pede (literal antes de param) é
  sempre segura — e o padrão não existe em nenhum dos 121 arquivos de rota atuais.

> Note que esta lesson é irmã da BE-003/AG-006 (webhook antes do `ensureAuthenticated`): as duas
> são sobre ordem de registro importar. A diferença é o escopo — BE-003 é entre arquivos
> (`routes/index.ts`), por isso fica com o `verifier`; BE-014 é dentro de um arquivo só, por isso
> coube no hook.

---

### [BE-013] Jest 26 não roda NENHUM teste que importe typeorm (bloqueio de toolchain ativo)

**Contexto**: descoberto em 2026-08-03 (spec 015), mas anterior a ela — a spec 012 já convivia com o
problema sem que ninguém tivesse notado.

**Sintoma**: qualquer `.spec.ts` cuja cadeia de imports alcance `typeorm` morre antes do primeiro
teste:

```
Cannot find module 'ansis' from 'node_modules/typeorm/platform/PlatformTools.js'
```

**Causa raiz**: `jest@26.6.3` não lê o campo `exports` do `package.json` (suporte só a partir do
Jest 28). O `ansis`, dependência do `typeorm@0.3.x`, se declara **apenas** por `exports`.

**Alcance**: o gatilho é a cadeia de imports conter um **import de VALOR de `typeorm` que
sobreviva à emissão**. Import usado só como tipo é elidido pelo compilador e não conta.

Na prática isso inclui, mas **não se limita a**, `AppDataSource`: importar uma **entity** como
valor também quebra, e entity nenhuma passa perto do `AppDataSource`. Exemplo vivo:
`donors_freezings/services/CreateDonorFreezingFromCollectionService.ts` importa a entity
`DonorFreezing` e seu spec só sobrevive porque ela é usada **apenas como tipo de retorno**. No dia
em que alguém a usar como valor (`new DonorFreezing()`, `DonorFreezing.name`), aquele spec morre.

⚠️ **Esta seção já esteve errada duas vezes, sempre superestimando o bloqueio.** Dizia que
quebrava "testar service que importa outro service concreto… é o caso de todo o módulo
`donors_workflow_histories`" — falso: aqueles specs rodam verdes, e **18 pontos do projeto injetam
`TransitionDonorWorkflowService` pela classe e têm teste**. Depois passou a dizer "alcançar o
`AppDataSource`", o que é verdadeiro mas incompleto.

**Contornos que NÃO funcionam** (todos testados, não repetir):

| Tentativa | Falha em |
|-----------|----------|
| `moduleNameMapper` para `ansis` | avança e trava em `node:util` — Jest 26 também não resolve o prefixo `node:` |
| `moduleNameMapper` `'^node:(.*)$': '$1'` | devolve builtin como caminho de arquivo → `ENOENT: open 'util'` |
| resolver customizado com `defaultResolver` | mesma coisa: o resolver não sinaliza "core module" ao runtime |
| `jest.mock('typeorm', () => …)` com factory | `ts-jest@26` usa `ts.getMutableClone`, **removida no TypeScript 5.x** → `TypeError` |

**Única saída DEFINITIVA**: subir `jest` e `ts-jest` para versões compatíveis com TypeScript 5.9.3.

**Contorno por caso**: quebrar a cadeia até o `AppDataSource` com **inversão de dependência** —
injetar por token de interface em vez da classe concreta, com `import type`. É o que o próprio
`TransitionDonorWorkflowService` faz com `DonorConsentGate`, `DonorReleaseGate` e
`TransactionRunner`. Use quando a cadeia **de fato** alcançar o `AppDataSource`, e confirme
rodando o spec — não por suposição.

⚠️ **NÃO inverter preventivamente.** Em 2026-08-20 um seam foi criado para o
`ApplyDonorFreezingWorkflowService` supondo que `@inject(Classe)` bastasse para bloquear, e foi
**removido no mesmo dia**: o teste mostrou que injetar a classe funciona. Ali não havia ciclo e 18
outros consumidores injetam a classe direto — o seam seria um one-off, com o efeito colateral de o
service ganhar duas identidades no container (singleton pelo token, transient pela classe).

**RETENTAR SUÍTES ESTACIONADAS — a lição mais cara desta lesson.** O bloqueio some sozinho quando
alguém inverte uma dependência lá atrás, em outra spec, sem saber que destravou o seu teste. Foi o
que aconteceu com o CA-07 da spec 019: estacionado em 2026-08-05 por bloqueio real, seguiu parado
depois que a inversão do `TransactionRunner` o destravou, e em 2026-08-20 bastou mover o arquivo
de volta e corrigir o caminho do import. **Antes de escrever qualquer contorno, mova o `.pendente`
e rode.**

**Enquanto não subir o Jest**:
1. `yarn test` sem filtro pode ficar vermelho. Não é regressão — confirme com `git stash` antes de
   culpar a sua alteração.
2. `verify.sh backend <modulo>` **com escopo** continua sendo verificação válida do módulo novo.
3. Ao escrever spec de service que alcança o `AppDataSource`: primeiro **rode**; se falhar, tente a
   inversão; só estacione em `tests/_pendente_be013/` se ela não couber — e registre no `tasks.md`
   qual CA fica sem verificação executável.

**Suítes estacionadas hoje: NENHUMA.** Não existe mais nenhuma pasta `_pendente_be013/` nem
arquivo `.pendente` no repositório.

**Destravadas em 2026-08-20**, todas apenas movendo o arquivo de volta e corrigindo o caminho do
import — **nenhuma mudança de código de produção**:
- `donors_freezings/tests/ApplyDonorFreezingWorkflowService.spec.ts` (CA-07 da spec 019) — 3 testes
- `donors_freezings_thaws/tests/ApplyDonorFreezingThawWorkflowService.spec.ts` (spec 022) — e
- `donors_collections_conclusions/tests/ApplyDonorCollectionConclusionDecisionService.spec.ts`,
  juntas 15 testes

⚠️ `donors_workflow_histories/tests/RejectDonorService.spec.ts` (spec 015) e
`crm/leads/tests/ConvertCrmLeadToDonorService.spec.ts` (spec 012) constavam como bloqueadas até
2026-08-20. **Rodam verdes** — 30 testes.

Somando: **48 testes** estavam parados sem motivo, alguns havia semanas. Nenhum precisava de
contorno; todos precisavam apenas de alguém rodar.

**Status de promoção**: NÃO promovível — é limitação de ambiente, não erro de código. Permanece
textual até o upgrade do Jest, quando deve ser **apagada**.

⚠️ **Esta lesson já esteve errada TRÊS vezes** — a redação do "Alcance" (duas versões) e a lista
de suítes bloqueadas —, e nas três o erro foi no sentido de **superestimar** o bloqueio, mantendo
48 testes parados sem necessidade. O custo não é teórico: a ausência do CA-07 da spec 019 deixou
passar um defeito que impedia todo congelamento de teste.

**Ao consultá-la, verifique antes de aceitar: rode o spec.** A verificação mecânica é nível 1;
esta lesson é nível 2. Se algum dia a lista acima voltar a ter itens, trate-a como suspeita até
provar o contrário.

---

### [BE-015] Enum novo que espelha o de outro módulo com valores QUASE iguais

**Contexto**: spec 020. O congelamento tem `DonorFreezingSamplePurpose`
(`TESTE | QUARENTENA | LIBERADA`); o estoque criogênico precisou de
`StoragePurpose` (`TESTE | QUARENTENA | LIBERADA_DOADOR | LIBERADA_PACIENTE`),
porque o botijão distingue material de doador do de paciente e o congelamento do
doador não.

**Erro cometido**: tratar os dois como o mesmo domínio. A coluna
`storage_stock.purpose` foi documentada como `StoragePurpose`, o Joi validava
`StoragePurpose`, o frontend oferecia `StoragePurpose` — e o alocador gravava
ali o valor do congelamento (`LIBERADA`), enquanto a função de compatibilidade
era chaveada pelo enum do congelamento e recebia, de dois caminhos, o enum do
estoque.

**Por que passou por todos os gates**: `TESTE` e `QUARENTENA` são idênticos nos
dois enums. Tudo funcionava — nos testes, no fluxo principal, na tela — até
alguém usar `LIBERADA`. Aí `POST /storagestock` com `purpose: 'LIBERADA_DOADOR'`
num container `LIBERADA_DOADOR` era **recusado**, com a mensagem "não pode
receber material liberada_doador". Typecheck não pega (ambos são `string` na
fronteira), lint não pega, e o teste não pegava porque testava o caso que
coincide.

**Regra correta**: quando um enum novo espelha outro com valores parcialmente
coincidentes, escrever **uma função de travessia explícita** e fazer com que
todo o módulo fale um vocabulário só:

```typescript
// A ÚNICA conversão entre os dois domínios.
export function toStoragePurpose(samplePurpose?: string | null): StoragePurpose | null {
  switch (samplePurpose) {
    case DonorFreezingSamplePurpose.LIBERADA:
      return StoragePurpose.LIBERADA_DOADOR   // ← o valor que NÃO coincide
    // ...
  }
}
```

E cobrir com teste **o valor que diverge**, não o que coincide: é a parte
coincidente que esconde o bug.

**Onde mais olhar quando isso acontecer**: a conversão precisa valer também no
**backfill da migration** — copiar a coluna crua de uma tabela para a outra
reproduz o bug nos dados históricos, onde é mais caro descobrir.

> **Avaliação de promoção**: não é promovível a hook nem a ESLint — exige
> entender que dois enums de módulos diferentes descrevem o mesmo conceito com
> recortes distintos, que é julgamento de domínio. **Delegada ao `verifier`**:
> ao auditar spec que cria enum espelhando outro, conferir se existe função de
> travessia e se o valor divergente tem teste.


---

### [BE-016] `Joi.boolean()` no `Segments.QUERY` entrega BOOLEAN ao controller — comparar com `'true'` inverte o filtro

**Contexto**: spec 025. Descoberto pelo `verifier`, não pelos gates.

**Erro cometido**: a rota declarou `search_is_active: Joi.boolean().optional()` na QUERY e o
controller converteu com `search_is_active === 'true'`, no pressuposto de que query string
sempre chega como texto. O celebrate roda o Joi com `convert: true` e **substitui `req.query`**
pelo objeto já convertido (`Object.defineProperty(req, 'query', { value })`), então o controller
recebe um **boolean**. `true === 'true'` é `false`, e o filtro passou a devolver o oposto do
pedido:

```
?search_is_active=true  → boolean true  → 'true' ? não → false → WHERE is_active = false
```

Na tela, filtrar **"Ativo: Sim"** listava exatamente os protocolos **inativos**.

**Por que nenhum gate pegou**: para o typecheck tudo é `string`/`boolean` válido; o ESLint não
sabe de semântica; e os specs de service **recebem o valor já convertido** — a fronteira
query→service não tinha teste nenhum. O bug só aparece com o servidor de pé.

**Regra correta**: para filtro booleano em QUERY, seguir a convenção já estabelecida no projeto —
`Joi.string().valid('true', 'false')`, e converter no controller com `=== 'true'`:

```typescript
// rota
search_is_active: Joi.string().valid('true', 'false').optional(),

// controller — undefined precisa significar "sem filtro", nunca `false`
search_is_active: parseOptionalBoolean(search_is_active),
```

Precedentes corretos: `documents_files/.../documentsFiles.routes.ts:97` e
`crm/leads_workflow_histories/.../crmLeadsWorkflow.routes.ts:44`.

**Cuidado com o `undefined`**: converter com `Boolean(value)` ou `value === 'false' ? false : true`
faz "sem filtro" virar um filtro. O `undefined` tem de sobreviver até o repositório.

**Como testar**: a conversão não é testável no controller — `jest.mock` com factory morre no
ts-jest 26 (`ts.getMutableClone is not a function`, lesson **BE-013**). Extrair para helper puro
em `helpers/` e testar o helper (ver
`laboratories/exams_protocols/helpers/parseOptionalBoolean.ts` e seu spec).

**Automatizável?**: sim, e **vale promover** — é a 2ª vez que o par celebrate+booleano aparece.
Guard sugerido para o `post-edit-check.sh`: ao editar um `*.routes.ts`, falhar se um campo
declarado como `Joi.boolean()` dentro de `Segments.QUERY` for comparado com `'true'`/`'false'`
no controller correspondente. Enquanto não for promovida, fica com o `verifier`: ao auditar
módulo com filtro booleano de listagem, conferir o tipo que o controller realmente recebe.

---

### [BE-017] Repositório com `manager` opcional: o `create` do TypeORM não persiste — quem persiste é o `save`

**Contexto**: descoberto em 2026-08-11 (spec 045), ao planejar o gerador de `donor_code`. Bug
vivo em `DonorRepository.create` desde a introdução do parâmetro `manager?` (conversão de lead
do CRM).

**Erro cometido**: o repositório escolhia o repo certo, usava-o só para instanciar, e persistia
com o repositório próprio:

```typescript
const repo = manager ? manager.getRepository(Donor) : this.ormRepository
const reg = repo.create({ id: uuidv4(), ...data })   // só instancia o objeto
await this.ormRepository.save(reg)                   // ❌ persiste FORA da transação
```

`repo.create()` do TypeORM **não toca o banco** — devolve uma instância da entity. O INSERT
acontece no `save`. Com `this.ormRepository.save`, o INSERT do doador escapava da transação do
`ConvertCrmLeadToDonorService`: se a transição de workflow ou o update do lead falhassem depois,
o doador ficava órfão e **já commitado**.

**Por que passa despercebido**: nada falha. Não há erro, não há warning, o teste passa, o dado
aparece no banco. O defeito só se manifesta no rollback — que é justamente o caminho que ninguém
exercita.

**Regra correta**:
1. Em repositório com `manager?`, **toda** operação de escrita usa o `repo` resolvido:
   `await repo.save(reg)`, `await repo.update(...)`, `await repo.delete(...)`.
2. `create()` nunca conta como escrita. Se o método só chama `create`, ele não persistiu nada.
3. Se um service abre transação e passa o `manager`, conferir no repositório que o `save` a
   respeita — o tipo não pega isso: `this.ormRepository.save` compila igual.

**Automatizável?**: sim, e **vale promover**. Guard sugerido para o `post-edit-check.sh`: em
`infra/typeorm/repositories/*.ts`, falhar se um método que declara `manager?: EntityManager`
contiver `this.ormRepository.save(` / `.update(` / `.delete(`.

---

### [BE-018] `AppDataSource.transaction` direto em service torna o módulo inteiro intestável

**Contexto**: descoberto em 2026-08-11 (spec 045). O seam `ITransactionRunner` existia e estava
documentado desde a lesson BE-013, mas services novos continuavam chamando o `AppDataSource`
direto — inclusive a spec 042, que aplicou a injeção por token para o `DonorConsentGate` do
`TransitionDonorWorkflowService` e **deixou a transação do mesmo arquivo** como estava.

**Erro cometido**: `TransitionDonorWorkflowService` importava `AppDataSource` como **valor**
(`import { AppDataSource } from '@shared/infra/typeorm/dataSource'`) para chamar
`AppDataSource.transaction(...)`. Consequência: o módulo e **todo spec que o importasse
transitivamente** morriam no load do Jest (`Cannot find module 'ansis' from
typeorm/platform/PlatformTools.js`). `RejectDonorService.spec.ts` ficou sem rodar de março a
agosto por causa disso, e a spec 015 registrou o bloqueio como se fosse imutável.

**O custo real**: não é só o service sem teste — é a **cadeia inteira**. Um único
`AppDataSource` como valor derruba specs de módulos vizinhos que nem sabem que ele existe.

**Regra correta**:
1. Service **nunca** chama `AppDataSource.transaction`. Ou a transação vive no repositório
   (padrão preferido: advisory lock + query + escrita no mesmo lugar), ou o service injeta
   `@inject('TransactionRunner') private transactionRunner: ITransactionRunner`.
2. Import de tipo (`import type { ... }`) some na compilação e é seguro. Import de **valor**
   não.
3. Antes de declarar um módulo "bloqueado por BE-013", verificar se a cadeia alcança o
   `AppDataSource` como valor — quase sempre alcança, e quase sempre dá para cortar.
4. Comentário de "esta suíte não roda" em arquivo de teste tem prazo de validade: reconferir
   antes de confiar.

**Automatizável?**: sim, e **vale promover**. Guard sugerido para o `post-edit-check.sh`: falhar
se um arquivo em `modules/**/services/*.ts` contiver `AppDataSource.transaction(` ou importar
`AppDataSource` sem `import type`.

---

### [BE-019] Enum de identidade + carga inicial completa = cadastro impossível

**Contexto**: descoberto em 2026-08-13 (spec 048), pelo `verifier`. Os gates mecânicos
(eslint + tsc + jest) passaram; nenhum deles alcança este defeito.

**Erro cometido**: `exams_types.code` é a identidade do registro (UNIQUE). A rota validou o
campo contra o enum que nomeia os tipos conhecidos:

```typescript
code: Joi.string().valid(...Object.values(ExamTypeCode)).required()   // ❌ 4 valores
```

O seed da carga inicial cria **exatamente esses 4** valores. Resultado: os quatro únicos
códigos aceitos já estão ocupados, o UNIQUE recusa qualquer repetição, e **todo POST devolve
400**. A tela de cadastro fica decorativa — o botão existe, abre formulário, e não há payload
possível que grave. Justamente o oposto do objetivo da spec ("incluir uma variante passa a ser
configuração, e não código novo").

**Por que passa despercebido**: cada peça isolada parece certa. Enum fechado é boa prática;
UNIQUE na identidade é boa prática; seed idempotente é boa prática. O defeito só existe na
**interseção das três**, e nenhum gate olha para a interseção. O teste do service tampouco
pega: o `findByCode` mockado devolve `undefined`, então a asserção passa com enum aberto ou
fechado — é o padrão da AG-011 (cenário de teste que o sistema real não consegue atingir).

**Regra correta**: antes de validar um campo contra um enum, responder **duas** perguntas:
1. *Este campo é identidade (UNIQUE)?*
2. *A carga inicial ocupa todos os valores do enum?*

Se as duas forem "sim", o cadastro está morto. Nesse caso o enum **nomeia** os valores
conhecidos (para outros módulos os referenciarem sem string solta) mas **não restringe** a
escrita — a validação vira formato (`.pattern(/^[A-Z][A-Z0-9_]*$/)`), não pertencimento.

Distinguir dos casos em que o enum fechado está certo: `AnalysisBlockCode`, na mesma spec, é
fechado de propósito e permanece — lá existe um módulo de análise por trás de cada valor, e o
conjunto **não** é a identidade do registro.

**Automatizável?**: parcialmente. Um guard sintático não sabe se o campo é identidade. O que
cabe é **auditoria do `verifier`**: para todo `Joi.…valid(...Object.values(X))` num campo que
tenha UNIQUE na migration, conferir se existe seed que ocupe todos os valores de `X`. E, na
spec, exigir que todo CA de "é possível cadastrar" tenha um teste com um valor **novo**, não
com um valor que a carga inicial já criou.

---

### [BE-020] `take`/`skip` + `orderBy` em coluna de relação `OneToMany` some com registros

**Contexto**: descoberto em 2026-08-13 (spec 048), pelo `verifier`, na **segunda** rodada — a
linha foi introduzida justamente para corrigir outro achado da primeira.

**Erro cometido**: a listagem precisava exibir os blocos de cada tipo de exame, então o
repositório ganhou o join e, junto, a ordenação dos filhos:

```typescript
.leftJoinAndSelect('et.examtypeblock', 'blocks')
.orderBy('et.name', 'ASC')
.addOrderBy('blocks.sort_order', 'ASC')   // ❌
.take(rowsperpage).skip((page - 1) * rowsperpage)
```

Com `take`/`skip` sobre `OneToMany`, o TypeORM pagina por uma subquery de ids **distintos** —
mas leva para dentro dela **toda coluna do `ORDER BY`**. Ordenar por `blocks.sort_order` faz o
`DISTINCT` virar o par `(pai.id, blocks.sort_order)`, e o `LIMIT` volta a contar **linhas do
join**, não registros.

**O estrago medido**: 4 tipos de exame com 8 + 8 + 9 + 1 = 26 blocos. Com `rowsperpage: 25` (o
valor que a tela envia), `findAll` devolvia **3** enquanto `findAllTotal` devolvia **4** — o
tipo com um bloco só sumia da tela. Duas páginas de 2 devolviam o **mesmo** registro.

**Por que nenhum gate pega**: o repositório não é testável em unit (BE-013 — a cadeia alcança
typeorm), e os testes de service mockam o repositório. Lint e `tsc` veem uma chamada
perfeitamente válida. O sintoma é registro sumindo **em silêncio**, com o total mentindo ao
lado.

**Regra correta**:
1. Em método com `take`/`skip`, o `ORDER BY` só pode citar colunas da entidade **raiz**. Ordem
   dos filhos, se importar, é resolvida em memória por quem consome.
2. Em método **sem** paginação (`findByIdRelations`, `findOne`), ordenar por alias de join é
   seguro e é o lugar certo de fazê-lo.
3. `ExamProtocolRepository.findAll` é o precedente correto: faz `leftJoinAndSelect` e **não**
   ordena por alias do join.

**Verificação que expõe o bug** (vale para qualquer listagem com join de coleção): comparar
`findAllTotal()` com `findAll({ page: 1, rowsperpage: <o valor que a TELA envia> })` e conferir
que batem; e pedir duas páginas pequenas consecutivas, conferindo que a união não repete
registro. Rodar com `rowsperpage` alto esconde o defeito — foi assim que a primeira verificação
desta spec deu falso negativo.

**Automatizável?**: parcialmente. Guard sintático viável para o `post-edit-check.sh`: em arquivo
`**/repositories/*Repository.ts`, falhar quando um mesmo encadeamento contiver `.take(` e um
`.orderBy(`/`.addOrderBy(` cujo alias **não** seja o da entidade raiz. Enquanto não existir,
fica como item de auditoria do `verifier`.

---

### [BE-021] `leftJoinAndSelect` de entity com `@Exclude()` vaza dado sensível quando o controller responde sem `classToClass`

**Contexto**: spec 049. Para ligar o paciente à agenda compartilhada, bastava um
`leftJoinAndSelect('da.patient', 'patient')` no `AppointmentRepository`. O `Patient` tem
`@Exclude()` em `document_hash`, então parecia protegido.

**O erro**: `@Exclude()` é honrado pelo **class-transformer**, não pelo TypeORM. Quem aplica é
o `classToClass` do controller — e o `AppointmentsController` responde `res.json(result)` cru.
Nenhum dos controllers do módulo de agendamentos usa `classToClass`.

Resultado do join: `GET /appointment` passaria a devolver, para quem tem `appointments_view`:

- `patient.document_hash` — sha256 **sem sal** dos dígitos do CPF. O espaço de busca de um CPF é
  ~10^11: é força bruta em segundos, ou seja, o hash **equivale ao CPF em claro**.
- `patient.document` — o ciphertext do CPF.

E `appointments_view` não é `patients_view`: o vazamento atravessa a fronteira de permissão que
a própria spec tinha acabado de criar.

A mesma auditoria encontrou, no mesmo arquivo, três campos já expostos pelo mesmo mecanismo:
`tentant.password` e `user.password` (hashes BCrypt) e — o pior — `professional.first_access_token`,
um **token de convite vivo**: quem o recebesse conseguiria definir a senha do profissional.

**Por que nenhum gate pega**: na fronteira o que sai é um objeto JSON e nenhum teste asserta
sobre ele. Lint e `tsc` veem uma query válida. O repositório é intestável (BE-013).

**Regra correta**: antes de escrever `leftJoinAndSelect`, responder duas perguntas —
1. A entity juntada tem algum campo `@Exclude()`, credencial, token ou dado cifrado?
2. O controller que serializa este resultado usa `classToClass`?

Se a resposta for "sim" para 1 e "não" para 2, usar `leftJoin` + `addSelect([...])` com as
colunas explicitamente necessárias. Selecionar coluna a coluna é a única forma que não depende
de o próximo controller lembrar do `classToClass`.

**Verificação**: `grep -n "leftJoinAndSelect" <repo>.ts` e, para cada alias, abrir a entity e
procurar `@Exclude()`/`password`/`token`/`hash`. Depois conferir se o controller correspondente
tem `classToClass`.

**Automatizável?**: sim, e vale promover. Guard para o `post-edit-check.sh`: em
`**/repositories/*Repository.ts`, avisar em todo `leftJoinAndSelect` cujo alias corresponda a
uma entity que contenha `@Exclude()`. Enquanto não existir, é item de auditoria do `verifier`.

---

### [BE-022] Nunca renumerar migration já aplicada — e todo seed/alter precisa de guarda de existência

**Contexto**: colisão de timestamp entre features desenvolvidas em paralelo. A
tentação é renomear o arquivo para um número livre.

**O erro**: o TypeORM rastreia migration executada pelo **nome da classe**
(`Nome<timestamp>`), não pelo caminho do arquivo. Renomear `X1785948040506` para
`X1785948040513` faz o ORM ver uma migration NOVA e tentar aplicá-la de novo. Se
a operação não for idempotente, ela falha — e como `migration:run` é sequencial,
**trava a fila inteira para todas as features seguintes**, não só para a sua.

**Erro real cometido (2026-08-13)**: `AlterTableAppointmentsAddPatientsForeignKey`
(spec 049) foi renumerada de 506 para 513 depois de aplicada. Passou a falhar com
`constraint "FK_appointments_patients" for relation "appointments" already exists`
e bloqueou as migrations da spec 032. Duas features paradas por um rename.

**Regra correta**:

1. **Colidiu o timestamp?** Deixe como está se já rodou em algum ambiente. Dois
   arquivos com o mesmo timestamp e nomes distintos são feios, mas funcionam — o
   ORM os trata como registros separados. Renumerar é que quebra.
2. **Precisa mesmo renumerar** (a migration ainda NÃO rodou em lugar nenhum)?
   Confira antes: `SELECT name FROM migrations WHERE name LIKE '%SuaMigration%'`.
3. **Todo `INSERT` de seed** leva `WHERE NOT EXISTS`. **Todo `createForeignKey` /
   `addColumn` / `createIndex`** leva guarda de existência via
   `queryRunner.getTable(...)`. Não é preciosismo: é o que permite reprocessar
   sem derrubar a fila, e o que salva quando alguém renumera assim mesmo.

**Promovível**: **PROMOVIDO em 2026-08-20** (a parte mecânica). A parte do rename
exige julgamento e continua só no texto.

**Por que a promoção demorou e o que ela corrigiu** — a versão anterior desta
lesson dizia "um hook pode exigir `NOT EXISTS` em migration cujo nome comece com
`SeedTable`", e foi exatamente isso que o hook passou a fazer: **só seed**. O
`addColumn` ficou de fora, e a skill `backend-module` só tinha template de
`createTable` — então toda migration de ALTER nascia improvisada, sem guarda e
sem nada que a reprovasse. Medição em 2026-08-20: **27 dos 41 arquivos
`AlterTable*` com `addColumn` no repositório não tinham guarda nenhuma**. O
`/new-migration` ajudava a errar: o exemplo de `alter` que ele documentava era um
`addColumn` cru, sem guarda (e o de `create` ainda trazia `generationStrategy:
'uuid'`, contra a BE-007).

Lição sobre a lição: **uma lesson promovida pela metade parece resolvida.** O
texto dizia "todo `addColumn` leva guarda", o hook verificava só seed, e a
diferença entre os dois não aparecia em lugar nenhum — nem para quem gerava, nem
para o `verifier`. Ao promover, conferir se o hook cobre TODA a superfície que o
texto exige; se não cobrir, dizer no texto o que ficou de fora.

O que passou a existir:

1. `.claude/hooks/post-edit-check.sh` — em migration `AlterTable*` (ou qualquer
   uma com `addColumn`): exige `hasColumn`/`findColumnByName` para `addColumn`,
   guarda de `foreignKeys`/`indices` para `createForeignKey`/`createIndex`,
   `IF NOT EXISTS` em `ADD COLUMN` de SQL cru, e rejeita a guarda usada como
   `return` no topo quando há FK/índice depois. As checagens rodam sobre o
   código com as linhas de comentário removidas — comentário não dispara a regra
   e também não vale como guarda.
2. `.claude/scaffold/templates/backend/migration-alter.ts.tpl` (era `skills/backend-module/templates/` até a spec 085) — template de
   alter com guarda por operação, `down` guardado na ordem inversa, e os casos de
   índice parcial e backfill idempotente.
3. `.claude/commands/new-migration.md` — exemplo de `alter` refeito com guarda.

**A guarda é POR OPERAÇÃO.** `if (table?.findColumnByName('x')) return` no topo é
armadilha: com a coluna presente e a FK/índice ausentes (reprocessamento
parcial), a migration termina "com sucesso" e deixa o schema incompleto em
silêncio. Referência correta:
`1785948040584-AlterTableStorageStockPatientLink.ts`.

**As 38 migrations já versionadas que a regra reprova continuam como estão** — o
`protect-migrations.sh` bloqueia a edição delas, e reescrever migration aplicada
é o erro que esta própria lesson descreve. A regra vale da próxima em diante.

---

### [BE-023] O `CLAUDE.md` manda usar `auditDelete`, mas esse util NÃO EXISTE

**Contexto**: spec 054 (2026-08-18), ao gerar os 12 repositórios dos blocos de análise
do paciente.

**Erro cometido**: segui o `backend/admin/CLAUDE.md` ao pé da letra. Ele diz, na seção
"Repository TypeORM — regras obrigatórias":

> **`delete`**: sempre delegar para `auditDelete`
> (`import { auditDelete } from '@shared/util/auditDelete'`)

Gerei 12 repositórios com esse import. O `tsc` reprovou todos: **o arquivo não existe**.
`find src -name "auditDelete*"` não retorna nada — nem em `@shared/util/`, nem em
`@shared/utils/`. A mesma instrução estava na §8.2 da documentação de arquitetura do backend
(removida na spec 086; conteúdo em `git show bdb9b78:documentacao/BACKEND-ARCHITECTURE.md`).

**O padrão REAL do repositório** é o direto:

```typescript
public async delete(id: string[]): Promise<void> {
  await this.ormRepository.delete(id)
}
```

Confirmado em `donors_collections_motilities/.../DonorCollectionMotilityBlockRepository.ts:235`
e em todos os repositórios de análise do doador.

**Não é descoberta nova**: `patients_serology_checklist_items/.../PatientSerologyChecklistItemRepository.ts:264`
já carrega um comentário registrando exatamente isto. Ou seja, pelo menos duas specs
tropeçaram na mesma instrução — e a documentação continua prescrevendo o util fantasma.

**Regra correta**: usar `this.ormRepository.delete(ids)`. Se um dia a auditoria de
exclusão for realmente necessária, o util precisa ser **criado antes** de a
documentação mandar usá-lo.

**Por que passa despercebido**: o import compila no editor (o path alias existe), o
ESLint não resolve módulos, e só o `tsc --noEmit` acusa. Quem rodar apenas o lint
entrega o módulo quebrado.

**Automatizável?**: sim, e **vale promover** por dois caminhos:
1. Guard no `post-edit-check.sh`: falhar em `infra/typeorm/repositories/*.ts` que
   contenha `auditDelete`.
2. **Corrigir a documentação** — ✅ feito: `backend/admin/CLAUDE.md` §Repository traz o padrão
   real, e a documentação de arquitetura que prescrevia o util inexistente foi removida na spec
   086. O `repository.ts.tpl` do scaffold também traz a nota. Enquanto uma fonte prescrever o util
   inexistente, a lesson se repete a cada módulo novo.

---

### [BE-024] `celebrate` antes do `multer` faz a rota de upload retornar 400 SEMPRE

**Contexto**: spec 054 (2026-08-18), rota `POST /patientcollectionother/file`. Achado pelo
`verifier` na 2ª auditoria — a rota tinha acabado de ser criada para CORRIGIR outro achado
("a coluna `files_id` está inalcançável") e nasceu inalcançável do mesmo jeito.

**Erro cometido**:

```typescript
patientcollectionotherRouter.post(
  '/file',
  accessControl(['patients_collections_others_edit']),
  celebrate({
    [Segments.BODY]: { id: Joi.string().uuid().required() },  // ← body ainda vazio
  }),
  upload.single('file'),
  fileController.create,
)
```

Em `multipart/form-data` o `request.body` fica `{}` até o **multer** parsear — o app monta
apenas `express.json()`. O `celebrate` roda antes e rejeita **toda** requisição com
`400 "id is required"`. O controller nunca é alcançado.

**Por que passa despercebido**: lint e typecheck não veem ordem de middleware; a suíte de
services passa inteira, porque nenhum teste sobe o Express. A rota existe, aparece no
`grep`, e a task fica marcada como entregue.

**Regra correta**: `upload.single('file')` vem **antes** de `accessControl` e de `celebrate`.
Quem valida campo de multipart precisa esperar o parse.

```typescript
router.post('/file', upload.single('file'), accessControl([...]), celebrate({...}), ctrl.create)
```

O repositório já documentava isso em
`documents/documents_files/infra/http/routes/documentsFiles.routes.ts` ("upload.single ANTES do
controle de acesso: … só existe depois que o multer parseia"), e
`donors_collections_others` contorna por outro caminho (`id: Joi.optional()`).

**Automatizável?**: sim, e **vale promover**. Guard para o `post-edit-check.sh`: em
`**/infra/http/routes/*.ts`, falhar quando um handler contiver `upload.single(` com um
`celebrate(` que declare `Segments.BODY` posicionado ANTES dele na mesma chamada de rota.

---

### [BE-025] Coluna `*_by_users_id` guarda UUID — documento assinado precisa do NOME

**Contexto**: spec 054 (2026-08-18), laudo FR08. Duas rodadas do `verifier` para fechar: a
primeira pegou a ORIGEM errada, a segunda pegou o FORMATO errado.

**O caminho completo do erro**:

1. `double_checked_by: conclusion.user_updated` — origem errada. O próprio service de emissão
   sobrescreve `user_updated` com quem emitiu o PDF, então a **reemissão** nomeava como
   conferente quem tinha emitido o laudo anterior. O primeiro laudo saía certo.
2. Corrigido para `conclusion.double_checked_by_users_id` — origem certa, **formato errado**:
   a coluna guarda `request.user.id`, e o `.hbs` imprime o valor cru. O PDF sairia com
   "Técnico responsável: Ana Silva" ao lado de "Dupla checagem: 3f2c8a10-9ab1-4c7e…".

**Regra correta**: colunas `*_by_users_id` são **identidade**, não apresentação. Documento que
vai para as mãos de alguém resolve o nome na emissão (`UserRepository.findById(...).user_name`)
ou persiste o nome junto. Nunca imprime o id.

⚠️ E o par `concluded_by`/`double_checked_by` precisa sair da **mesma fonte**: metade nome e
metade uuid é o sintoma que denuncia a mistura.

**Automatizável?**: parcialmente. Guard sugerido: falhar quando um `.hbs` receber, no objeto
`variables`, uma chave cujo valor venha direto de identificador terminado em `_users_id`.
Enquanto não houver guard, fica **delegada ao `verifier`**: ao auditar geração de documento,
conferir se todo campo de assinatura imprime nome.


---

### [BE-026] Tabela de referência: a coluna que SELECIONA a linha não é a que COMPARA

**Contexto**: spec 054 (2026-08-19), 5ª e 6ª auditorias. O mesmo erro em duas tabelas da
OMS, atingindo 8 helpers de cálculo nos contextos de doador e paciente. Vivo desde a
implementação original do doador.

**A forma do erro** — Tabela 2.2 (`acceptable_differences`):

```typescript
// repositório SELECIONA a linha assim:
.where('average_min <= :v', { v }).andWhere('average_max >= :v', { v })

// helper depois COMPARA assim:
difference >= Number(range.average_min) && difference <= Number(range.average_max)
```

A faixa `average_min/average_max` existe para **escolher** a linha a partir da MÉDIA. O que a
tabela **fornece** é `acceptable_difference`. Comparar a diferença contra a faixa de médias é
erro de categoria — e o resultado não é "às vezes errado", é errado nos dois sentidos.

Provado por execução, com a linha real `35–65 → 9`:

| Bloco | Diferença | Resultado |
|---|---|---|
| Réplicas em acordo excelente | 34 | **REPROVADO** |
| Divergência grosseira | 60 | **APROVADO** |

Na Tabela 2.3 (`comparison_difference_between_replicate_counts`) o mesmo erro produziu uma
**tautologia**: o helper rechecava `min <= soma <= max`, exatamente a condição pela qual a
linha tinha sido selecionada. Sempre verdadeira ⇒ o bloco de concentração **nunca** reprovava,
em nenhum paciente e em nenhum doador, desde sempre.

**Como reconhecer**: se o `WHERE` do repositório e o `if` do helper mencionam as **mesmas
colunas**, uma das duas comparações é redundante — ou tautológica, ou de categoria errada. A
coluna que a tabela existe para fornecer é a que sobra, e é essa que precisa ser comparada.

**Regra correta**: identifique explicitamente, para cada tabela de referência, qual coluna é
**chave de busca** e qual é **valor de retorno**. Escreva no comentário do repositório. Depois
confira que o helper compara contra o valor de retorno.

**Automatizável?**: não diretamente — exige conhecer a semântica da tabela.
**Delegada ao `verifier`**: ao auditar helper que consulta tabela de referência, confrontar as
colunas do `WHERE` do repositório com as do `if` do helper. Interseção = suspeita.

---

### [BE-027] "Maior diferença todos-contra-todos" mistura itens e não mede réplica nenhuma

**Contexto**: spec 054 (2026-08-19), 6ª auditoria. Exposto só depois que a BE-026 foi
corrigida — com o comparador errado, a entrada errada não aparecia.

**O erro**: os helpers empilhavam TODAS as contagens de TODOS os itens do bloco num array e
tiravam a maior diferença absoluta:

```typescript
const allValues: number[] = []
items.forEach((i) => allValues.push(i.count_1a, i.count_1b, i.count_2a, i.count_2b))
const difference = maxPairwiseDifference(allValues)   // ← mistura itens
```

Leucócitos reais: peroxidase `60/58/62/61` e não coradas `40/42/38/39`. Cada item concorda
dentro de **4 pontos**. O código comparava **24** — a distância entre a maior leitura de um
item e a menor do outro.

**Por que é sempre grande**: quando os itens do bloco somam 100 (motilidade MP+MNP+IM,
vitalidade vivos+mortos, leucócitos), a amplitude entre itens é a própria composição da
amostra. Uma amostra com 60% de progressivos e 20% de imóveis tem 40 pontos de "diferença"
que não têm nada a ver com concordância de réplica.

**Regra correta**: a Tabela 2.2 mede a concordância entre as **duas leituras do MESMO item**.
Cada item tem a sua média → a sua linha → o seu limite. O bloco reprova se **qualquer** item
exceder o dele. Está em `@shared/utils/semenAnalysis/replicates.ts::evaluateReplicatesPerItem`.

**⚠️ E o teste que congelou o defeito era meu.** Escrevi `deve apurar a MAIOR diferença
absoluta todos-contra-todos (não par a par)` na T-02 justamente para "fixar o contrato antes
de refatorar" — e fixei o bug. Fixar comportamento observado protege contra regressão **e**
contra correção. Ao escrever teste de caracterização, marque o que é contrato deliberado e o
que é só o que o código faz hoje.

---

### [BE-028] Guarda de regra colocada na camada errada é regra que não existe

**Contexto**: descoberto em 2026-08-19 (spec 039), pelo `verifier`. Lint, typecheck e 555 testes
passaram; nenhum deles alcança o defeito.

**Erro cometido**: a RN-14 mandava recusar o lote inteiro quando algum raque de quarentena não
tivesse congelamento vinculado. A guarda foi escrita no service que EXECUTA a transferência,
percorrendo o payload recebido:

```typescript
// TransferDonorFreezingsToCleanContainerService — a camada de baixo
if (!origin.donors_freezings_id) {
  throw new AppError('...não está vinculado a nenhum congelamento...', 400)
}
```

Parece correto e é inalcançável. O raque órfão é classificado como **bloqueado** pelo service de
elegibilidade, portanto:

1. nunca aparece em `items`;
2. o frontend monta a tela a partir de `items`;
3. logo o payload **nunca** contém o órfão;
4. logo a guarda nunca dispara.

Resultado: doador com 3 raques aptos + 1 órfão transferia os 3 e o lote era **aceito**. A regra
existia em comentário, em teste e em revisão de código — em todo lugar menos no caminho que roda.

**Por que passa despercebido**: existe um teste, ele é verde, e ele exercita a guarda. O que o
teste faz é injetar o órfão **direto no payload** — um estado que o produto não consegue produzir.
É a AG-011 vista de outro ângulo: lá o cenário impossível estava no dado; aqui está na **camada**.

**Regra correta**: uma guarda pertence à camada onde a informação que ela consulta ainda existe.
Se a regra fala do que foi **excluído** de um conjunto, ela tem de rodar onde a exclusão é
visível — ou seja, sobre a lista de bloqueados, e não sobre a lista de selecionados. Duas
perguntas antes de aceitar uma validação:

1. *Existe um caminho real que entregue a esta camada o dado que a guarda procura?* Se a camada
   de cima filtra esse dado, a resposta é não.
2. *O teste dessa guarda constrói o payload com as mesmas peças que o produto usa?* Se ele monta
   à mão um estado que nenhuma tela produz, ele não prova nada sobre a regra.

**Como confirmar**: teste de mutação de um minuto. Neutralize a guarda (`if (false && cond)`) e
rode a suíte. Se nada ficar vermelho, a regra não está protegida — independentemente de quantos
testes verdes a cercam.

**Automatizável?**: parcialmente, e vale promover ao `verifier`. Para toda RN cuja redação seja do
tipo "recusa quando existe X", auditar se X pode chegar ao ponto da checagem: se a camada anterior
segrega X em outra lista, a guarda está órfã. O gate mecânico não pega; a mutação pega.

---

### [BE-029] Bloco de planilha atribuído à aba errada — e o comentário que sobrevive à correção

**Contexto**: spec 063 (2026-08-21), RN-12. Conferência da ficha do ERP contra
`FR71 - Congelamento Teste Sêmen Doador V6.xlsx`. Corrigido pela spec 065 no mesmo dia,
depois que o usuário perguntou por que a aba de motilidade tinha mudado.

**O erro**: a aba `Ficha traseira` da planilha tem um bloco com `LEITURA 1 / 2 / 3` e `MÉDIA`.
A RN-12 concluiu que **a motilidade** passava a ter três leituras por réplica, e a implementação
acrescentou `count_1c`/`count_2c` a `donors_collections_motilities` — migration, entity, DTOs,
Joi, helper, teste e as duas telas.

O bloco não era da motilidade. Era do **MOT — concentração de espermatozoides móveis**, uma
grandeza MEDIDA em câmara que pertence à **aba de concentração**. A prova estava no próprio diff:
a mesma spec 063 criou `MOTILE_CONCENTRATION` em `DonorCollectionConcentrationName`, com o
comentário *"MEDIDO, com três leituras por réplica, como a ficha traseira do FR71 desenha"*. A
terceira leitura foi aplicada **duas vezes** — uma certa e uma errada — e ninguém cruzou as duas.

A motilidade (MP/MNP/IM) é **percentual**, as três linhas somam 100 por coluna, e sempre teve duas
leituras por réplica. Concentração é **contagem em milhões/mL**. São grandezas de tipos
diferentes; o rótulo `MOT` é que as aproxima no papel.

**Por que passa despercebido**: o gate mecânico aprova sem hesitar. `COUNT_FIELDS` é a lista única
que alimenta média, soma-100 e aceitação de réplica, então acrescentar duas colunas mantém tudo
coerente — o teste continua verde porque foi atualizado junto, e o typecheck não tem opinião sobre
qual grandeza a coluna mede. **Nenhuma verificação automática distingue "seis leituras corretas" de
"seis leituras erradas".**

**Regra correta**: antes de replicar layout de coluna entre abas a partir de uma planilha, responder
duas perguntas:

1. *De qual GRANDEZA é este bloco?* Percentual que soma 100 entre linhas, ou contagem absoluta?
   O bloco pertence à aba que já mede essa grandeza — não à aba cujo nome se parece com o rótulo.
2. *Este mesmo bloco já foi implementado em outro lugar nesta mesma entrega?* Se a resposta for
   sim, um dos dois está errado. Dois itens novos citando "a ficha traseira do FR71" no mesmo diff
   é sinal, não coincidência.

⚠️ **Conteúdo da FR71 não está nas células.** A aba `Ficha` vive em 31 caixas de texto em
`xl/drawings/drawing1.xml`; só a `Ficha traseira` está em `xl/worksheets/sheet2.xml`. Quem lê o
arquivo por células vê quase nada e preenche a lacuna por inferência — que foi exatamente o que
aconteceu.

**A segunda metade da lição: comentário que sobrevive à mudança é a próxima regressão.** Reverter
a spec 063 exigiu reescrever texto em cinco arquivos que **afirmavam** três leituras na motilidade
(`COUNT_FIELDS`, o teste, o `<Th>` do modal, o enum da concentração, a migration). Deixá-los seria
entregar à próxima auditoria de conformidade FR71 um repositório que documenta a versão errada e a
convida a reimplantá-la. Ao reverter uma decisão, o texto que a justificava é parte do escopo — e
vale registrar **por que** estava errada, não só apagar. A `COUNT_FIELDS` de hoje começa com "NÃO
ACRESCENTE UMA TERCEIRA LEITURA AQUI" e diz de quem é o bloco.

**Automatizável?**: **não**, e é o ponto. Exige ler a planilha e julgar de que grandeza é o bloco —
nenhum grep separa a coluna certa da errada. O que **é** delegável ao `verifier`: quando uma
entrega acrescenta o mesmo conceito ("três leituras", "a ficha X pede Y") a **dois módulos
diferentes** no mesmo diff, sinalizar para conferência humana. E, ao remover campo/item, auditar se
sobrou comentário afirmando a versão anterior — `grep` por "SEIS\|seis leituras" ao lado de uma
constante de quatro campos é barato e teria pego este caso na volta.

---

### [BE-030] Remover a FONTE de um dado sem tocar no service que o SOBRESCREVE apaga o que o operador digita

**Quando aconteceu**: 2026-08-27, na aba DESCONGELAMENTO do painel da coleta (specs 023, 068, 069).

**Sintoma relatado pelo usuário**: "não consigo informar os dados do pós-descongelamento, estão com
os campos desabilitados" e "a criosobrevida não atualiza".

**O que aconteceu**: a spec 023 desenhou o momento `POS_DESCONGELAMENTO` como DERIVADO — concentração,
células redondas e as três motilidades vinham das análises da etapa FR71, e
`SyncDonorFreezingThawMomentService` as reescrevia a cada abertura da ficha. A tela, coerentemente,
desabilitava os cinco campos. Um ano de specs depois, a **068 removeu a etapa FR71 do painel de
análises** — decisão correta, e "só tela", como a própria spec registra.

Só que o service não é tela. Ele continuou rodando, continuou não achando bloco FR71 nenhum, e
continuou atribuindo o resultado da leitura **diretamente**:

```ts
existing.concentration = analysis.concentration   // ← null, SEMPRE, depois da 068
```

Resultado: cinco campos travados e permanentemente vazios, e com eles a criosobrevida — que é a
divisão do pós-descongelamento pelo prévio e por isso ficou em branco nas quatro linhas.

**Por que passa despercebido**: nenhum gate reprova. Os testes do sync passam porque **mockam** o
bloco de análise — eles provam que o service copia o que a análise diz, que é exatamente o
comportamento que deixou de fazer sentido. Typecheck e lint não têm opinião sobre uma fonte de dados
que sumiu da UI. E a perda é a silenciosa: o `PUT` responde 200, o toast diz "salvo com sucesso", e o
valor só some na **próxima abertura**.

**Regra correta**: ao remover uma tela, uma etapa ou um caminho de escrita, procurar quem **escreve
a partir daquilo** — não só quem lê. Um `grep` pelo enum/valor removido (`FR71`, aqui) nos
`services/` é o começo. Para cada acerto, decidir explicitamente:

1. a escrita ainda tem fonte? Se não, o campo passa a ser INFORMADO e a tela precisa liberá-lo;
2. o service pode continuar rodando sem apagar o que já existe?

Atribuição de sincronização é `campo = novo ?? campo`, nunca `campo = novo`, sempre que o "novo"
puder legitimamente vir `null`. Ausência de fonte não é medição zero, e não é autorização para
apagar medição alheia.

**⚠️ Corolário**: campo desabilitado na tela é uma AFIRMAÇÃO — "isto vem de outro lugar". Quando esse
outro lugar deixa de existir, o `disabled` vira mentira, e mentira em `disabled` não dá erro: dá um
operador convencido de que o sistema está quebrado.

**Automatizável?**: **parcialmente**. Delegável ao `verifier`: numa entrega que remove tela, etapa ou
enum, listar os `services/` que citam o termo removido e cobrar decisão explícita sobre cada um —
uma spec "só tela" que deixa service escrevendo com base no que sumiu não é "só tela". O julgamento
de o campo virar informado ou continuar derivado é humano e sai da ficha de papel (aqui, a FR71 diz
`Volume (mL): informado` / `Conc. p/ml: informado` no bloco TESTE DESCONGELAMENTO).

---

### [BE-031] `orderBy` com expressão SQL quebra em query paginada com join — usar `addSelect` + alias

**Contexto**: reportado pelo usuário em produção (2026-09-03), ao pesquisar/ordenar a listagem de
Perguntas do questionário do doador. Achado o mesmo padrão, ainda não disparado na prática, em
mais 3 repositórios do módulo `donors` (`donors_answers`, `donors_reviews_items`,
`donors_questions_options`).

**O erro**: `Internal server error. "LOWER(dq" alias was not found. Maybe you forgot to join it?`
— apesar de o alias `dq` estar corretamente joinado na mesma query. Não é erro de join faltando.

**Causa raiz**: `TypeOrmQueryBuilder.getMany()`, quando a query tem `.take()`/`.skip()` **e**
pelo menos um join, entra num modo interno de paginação que separa a query em duas etapas
(`createOrderByCombinedWithSelectExpression`, em
`node_modules/typeorm/query-builder/SelectQueryBuilder.js`). Esse modo faz
`orderCriteria.split('.')` para resolver o `orderBy` contra um alias já joinado — o que funciona
para uma referência de coluna (`'dq.order_index'`), mas quebra para uma EXPRESSÃO SQL
(`'LOWER(dq.title)'`), porque o split devolve `"LOWER(dq"` como se fosse o nome do alias.

**Onde aparece**: qualquer `.orderBy(<expressão com função>, ...)` (`LOWER(...)`, `COALESCE(...)`,
etc.) numa query que também tenha `.take()`/`.skip()` (paginação server-side, praticamente toda
listagem do projeto) **e** pelo menos um `leftJoin`/`leftJoinAndSelect`. Ocorreu com
`sort_field_data = 'LOWER(dq.title)'`/`'LOWER(dqo.label)'`/`'LOWER(dri.decision)'` em
`DonorQuestionRepository.findAllDonorsQuestions`, `DonorAnswerRepository.findAllDonorsAnswers`,
`DonorReviewItemRepository.findAllDonorsReviewsItems` e
`DonorQuestionOptionRepository.findAllDonorsQuestionOptions` — todos com o padrão comum do
projeto de ordenação case-insensitive por texto (`sort_field === 'title'` etc.).

**Regra correta**: nunca passar uma expressão SQL direto pro `orderBy` de uma query
paginada+joinada. Selecionar a expressão com um alias via `addSelect` e ordenar por esse alias
(sem ponto, o que usa outro caminho de resolução do TypeORM que não quebra):

```typescript
// ❌ quebra com "<expressão>" alias was not found, se houver join + take()/skip()
.orderBy('LOWER(dq.title)', sort_order, 'NULLS FIRST')

// ✅ funciona igual com ou sem join/paginação
.addSelect('LOWER(dq.title)', 'sort_value')
.orderBy('sort_value', sort_order, 'NULLS FIRST')
```

**⚠️ Segundo bug, achado só depois de rodar contra o banco de verdade**: o `addSelect` acima
**só pode ser condicional** — aplicá-lo também quando `sort_field_data` já é uma referência de
coluna PLANA (sem função, ex.: `'dq.order_index'`, o valor-padrão de `sort_field_data` em todo
repositório com esse padrão) reintroduz o problema de outro jeito: `Internal server error. column
reference "sort_value" is ambiguous`. Causa: essa mesma coluna JÁ é selecionada automaticamente
pelo `leftJoinAndSelect` da entidade principal; um segundo `addSelect` com o MESMO texto de seleção
(`'dq.order_index'`) não cria uma coluna nova — o TypeORM funde as duas entradas de seleção, e o
SQL final acaba com a coluna `dq.order_index` projetada **duas vezes**, as duas com o alias
`"sort_value"` (uma no lugar de `"dq_order_index"`, outra na posição do `addSelect`) — daí a
ambiguidade que o Postgres recusa. A referência de coluna plana **já funcionava sozinha** antes de
qualquer contorno (só a expressão com função quebra a resolução de alias do TypeORM) — então o
`addSelect` deve ser condicionado a `sort_field_data.includes('(')`:

```typescript
const isExpression = sort_field_data.includes('(')
const queryBuilder = this.ormRepository.createQueryBuilder('dq')
  .leftJoinAndSelect('dq.donorquestionoption', 'dqo')

if (isExpression) {
  queryBuilder.addSelect(sort_field_data, 'sort_value')
}

// ...where/andWhere...

queryBuilder.orderBy(
  isExpression ? 'sort_value' : sort_field_data,
  sort_order,
  'NULLS FIRST',
)
```

**Por que passa despercebido (as duas vezes)**: só reproduz com uma query REAL contra o banco
(join + paginação + expressão OU coluna repetida), que é exatamente o que os testes deste projeto
não fazem — services são testados com o repositório mockado (`jest.fn()`), então a query nunca
roda de verdade. `tsc`/ESLint não têm opinião sobre SQL gerado em runtime. **Verificação usada
para confirmar o fix desta vez**: conectar direto no Postgres remoto de dev via `tsx` (sem
depender do container Docker — `DB_HOST` do `.env` é um host de rede, alcançável por TCP direto do
WSL) e chamar o método do repositório para cada combinação de `sort_field`/`sort_order`/página,
capturando `err.query` de um `QueryFailedError` (TypeORM anexa o SQL que falhou de verdade nessa
propriedade) — mais confiável do que ler o código-fonte do TypeORM e prever o comportamento.

**Automatizável?**: parcialmente. Promovível a um guard do `verifier`: ao auditar um método de
`findAll*` que usa `.take()/.skip()` e algum join, conferir se `sort_field_data`/equivalente
contém uma expressão com parênteses (`LOWER(`, `COALESCE(`, etc.) passada direto ao `.orderBy()` —
se sim, cobrar `addSelect` condicional + alias no lugar, e cobrar que o `addSelect` NÃO rode para
os ramos de coluna plana do mesmo `sort_field_data`. Um teste de integração contra Postgres real
pegaria os dois lados automaticamente, mas o projeto não tem essa camada hoje.

---

### [BE-032] Backfill que funde duas colunas tem de checar se o destino já contém a origem

**Contexto**: sessão de 21/09/2026, migration `1788500000008-AlterTableUsersDropLastName`. O
cadastro de usuário estourava com `null value in column "last_name" violates not-null constraint`:
o contrato inteiro (rota Joi, DTO, service, repositório, formulário) já só trafegava `first_name`,
mas a coluna continuava `NOT NULL` no Postgres. A correção é derrubar a coluna — e, antes disso,
não perder o sobrenome de quem já estava cadastrado.

**O erro**: o backfill concatenou incondicionalmente.

```sql
-- ❌ NÃO COPIAR
UPDATE "users"
   SET "first_name" = btrim(concat_ws(' ', nullif(btrim("first_name"), ''), btrim("last_name")))
 WHERE nullif(btrim("last_name"), '') IS NOT NULL
```

Resultado medido em dev: `Letícia Schmidt Arruda` + `Arruda` virou **`Letícia Schmidt Arruda
Arruda`**, em 2 dos 4 registros. A premissa "`first_name` é só o primeiro nome" era falsa: **o
formulário só tem um campo há tempos**, então toda edição de usuário gravava o nome completo em
`first_name` e deixava o `last_name` antigo para trás. Metade da base já estava consolidada, e o
`UPDATE` duplicou o sufixo nela.

**A regra**: numa fusão de colunas, a coluna de destino **já pode conter a de origem** — o campo
que o formulário abandonou continua sendo escrito em algum caminho, ou a consolidação já foi feita
à mão. Guarde a concatenação por sufixo:

```sql
-- ✅
 WHERE nullif(btrim("last_name"), '') IS NOT NULL
   AND right(lower(btrim("first_name")), length(btrim("last_name"))) <> lower(btrim("last_name"))
```

`lower` porque a duplicidade é do dado, não da caixa. A heurística tem um falso negativo aceito e
documentado (sobrenome que seja sufixo por coincidência — `"Ana"` + `"na"`); o que não se aceita é
o falso positivo, que corrompe o nome de todo mundo.

**Por que passou pelo gate**: passou por tudo. `tsc`, ESLint e Jest não têm opinião sobre o
conteúdo de um `UPDATE`, e não há teste de integração contra Postgres neste projeto (BE-013). O
defeito só apareceu porque, **depois de `migration:run`, o resultado foi conferido no banco** com
`yarn typeorm:cli -d src/shared/infra/typeorm/dataSource.ts query "SELECT …"`. Sem esse `SELECT` a
migration teria ido para o repositório com o dado corrompido e o cabeçalho afirmando o contrário.

⚠️ **E o conserto não é reexecutar.** O `down` desta migration é lossy: ele devolve `last_name`
como `''`, e um segundo `up` pula a linha pela guarda de vazio — o nome duplicado **fica**. Foi
preciso `migration:revert`, **restaurar os 4 registros à mão** ao par original e só então rodar a
versão corrigida. Migration de fusão só é reversível para o estado anterior enquanto o dado
original ainda existe em algum lugar; depois do primeiro `up`, não existe mais.

**Automatizável?**: parcialmente, e a parte que vale é a de processo.

- **Promovível ao `verifier`** (guarda de leitura, não de hook): migration cujo `up` tem um
  `UPDATE` com `concat_ws`/`||` entre duas colunas da mesma tabela **seguido de `dropColumn`** deve
  ter, no `WHERE`, uma comparação entre destino e origem (`right(`, `NOT LIKE`, `position(`).
  Sem ela, cobrar justificativa escrita de por que a duplicação é impossível naquela tabela.
- **Não promovível a hook**: exige entender que as duas colunas se fundem, o que é semântica do
  domínio, não forma do arquivo.
- **Regra manual que fica**: toda migration com backfill é seguida de um `SELECT` de conferência
  no banco de dev, e o resultado vai no relatório ao usuário. "A migration rodou sem erro" não é
  evidência de que o dado ficou certo.
