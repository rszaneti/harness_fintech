# Harness — Plataforma de Pagamentos (BTG BaaS)

> **Versão atual do harness: v1.0-clone** (23/10/2026, spec `001-harness-pagamentos-adaptacao`).
>
> Este arquivo é a memória do **processo**, não do produto: de onde o harness veio, o que ele deve
> e o que mudou nele. Contexto de negócio está nos documentos `00`–`06` desta pasta.
> Mudança estrutural no harness (hook, gate, scaffold, agente, skill) ganha uma linha no histórico
> no fim deste arquivo, na mesma feature que a faz.

---

## Origem

O harness é um fork do harness do ERP Vida Fértil — repositório `rszaneti/harness_vidafertil`,
commit `0c878b7` ("V1.0"), que estava na **v2.3-F7** daquele projeto: seis fases de evolução
(F0–F6, specs 084–089) e a spec 090, executadas e pilotadas entre 10 e 14/09/2026.

O **roteiro F0–F7**, as medições de cada fase e o histórico até a v2.3-F7 **não foram trazidos**:
descrevem o ERP (176 módulos, 56 specs em andamento, pilotos nas specs 062 e 074) e não valem como
estado deste projeto. Continuam legíveis na origem:

```bash
git -C <clone de harness_vidafertil> show 0c878b7:documentacao/HARNESS.md
```

O que veio junto, e vale integralmente aqui: SDD em 3 camadas, os hooks, o gate com evidência, o
`verifier` independente, a hierarquia de fontes, os agentes por papel, o scaffold e as **87
lessons** (mantidas inteiras — ver `.claude/lessons/README.md`, seção "Origem").

---

## Princípios herdados

São regras de processo que o ERP aprendeu caro, não roteiro:

- **Instrução não garante qualidade; verificação garante.** Regra que cabe em script vira script
  (política de promoção das lessons); texto fica para o que exige julgamento.
- **Hierarquia de fontes**: hook/gate > lessons > skill + scaffold > `CLAUDE.md` do workspace >
  spec/plan. A skill nasce antes do erro; o hook, depois. Skill no topo aprovaria o que o hook
  reprova.
- **SDD em 3 camadas** e o **gate humano do `/finish-task`**: só o usuário conclui uma feature.
- **Quem implementa não se auto-aprova**: o `verifier` nunca é filho de quem ele audita.
- **Commits separados**: a raiz rastreia só o harness e a documentação; cada workspace tem `.git`
  próprio.
- **Não fazer**: fan-out de agentes escrevendo código em paralelo; dividir um módulo por camada
  entre agentes; dois escritores na mesma tela; skill acima do hook; editar `.ts/.tsx` por `sed`.
- **Método** (os dois movimentos que fecharam a spec 090 do ERP): (1) **juntar achados que rimam**
  — três achados que cabem na mesma frase pedem o predicado, não a terceira correção; (2) **mutar a
  guarda, não exercitá-la** — "passa nos casos" não prova que a guarda faz algo; remover a guarda e
  ver o self-test reprovar prova. Os self-tests dos hooks financeiros conferem a **linha** de
  cada achado (`@acusa`), e a 001 validou os detectores com 14 mutações, todas mortas

---

## Dívidas vigentes

| Dívida | Origem | Estado |
|---|---|---|
| **O gate não alcançava o harness** — `.py`, `.sh` e `.md` passavam sem lint, typecheck ou teste; todos os defeitos ALTA das fases F4, F5 e F7 do ERP estavam em arquivos que nenhum gate lia | ERP, spec 087 | **Parcialmente fechada** pela spec 001: `verify.sh harness` roda `bash -n`, compilação de todo `.py`, todos os `--self-test` e as fixtures dos hooks, com evidência em `.claude/gate/`. Continua aberto: `.md` não tem verificação (prosa de agente/skill/comando só é conferida pelo `verifier`), e não há lint de Python/Shell |
| **Escopo que casa 0 suítes passa verde** (`--passWithNoTests`) — um escopo pode ficar verde sem ter rodado nada | ERP, spec 090 | Aberta. Forma certa: reprovar quando o escopo casa 0 suítes **e** há `.ts` daquele módulo no diff. Gatilho: primeiro módulo do `backend/api` |
| **Rename over-acusa** no check `v1-import` do `check-module.py` | ERP, spec 090 | Aberta e de baixa prioridade: só afeta telas v1, que não existem neste projeto. Fechar quando a revisão do padrão visual (specs 010/011) decidir o destino do check |
| **`--self-test` completo do perfil `--append-only`** (compilar, lint, jest dentro do workspace) | spec 001, RN-10 | Aberta. Sem `backend/api`, a prova é o `--self-test static`. Vira critério de aceite da primeira spec que criar o workspace (a 002 registra a questão) |
| **`ensureIdempotency` é importado e não existe** — todo módulo gerado depois da 001 importa `@shared/infra/http/middlewares/ensureIdempotency` | spec 001, plan 2.8.3 | Aberta, de propósito: falha alta e cedo. A spec 002 registra quem cria o middleware |
| **Ramo "hook financeiro não rodou"** do `post-edit-check.sh` | spec 001, T-08 | **Fechada na 001** (correção da 1ª auditoria): biblioteca que não carrega ou regra que quebra sai **3**, não 1, e o hook pós-edição a reporta como "NÃO RODOU". Sondado em cópia do harness com `workspaces.json` corrompido: hook pós-edição 2, `block-shell-write-ts` 2, hook financeiro 3 |
| **Limites declarados dos hooks financeiros** — o que eles sabidamente NÃO pegam | spec 001, 1ª auditoria | Aceitos, com o `verifier` (check `financeiro`) como segunda barreira: segredo **só de letras** (sem dígito) passa; `type: 'real'`/`'money'` fora de coluna, em contexto financeiro, é acusado (falso positivo); `.delete(` de `Map`/`Set` e `.toFixed(` de log são acusados (reescrever a linha); `--append-only --sem-migration` é aceito e a trigger fica por conta do `check-module.py` |
| **Resíduos da 3ª auditoria da 001** (BAIXA, aprovados como não bloqueantes) | spec 001, T-21 | Abertos: (1) mensagem que termina em "TRUNCATE <palavra>" e fecha a aspa ainda é acusada pela RN-12, e `TRUNCATE a, b` / `TRUNCATE ONLY a` passam (a trigger cobre no banco); (2) o diretório-caso `<x>-acusa/` das fixtures pode deixar de ser visto sem o self-test reprovar — falta contagem mínima por caso; (3) `r.use(ensureIdempotency)` seguido de `r.route('/').post(...)` é acusado (falha fechada consciente: middleware na própria rota) |
| **`check-ui-v2-refs.py` sem alvo** — o padrão v2 aponta para `frontend/operador`, que não existe; o script sai 65 (não rodou) | spec 001 | Aberta até as specs 010/011 |

---

## Histórico de versões do harness

> Uma linha por mudança estrutural, com a data real e o que ficou diferente do planejado.

| Data | Versão | Mudança | Spec |
|---|---|---|---|
| 23/10/2026 | **v1.0-clone** | **Harness adaptado do ERP Vida Fértil para a plataforma de pagamentos.** (1) **Uma fonte para os workspaces**: `.claude/workspaces.json` + `workspaces.py` substituem sete listas fixas (gate, hook, scaffold, `check-module`, `diff-classify`, `check-ui-v2-refs`, `block-shell-write-ts`) que já divergiam; `--scan` reprova executável do harness que cite workspace fora do JSON. (2) **`verify.sh` v2.1**: alvos `backend`/`operador`/`cliente`/`simulator`/`frontend`/`harness`/`all`; o alvo `harness` é o "comando único" das provas que substituem lint/tsc/jest no harness, com evidência; base = árvore vazia em repositório sem commit. (3) **Quatro hooks financeiros** (`money-bigint`, `ledger-immutable`, `idempotency-required`, `no-secret-in-code`) sobre uma biblioteca única, `financial_rules.py`, que o `check-module.py` (check `financeiro`) também usa; isenção de idempotência só por marcador com motivo; self-test de cada hook confere a linha exata de cada achado. (4) **Perfil `--append-only`** no scaffold, por diretiva nos templates existentes (sem template novo), com trigger `reject_mutation()` contra `UPDATE`/`DELETE`/`TRUNCATE`; o scaffold recusa os módulos append-only sem a flag; `--self-test static` prova o gerador sem workspace e roda os 4 hooks sobre o que ele gera. (5) Skill `backend-module` com "Regras financeiras"; `verifier-checks/financeiro.md`; `CLAUDE.md` raiz, `documentacao/` e este arquivo reescritos; lessons mantidas inteiras. **Desvios do plan**: as fixtures dos hooks (`.claude/scripts/tests/`, e só elas) não contam como workspace — são mini-workspaces que o hook reprovaria; o módulo "corrigido" do self-test do `check-module` é gerado na hora pelo scaffold, não versionado; o hash do alvo `harness` não cobre as pastas de estado das specs. **1ª auditoria REPROVADA** (1 ALTA: segredo em comentário passava, porque o plan mandava filtrar comentário em todas as regras e a RN-14 não abre essa exceção — venceu a spec) e corrigida: RN-14 sobre o texto cru; self-test dos hooks confere a **linha** de cada achado (`@acusa`) em vez da sonda "regra desligada", que era só `n_acusa > 0`; 14 mutações dos detectores, todas mortas; furos da RN-12 (SQL minúsculo, `.clear`, `.orUpdate`), HMAC em dois passos, isenção por router, marcador sem `:`, `routes/index.ts`, JSON corrompido sem silêncio, modo pasta do `check-module` lendo a migration | 001 |
