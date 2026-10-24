# Tasks: Adaptação do harness para a plataforma de pagamentos

> **Camada 3 de 3 (SDD)** — passos de execução derivados de `plan.md`.
> Tasks são **descartáveis e regeneráveis**: se o plan mudar, regenerar este arquivo.
> **Plan de origem**: `./plan.md` (status `aprovado` em 2026-10-23)
>
> **Regras de execução:**
> 1. Executar na ordem. Marcar `[x]` IMEDIATAMENTE ao concluir cada task — nunca em lote no final.
> 2. Cada task termina com sua verificação passando. Task sem verificação aprovada = task não concluída.
> 3. Se pausar/retomar (mesma sessão ou outra): ler este arquivo primeiro e NÃO refazer o que está `[x]`.
> 4. O gate final (`verify.sh`) é obrigatório antes de mover a feature para `concluido`.
>
> **Feature de harness** (spec 088 §2.1): executada pela sessão principal, sem leads. O hook
> pós-edição não lê `.py`/`.sh`/`.md` — até a T-03 existir, a prova de cada edição é `bash -n`,
> `py_compile` e `--self-test` rodados à mão (AG-019, AG-025).

---

## Fase 0 — Preparação

- [x] **T-01** Linha de base: `sha256sum` de `lessons/{backend,frontend,agents}.md` registrado no
      "Registro de execução" (CA-05), e a contagem de menções aos caminhos do ERP por arquivo
      (plan 2.8.1)
  - Verificação: as 3 somas e a contagem estão no registro

## Fase 1 — Harness mecânico

- [x] **T-02** `.claude/workspaces.json` + `.claude/scripts/workspaces.py` (`load()`, `--path <ws>`,
      `--which <arquivo>`, `--list`, `--self-test`) — plan 2.8.1
  - Verificação: `python3 .claude/scripts/workspaces.py --self-test` sai 0; `--which` de um caminho
    `…/backend/api/src/x.ts` devolve `backend`, e de `…/frontend/admin/src/x.ts` devolve vazio
- [x] **T-03** `verify.sh`: `ws_dir` lido do JSON; alvos `backend|frontend|operador|cliente|simulator|harness|all`;
      `diff_hash` com a lista de caminhos por alvo; base = árvore vazia quando não há `HEAD`; alvo
      `harness` com as etapas 1–7 da 2.8.5 (as que dependem de peça ainda não feita entram nas
      tasks que as criam)
  - Verificação: `bash -n verify.sh`; `verify.sh all` sem workspaces sai 0 com 4 avisos;
    `verify.sh harness` sai 0 com as etapas existentes; `--check-evidence x harness` sai 4 (ausente)
- [x] **T-04** `post-edit-check.sh`: detecção de workspace via `workspaces.py --which`;
      `block-shell-write-ts.py`: `WORKSPACES` do JSON, casos do `--self-test` com os caminhos novos
  - Verificação: `bash -n`; `block-shell-write-ts.py --self-test` sai 0; sonda: JSON de Edit
    apontando para `.ts` em `<scratch>/backend/api/src/…` passa pelo hook sem erro de detecção
- [x] **T-05** `scaffold.py`, `check-module.py`, `diff-classify.py`, `check-ui-v2-refs.py`: `WS` do
      JSON; scaffold `frontend --ws operador|cliente`; `Generator` com `ws` alternativo; condição
      negada (`!flag`) em `BACKEND_DEST` com avaliador único usado também por inventário e
      completude
  - Verificação: `py_compile` dos 4; `scaffold.py --list-placeholders` sai 0;
    `check-module.py --self-test` sai 0
- [x] **T-06** `hooks/financial_rules.py` + `money-bigint.py`, `ledger-immutable.py`,
      `idempotency-required.py`, `no-secret-in-code.py`, com fixtures `*-acusa.*`/`*-limpo.*` em
      `.claude/scripts/tests/<hook>/` no idioma real do template (rota multilinha) — plan 2.8.4
  - Verificação: `--self-test` de cada um sai 0; fixtures do CA-11 presentes
    (`patch-sem-middleware-acusa`, `isencao-com-motivo-limpo`, `isencao-sem-motivo-acusa`); cada
    hook, apontado para o próprio arquivo de fixture `-acusa` **com a regra desligada** (sonda de
    não-acerto, AG-020), falharia o self-test — anotado no registro
- [x] **T-07** Perfil `--append-only`: flag, guarda dos `APPEND_ONLY_MODULES`, incompatibilidade com
      `--no-table`, diretivas nos 10 templates, `ensureIdempotency` nas rotas de escrita dos dois
      perfis, `--self-test static` com as invariantes (a)–(g) — plan 2.8.3
  - Verificação: `scaffold.py --self-test static` sai 0; `scaffold.py backend ledger x X --dry-run`
    (sem a flag) sai 64; `--append-only --no-table` sai 64; `--list-placeholders` sai 0
- [x] **T-08** `post-edit-check.sh` chama os 4 hooks financeiros para `.ts` de workspace; `verify.sh
      harness` ganha as etapas 4, 6 e 7 completas
  - Verificação: sonda com `.ts` violador em `<scratch>/backend/api/src/modules/ledger/…` → hook
    sai 2 com o código da regra; versão limpa → sai 0; `verify.sh harness` sai 0
- [x] **T-09** `check-module.py`: check `financeiro` + completude append-only + casos em
      `tests/check-module-financeiro/` (violador e corrigido); `diff-classify.py`: etiqueta
      `financeiro`; `verifier-checks/financeiro.md` — plan 2.8.6
  - Verificação: `check-module.py --self-test` sai 0 com os casos novos (`acusa` e `limpo`);
    `diff-classify.py --list-tags` sai 0
- [x] **T-10** Skill `backend-module`: seção "Regras financeiras"; linha "Tipos" sem
      `decimal→numeric` para dinheiro
  - Verificação: `grep -n "decimal→\`numeric\`" SKILL.md` vazio; seção presente

## Fase 2 — Documentação e estado

- [x] **T-11** Prosa dos workspaces (RN-08): agentes, comandos, skills (`ui-v2` + nota de herança),
      `verifier-checks/tela.md`, `specs/README.md`, `sprints/_template.md`; `finish-task.md`,
      `sprint-close.md` e `verifier.md` com o alvo `harness`
  - Verificação: CA-08 — `grep -rnE "backend/admin|frontend/admin|frontend/portal|frontend/professional" .claude --include=*.md`
    excluindo `lessons/`, `_backup_*` e `specs/*/001-*`: vazio
- [x] **T-12** `.gitignore`: `tools/`, comentário sem ERP
  - Verificação: `git check-ignore tools/btg-simulator/x` devolve o caminho
- [x] **T-13** `documentacao/`: remover os 3 arquivos da RN-04; `00-README.md` com a linha do `HARNESS.md`
  - Verificação: CA-03 — `ls documentacao/` = documentos do índice + `HARNESS.md`
- [x] **T-14** `documentacao/HARNESS.md` reescrito (origem, dívidas vigentes, histórico `v1.0-clone`)
  - Verificação: `grep -c "^## F[0-7]" HARNESS.md` = 0; nota de origem e linha `v1.0-clone` presentes
- [x] **T-15** `lessons/README.md`: título e seção "Origem" com a correspondência de caminhos
  - Verificação: CA-05 — `sha256sum` dos 3 arquivos de lessons igual ao da T-01
- [x] **T-16** `CLAUDE.md` raiz reescrito — plan 2.8.7
  - Verificação: CA-01 — `grep -niE "clínica|clinica|doador|donor|tentante|especialista|backend/admin|frontend/admin|portal|professional" CLAUDE.md`
    vazio; as 3 regras novas presentes; CA-02 — script confere cada `planejado — spec NNN`
- [x] **T-17** Specs `002-auth-jwks-httponly` e `003-ledger-core` em `a_fazer/`, só `spec.md`, `rascunho` — plan 2.8.8
  - Verificação: CA-14 — só `spec.md` em cada pasta; 003 com 8 CA `[auto]` das invariantes; 002
    com as 3 questões em aberto
- [x] **T-18** Zerar estado do ERP: remover `.claude/gate/*.json` (65)
  - Verificação: CA-15 — `ls -a .claude/gate/` = `.gitkeep`; `ls .claude/specs/*/` = só 001/002/003

### ⚠️ Obrigatória quando a feature REMOVE algo (AG-017)

- [x] **T-RM** Conferir as remoções por **grep do termo VELHO** no harness inteiro: caminhos do ERP
      (`backend/admin`, `frontend/admin`, `portal`, `professional`), `WS = {` fixo, `spec 032` como
      justificativa de workspace ausente, `decimal→numeric`, `GetPostalCodeProvider`, `jwtTentant`.
      Cada ocorrência classificada como (a) legítima, (b) comentário histórico honesto ou (c) defeito.
  - Verificação: nenhuma na categoria (c), lista no registro

---

## Fase 3 — Gate de conclusão

- [x] **T-19** **GATE**: `bash .claude/scripts/verify.sh harness --feature 001-harness-pagamentos-adaptacao` ✅
      (gera `.claude/gate/001-harness-pagamentos-adaptacao.harness.json`; exit code lido direto, AG-012)
- [x] **T-20** **GATE**: `bash .claude/scripts/verify.sh all` sem workspaces → exit 0, 4 avisos (CA-07)
- [x] **T-21** Subagente `verifier` rodou auditoria (diff do harness, etiquetas `harness` e
      `financeiro`) e aprovou
- [x] **T-22** Commit inicial na raiz **com autorização explícita do usuário**; `git status` limpo (CA-16)
- [x] **T-23** Critérios de aceite `[humano]` (CA-04, CA-13, CA-16, CA-17) validados pelo usuário via `/finish-task`

---

## Registro de execução

> Anotar aqui desvios do plan, erros encontrados e lições candidatas a `.claude/lessons/`.

| Data | Task | Observação |
|------|------|------------|
| 2026-10-23 | T-01 | Linha de base. sha256: backend.md 129e3248…2600 · frontend.md 3618a0e7…b9da · agents.md 043fa7ee…84b. Menções aos caminhos do ERP: 32 arquivos, contagem na tabela do plan 2.8.1 (block-shell-write-ts.py 35, post-edit-check.sh 9, …) |
| 2026-10-23 | T-02 | workspaces.json + workspaces.py. --self-test rc=0. A varredura do CA-06 ficou num modo separado, --scan: ela acusa 73 citações nos executáveis, que as T-03 a T-05 corrigem, e reprovaria a T-02 por trabalho de tasks futuras. As sondas negativas montam os caminhos do ERP por partes, senão o próprio --scan as acusaria. Durante a medição, um `| tail` mascarou o rc do self-test (AG-012); a partir daqui o rc é lido sem pipe. |
| 2026-10-23 | T-03 | verify.sh v2.1. Alvos vêm do workspaces.json, há o alvo harness e a base sem commit vira a árvore vazia. Medido: `all` sem workspaces dá rc=0 com 4 avisos; harness rc=0 com 8 etapas; --check-evidence de feature inexistente dá 4. Sonda de hash: evidência gravada e conferida dá 0, editar um .md do harness dá 3 e reverter volta a 0. Assim a gravação da evidência não altera o próprio hash. As etapas de scaffold static, hooks financeiros e --scan entram nas T-07 e T-08, não como etapa condicional. |
| 2026-10-23 | T-04 | post-edit-check.sh detecta o workspace por workspaces.py --which-dir (novo modo). block-shell-write-ts.py lê WORKSPACES do JSON e ganhou 3 casos: cliente e simulator barram, caminho do ERP libera. --self-test rc=0. Sonda no hook com .ts em <scratch>/backend/api/src: arquivo limpo rc=0, arquivo com BE-023 rc=2, WS resolvido no trace. Comentários históricos sem caminho literal do ERP; o conteúdo foi reescrito para "no ERP de origem…". |
| 2026-10-23 | T-05 | scaffold.py, check-module.py, diff-classify.py e check-ui-v2-refs.py leem o workspaces.json. O scaffold tem `frontend --ws` obrigatório, Generator(ws=…) e cond_ok() como avaliador único, usado também na completude do check-module. Medido: compilação dos 4 ok, --list-placeholders 0, check-module --self-test 0, verify.sh harness 0, `frontend` sem --ws dá erro de uso. Defeito pré-existente corrigido: o --self-test completo dava traceback quando o workspace não existia, porque o git_dirty rodava num cwd inexistente; agora reporta "não rodou" (exit 5). check-ui-v2-refs sem o workspace operador sai 65, não 0 (AG-019). check_contrato e check_joi_payload rodam por frontend do JSON. |
| 2026-10-23 | T-06 | financial_rules.py + 4 entradas finas. São 32 fixtures em mini-workspaces dentro de tests/<hook>/: money 6 acusa/4 limpo, immutable 3/4, idempotency 4/5, secret 5/1. Cada acusa foi conferida pelo motivo e pela linha certos. A sonda de não-acerto (AG-020) é automática no --self-test: com a regra desligada, ele reprova os N casos acusa. Idioma real coberto: rota multilinha com celebrate aninhado, use() antes e depois da rota, createHmac().update() em cadeia multilinha (não é escrita em banco), antipadrão citado em comentário. Ajuste fora do plan: workspaces.which e block-shell-write-ts tratam caminho dentro de /.claude/ como não-workspace; sem isso o hook pós-edição reprovaria as fixtures a cada gravação. As fixtures foram gravadas por script Python (shell liberado em .claude/) e depois passadas uma a uma pelo post-edit-check.sh: 32/32 sem reprovação (AG-025). |
| 2026-10-23 | T-07 | Perfil --append-only por diretiva nos 10 templates, com ensureIdempotency no POST/PUT dos dois perfis e a guarda append_only_guard(). --self-test static gera 4 variações (23/18/17/9 arquivos) e 2 migrations em dry-run, confere as invariantes (a)–(g) e roda os 4 hooks sobre o gerado: rc=0. Sondas de não-acerto: 3 mutações nos templates (POST sem ensureIdempotency, save( no repositório append-only, trigger TRUNCATE removida) dão rc=5, cada uma pela invariante certa; templates restaurados (cmp). CLI lido sem pipe: ledger sem a flag 64, --append-only --no-table 64, ledger com a flag 0, split_rules sem a flag 0. Dois deslizes meus: uma leitura de rc via `| tail` (AG-012) e um comando com `rm -rf` barrado pelo deny; ambos refeitos. |
| 2026-10-23 | T-08 | post-edit-check.sh roda os 4 hooks financeiros para .ts de workspace. Exit 1 vira achado com o código da RN; qualquer outro exit vira "hook NÃO RODOU", que também reprova. Sonda em <scratch>/backend/api/src/modules/ledger/…: repositório com save( dá rc=2 [RN-12] linha 3; repositório com insert dá rc=0; rota PATCH sem middleware dá rc=2 [RN-13]. O ramo "hook não rodou" não foi sondado (exigiria quebrar um hook de propósito). verify.sh harness tem agora 14 etapas, todas ✅, incluindo --scan, --self-test static e os 4 hooks. Desvio: o --scan acusava 3 falsos positivos (`templates/backend/migration.ts.tpl`); o detector passou a ignorar caminho seguido de extensão ou sob templates/, e o self-test do workspaces.py ganhou as sondas de acerto e de não-acerto do próprio scan. |
| 2026-10-23 | T-09 | check-module.py tem o check financeiro, que roda as mesmas 4 regras da financial_rules, e check_append_only (papéis Update/Delete proibidos + migration sem reject_mutation, código RN-09). --self-test com os casos novos, rc=0: o módulo corrigido sai limpo e as 5 mutações, uma por vez, dão RN-11, RN-12, RN-13, RN-09 e RN-09. Desvio do plan: o módulo corrigido NÃO é fixture versionada. Ele é gerado na hora pelo scaffold, para não divergir do template, e em tests/check-module-financeiro/ ficam só as mutações (mutations.json). diff-classify ganhou a etiqueta financeiro (contexto financeiro/append-only ou marcador adicionado); --list-tags reprovou até existir o verifier-checks/financeiro.md e agora sai 0. Gate harness 0. |
| 2026-10-23 | T-10 | Seção "Regras financeiras" (9 situações × decisão × quem verifica) entre "Decisões" e "Regras por camada". As regras mecânicas não estão repetidas na seção, que aponta para financial_rules.py. Linha Tipos sem `decimal→numeric` (grep vazio, rc=1). Controller e Routes de "Regras por camada" citam o perfil append-only e o ensureIdempotency; o uso do scaffold mostra --append-only. A representação TS do bigint ficou marcada como decisão da spec 003. |
| 2026-10-23 | T-11 | Troca em 22 arquivos de prosa: backend/admin vira backend/api; frontend/admin vira frontend/operador na ui-v2 (onde o check-ui-v2-refs procura) e frontend/<ws> no resto, com definição de <ws> nos agentes e na skill. sprint-close percorre os workspaces via workspaces.py e fecha também `harness --full`; o template de sprint tem as 4 linhas + harness. verifier.md e finish-task: --check-evidence com chave do JSON ou `harness`, porque `frontend` é grupo e não tem evidência. scaffold --ws em 4 usos de prosa, e o README do scaffold documenta --append-only e static. Fora da letra da RN-08, mas consistente: as descrições das 3 skills deixam de dizer "ERP Vida Fertil", e a ui-v2 ganhou a nota de herança. CA-08 grep rc=1 (vazio); "portal" restante = portal do React (legítimo). Gate harness 0. |
| 2026-10-23 | T-12 | .gitignore ganhou tools/ e *:Zone.Identifier (o resto de download que a RN-04 remove não volta); comentários sem referência ao roteiro F0 do ERP. git check-ignore de tools/btg-simulator/x casa na linha 7 (rc=0). |
| 2026-10-23 | T-13 | Removidos o Roteiro-MVP-…-BaaS.md (versão anterior do 02), o Ui_Ux/PADRAO-UI-V2.md (74 KB, padrão visual do ERP; o vigente está na skill ui-v2) e o HARNESS.md:Zone.Identifier; a pasta Ui_Ux saiu vazia. 00-README ganhou a linha do HARNESS.md (sem número: é memória de processo, não negócio). CA-03 conferido por script: nenhum arquivo fora do índice e nenhum link do índice ausente. |
| 2026-10-23 | T-14 | HARNESS.md reescrito: origem (harness_vidafertil @ 0c878b7, v2.3-F7), princípios herdados (as regras de processo, não o roteiro), 7 dívidas vigentes (3 do ERP reavaliadas + 4 abertas pela 001) e histórico com a linha v1.0-clone. Verificação: grep "^## F[0-7]" = 0; nota de origem e v1.0-clone presentes. |
| 2026-10-23 | T-15 | lessons/README.md: título sem "ERP Vida Fertil", seção "Origem" com a nota da RN-06, a tabela de correspondência de caminhos e a regra de numeração de lessons novas (BE-033, FE-027, AG-030). CA-05: sha256 dos 3 arquivos de lessons idêntico à T-01 (129e3248…, 3618a0e7…, 043fa7ee…). DIVERGÊNCIA a reportar ao usuário: são 87 códigos únicos (32 BE, 26 FE, 29 AG), não os 79 que o documentacao/05 §1 cita (31+26+22). Corrigido no README e no HARNESS.md; o 05 não foi alterado, porque é documento de negócio do usuário. |
| 2026-10-23 | T-16 | CLAUDE.md raiz reescrito no mesmo esqueleto. Tem: produto/modelo 2, os 4 workspaces com coluna Estado, "um frontend por papel" (não por token), hierarquia com nível 4 vazio até o workspace nascer, regras críticas 8–12 (as 3 da RN-01 + segredo + modelo 2), módulos de 04 §4 × spec, providers como planejados. GetPostalCodeProvider saiu. CA-01: grep vazio (rc=1); as 3 regras novas presentes. CA-02: script (scratchpad/ca02.py) confere 23 menções "planejado — spec NNN" contra as pastas de specs e a sequência de 05 §5, rc=0 lido sem pipe. O 1º falso positivo (título de seção) foi corrigido restringindo a regra a linhas de tabela/árvore, com sonda de acerto. Decisões a reportar: api_keys atribuído à 002 (05 §5: "002 = chaves de API"), embora o 04 §4 o ponha no contexto platforms; audit_log sem spec na sequência do 05, marcado como 003 com questão aberta na 003. Terceira ocorrência de AG-012 (rc lido de `| tail`) nesta sessão. |
| 2026-10-23 | T-17 | Specs 002 e 003 em a_fazer/, só spec.md, status rascunho, com aviso de que nasceram sem a entrevista do /spec-new e não são aprováveis. 003: as 8 invariantes de 04 §5 como CA-01..08 [auto] (grep = 8); questões sobre a representação TS do bigint, audit_log e a fronteira de CA-07/08. 002: 4 questões abertas (cria o backend/api + self-test completo? quem cria ensureIdempotency? hook Joi sem unknown(true)? login/refresh isentos?). Uma a mais que o plan previa: a isenção de login/refresh. CA-02 continua rc=0 (audit_log → 003 rastreável). |
| 2026-10-23 | T-18 | Removidos os 65 .json de evidência do ERP (35 features/sprints, de 042-donor-* a sprint-2026-09-13; todos no .gitignore, não versionados). CA-15: gate/ = .gitkeep; specs/ = 001 (em_andamento), 002 e 003 (a_fazer), concluido e canceladas vazios, mais _templates/, _template.md (legado) e README.md. |
| 2026-10-23 | T-RM | Grep do termo VELHO em .claude/, CLAUDE.md e documentacao/ (fora lessons/, _backup_* e a própria 001). (a) Legítimas: documentacao/04 §2 cita jwtTentant/jwtProfessional ao descrever "como o harness faz hoje"; é documento de negócio do usuário e descreve a origem corretamente. (b) Comentários históricos honestos: workspaces.py:7 e :53 (descrevem as listas que existiam); post-edit-check.sh:121 e SKILL backend-module:194 (anedota da BE-022, agora com "no ERP de origem"). (c) Defeito encontrado e corrigido: agents/backend-builder.md:35 ainda listava o GetPostalCodeProvider, que saiu do CLAUDE.md; agora aponta para a lista vigente no CLAUDE.md raiz. Caminhos do ERP: 0. `WS = {` fixo: 0 (só a menção histórica). decimal→numeric: 0. Nenhuma ocorrência restante na categoria (c). |
| 2026-10-23 | T-19 | GATE: verify.sh harness --feature 001-harness-pagamentos-adaptacao, rc=0 lido direto, 14 etapas ✅, evidência .claude/gate/001-harness-pagamentos-adaptacao.harness.json com rc 0, missing []. Desvio: na 1ª rodada percebi que o hash do harness cobria .claude/specs/, e marcar esta task invalidaria a evidência recém-gravada. verify.sh passou a excluir .claude/specs/ do hash (como o hash dos workspaces) e o gate foi rodado de novo: rc=0, hash 4c4e9948. ⚠️ Depois do commit inicial (T-22) a base HEAD deixa de ser a árvore vazia e a evidência fica desatualizada; o gate tem de rodar de novo antes do /finish-task. |
| 2026-10-23 | T-20 | GATE: verify.sh all sem workspaces, rc=0 lido direto; 4 linhas "não existe neste checkout (nasce na spec NNN)" (backend 002, operador 010, cliente 011, simulator 004) + harness ✅ (CA-07). |
| 2026-10-23 | — | T-21, 1ª auditoria: REPROVADO. 1 ALTA: RN-14 sobre código sem comentário, então segredo comentado passa; o plan contradizia a spec e vence a spec. 8 MÉDIA: sonda "regra desligada" equivale a n_acusa>0; ramos sem fixture (float/real/money, .delete/.remove…, JWT); SQL minúsculo e .clear/.orUpdate na RN-12; HMAC em dois passos acusado; exclusão /.claude/ larga demais (worktree e TMPDIR); JSON corrompido silencia o hook; prosa com `check-module.py frontend`; modo pasta do check-module não vê a migration. Vários BAIXA. Correções na sequência abaixo; reauditoria obrigatória (AG-016). |
| 2026-10-23 | — | Correções da 1ª auditoria, parte 1 (hooks). ALTA: RN-14 roda sobre o texto cru, e a fixture comentario-acusa tem AKIA, PEM em bloco e clientSecret, todos comentados. O plan foi corrigido (2.8.4 e riscos), porque contradizia a spec. Self-test: a sonda "regra desligada" (= n_acusa>0) foi substituída por conferência de LINHA via marcador @acusa/@acusa-abaixo: 18 fixtures antigas marcadas + 11 novas, 46 linhas conferidas. Mutação: 14 alterações nos detectores, 14 mortas, arquivo restaurado (cmp). RN-12: SQL case-insensitive com forma de SQL, .clear, .orUpdate, HMAC em dois passos (variável de createHmac/createHash). RN-13: .use só vale para o mesmo router; marcador sem ":" reprova; a string ensureIdempotency não conta; routes/index.ts entra no escopo (sonda --as: index 1, outro 0). RN-11: *_cents por span balanceado (transformer) e int8 = bigint. RN-14: header kebab e caminho "/" não são segredo. Entradas dos hooks saem 3 quando a biblioteca não carrega. |
| 2026-10-23 | — | Correções da 1ª auditoria, parte 2. Exclusão de workspace restrita a /.claude/scripts/tests/: worktree em .claude/worktrees/ volta a ser workspace (self-test do workspaces.py e caso do block-shell). JSON corrompido, sondado em cópia: post-edit 2, block-shell 2 (falha fechada só para gravação de .ts), hook 3. protect-migrations ignora as fixtures. Static (g) reprova se o gerado cair fora do escopo (TMPDIR em fixtures dá rc=5) e a mensagem passou a dizer (a)–(g). check-module: o modo pasta inclui as migrations da tabela do módulo (files_for_folder), o self-test usa o mesmo caminho da CLI e ganhou o caso "numeric na MIGRATION" (RN-11). Prosa: check-module.py frontend → <operador|cliente> em 7 arquivos + commands/check-module.md (AG-017: o termo velho como chave da CLI escapou do grep do CA-08). diff-classify: harness acende para commands/, skills/ e workspaces.json; financeiro acende para migration de tabela financeira. O hash harness exclui só as pastas de estado das specs. Templates: comentários de delete e FK CASCADE sob diretiva no perfil append-only. CLAUDE.md: nota de que "padrão sem Delete" (04 §4) não existe no scaffold. sprints/_template e HARNESS.md atualizados. |
| 2026-10-23 | — | Correção da reauditoria (2ª rodada, REPROVADA por 1 ALTA). Regressão minha na RN-13: a regex com receptor obrigatório (para isentar só pelo mesmo router) deixou de VER router.route(...).post( e as cadeias. WRITE_ROUTE_RE volta a ver toda chamada; o receptor é lido à parte (_receptor) e só decide a isenção por .use, e sem receptor simples não há isenção. Fixture route-encadeada-acusa (3 formas) + route-com-middleware-limpo. BAIXA também corrigidos: truncate exige forma de SQL (mensagem com "TRUNCATE" é limpa); marcador sem ":" só quando abre o comentário; *_cents com @Index() no meio ou public/readonly; exemplo de FK RESTRICT no perfil append-only; caso como diretório (<caso>-acusa/) para o routes/index.ts. Fixtures para os 5 vivos da bateria do verifier (float4/float8 em SQL, int8, truncate, routes/index.ts, nome de env com dígito, fora de src/). Mutação: 12 de 12 mortas, incluindo a que reintroduz a regressão. Arquivo restaurado (cmp). |
| 2026-10-23 | T-21 | verifier: 1ª rodada REPROVADA (1 ALTA RN-14 + 8 MÉDIA), 2ª REPROVADA (1 ALTA: regressão minha na RN-13), 3ª APROVADA. Na 3ª: probes de rota encadeada acusados, 70 mutações com 67 mortas (as 3 vivas são 2 equivalentes/meta e 1 BAIXA), CA-01/06/08 vazios, lessons com o mesmo sha, evidência válida. Os 3 BAIXA restantes foram registrados em "Dívidas vigentes" do HARNESS.md; gate refeito com rc=0. A levar ao usuário no /finish-task: o plan.md foi editado depois de aprovado (2.8.4/riscos, para alinhar à RN-14 da spec). |
| 2026-10-23 | — | Preparação da T-22: achado ALTO antes do commit. O .gitignore tinha `backend/` e `frontend/` (herdados do ERP) e `tools/` (meu, T-12) SEM âncora. Isso ignorava em qualquer profundidade: .claude/scaffold/templates/{backend,frontend}/ e as fixtures dos hooks. O commit sairia com 98 arquivos e sem os templates do scaffold. git check-ignore confirmou 4 de 4. Corrigido para /backend/, /frontend/, /tools/: agora são 183 arquivos, e o cruzamento find × git status mostra fora só _backup_*, gate/*.json e settings.local.json. Os workspaces continuam ignorados (check-ignore rc=0). Gate harness refeito: rc=0. Nenhum gate ou auditoria pegava isso, porque o gate não olha o que o git rastreia; vale avaliar como lesson. |
| 2026-10-23 | T-22 | Commit inicial autorizado pelo usuário em 24/10/2026 (/finish-task). Feito com o estado final (feature já em concluido/), para o git status terminar limpo (CA-16). O gate harness é refeito depois do commit, porque a base deixa de ser a árvore vazia. |
| 2026-10-23 | T-23 | Usuário validou CA-04, CA-13 e CA-17 e confirmou a conclusão em 24/10/2026 (/finish-task). CA-16 é conferido logo após o commit. |
| 2026-10-23 | — | /finish-task, colheita de lições: das 4 candidatas, o usuário escolheu registrar só a do .gitignore sem âncora, como AG-030 em lessons/agents.md, com a linha "CANDIDATA → verify.sh harness" no README (a promoção fica para uma spec própria). Não registradas: estreitar detector cega (AG-016 cobre em parte), cadeia && que engole edição, e a reincidência da AG-012 (3x). |
