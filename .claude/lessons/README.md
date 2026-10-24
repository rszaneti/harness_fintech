# Lições Aprendidas — Plataforma de Pagamentos (herdadas do ERP Vida Fértil)

> **Leia este arquivo antes de gerar qualquer código.**
> Cada lição representa um erro real cometido em sessões anteriores.
> O objetivo é não repetir o mesmo erro duas vezes.

---

## Origem

**Lessons herdadas do ERP Vida Fértil em 23/10/2026; códigos BE/FE/AG mantidos** (spec 001,
RN-06). As 87 lições (32 BE, 26 FE, 29 AG — contadas em 23/10/2026; o `documentacao/05` diz 79) de `backend.md`, `frontend.md` e `agents.md` vieram **inteiras** — códigos,
textos, números e caminhos originais. São da stack (TypeORM, Express, Jest, celebrate, MUI,
agentes), não do domínio da clínica, e cada uma registra um erro real. Reescrever o caminho dentro
delas reescreveria a evidência.

Por isso os caminhos citados nas lições são os **do ERP de origem**. A correspondência neste
projeto (`.claude/workspaces.json`):

| Caminho na lesson | Aqui |
|---|---|
| `backend/admin` | `backend/api` |
| `frontend/admin` | `frontend/operador` (e, para regra de SPA, também `frontend/cliente`) |
| `frontend/portal`, `frontend/professional` | sem correspondente — eram SPAs de outros públicos (tentante, especialista) |
| módulos citados como exemplo (`donors_*`, `clinics`, `patients`…) | sem correspondente — vale o erro, não o módulo |

Lição nova escrita neste projeto usa os caminhos daqui e continua a numeração de onde parou
(`BE-033`, `FE-027`, `AG-030`…) — o código é único entre origem e clone.

---

## Política de promoção (REGRA CENTRAL)

Lessons são uma **área de triagem**, não um arquivo que só cresce. Toda lesson nova passa por esta avaliação:

| A regra é... | Destino |
|--------------|---------|
| Verificável por grep/padrão de texto | **Promover** para `.claude/hooks/post-edit-check.sh` (verificação automática a cada edição) |
| Coberta por regra de ESLint existente ou configurável | **Promover** para o ESLint do workspace — o hook pós-edição já roda ESLint por arquivo |
| Verificável por inspeção estruturada (diff, estrutura de pastas, ordem de registros) | **Delegar** ao subagente `verifier` (já lista as lessons que audita) |
| Exige julgamento de contexto que máquina não pega | **Permanece** aqui como lesson textual |

Lesson promovida ganha a marca `[PROMOVIDA → hook/eslint/verifier]` no título e o corpo pode ser
resumido — a verificação mecânica passa a ser a fonte de verdade. **Lição que virou verificação
mecânica nunca mais se repete e não consome contexto.**

## Status de promoção atual

| Lesson | Status |
|--------|--------|
| BE-001 / AG-004 (import AppError sem uso) | PROMOVIDA → hook (grep) |
| BE-002 / AG-005 (no-useless-assignment) | PROMOVIDA → ESLint via hook |
| BE-007 (uuid_generate_v4 proibido) | PROMOVIDA → hook (grep) **em migration E em `plan.md`/`tasks.md`** — a 3ª ocorrência (spec 041) veio do `_templates/plan.md`, não do código: hook audita a saída, template molda a entrada |
| FE-008 (CssDateField props) | PROMOVIDA → hook (grep, parcial) |
| FE-009 (inputProps deprecated) | PROMOVIDA → hook (grep) |
| BE-014 (rota literal depois de `/:param`) | PROMOVIDA → hook (ordem de registro no arquivo) |
| BE-023 (`auditDelete` inexistente) | PROMOVIDA → hook (grep em `infra/typeorm/repositories/`) |
| FE-021 (mock implementado na factory do `jest.mock`) | PROMOVIDA → hook (`jest-mock-factory.py`) — a janela entre `jest.mock(` e o fecha-parênteses; grep simples não distingue a factory do `beforeEach` |
| FE-022 (varredura por assinatura em vez de corpo) | verifier audita — conversor numérico × campo `type="number"` de Formik |
| AG-020 (anunciar varredura sem validar o detector) | **PROMOVIDA → núcleo do `verifier.md`** — vale em toda auditoria, não depende de etiqueta. ⚠️ Vale também para a AMOSTRA: número medido sobre commit de 1.800 arquivos não descreve um diff de feature (spec 087) |
| **AG-023** (relação nova só no repositório do dono) | **era `AG-020`** até 12/09/2026 — o código estava duplicado; renumerada na spec 087. verifier audita (check `removal`) |
| FE-010 (hook condicional) | PROMOVIDA → ESLint (rules-of-hooks) via hook |
| FE-011 (import sem uso) | PROMOVIDA → ESLint (no-unused-vars) via hook |
| **AG-024** (renomeação em lote atropela identificador de biblioteca) | **era `AG-021`** até 12/09/2026 — o código estava duplicado com "gate em background"; renumerada na spec 088 (mesmo caso do `AG-020` → `AG-023`).<br> PROMOVIDA → hook (grep da chave de `toast.POSITION`; 0 falso positivo em 648 usos) **+** verifier para a variante `@Entity`, cujos detectores óbvios acusam 31% e 17% de casos legítimos |
| FE-024 (`slots={{ backdrop: Backdrop }}` no Modal) | PROMOVIDA → hook (grep sobre o CÓDIGO) **+** neutralizada no `CssModalForm`, que repõe o `zIndex: -1` |
| FE-023 (crase em comentário dentro de `styled`) | PROMOVIDA → hook (`styled-template-backtick.py`) — o ESLint já pegava, mas a mensagem apontava a linha errada |
| FE-025 (espelhar tela sem conferir o schema Joi da rota) | **PROMOVIDA (parcial) → `check-module.py --contract`** (spec 087): chaves do payload × `[Segments.BODY]`, como **INFO**. Limite declarado no script: compara contra a UNIÃO de todas as rotas, então só acusa campo que não existe em rota nenhuma — o resto continua com o verifier (check `contract`) |
| FE-026 (tela inerte com o corpo comentado; `carriers` 3×) | verifier audita — antes de migrar, remover comentários DE VERDADE e conferir que a tela chama o backend |
| Editar migration versionada | GUARDRAIL → hook protect-migrations.sh |
| BE-003 / AG-006 (ordem de rotas webhook) | verifier audita |
| BE-004 / AG-001 (stub vs módulo completo) | verifier audita |
| BE-008 (código falível fora do try-catch) | verifier audita |

| **AG-025** (edição por `sed`/heredoc não dispara o hook) | **PROMOVIDA → `PreToolUse` `block-shell-write-ts.py`** (spec 090): recusa `>`, `>>`, `>\|`, `sed -i`, `tee`, `cp`, `mv` com alvo `.ts/.tsx` dentro dos workspaces, resolvendo `cd` em qualquer posição. ⚠️ Eu havia escrito aqui que **não era promovível** — "o ponto é que o hook não é chamado". Estava errado: o `PostToolUse` não é chamado, mas o **`PreToolUse` de `Bash`** é. **Limite declarado**: não detecta `python -c` com `open(...,'w')`, `dd of=`, `perl -i`, `xargs`, variável com prefixo do workspace, `cd` em subshell, `cp` para diretório, nem tag de heredoc com hífen — todos com **0 ocorrências** medidas, e a ressalva de que o corpus é anterior ao hook. A regra **reduz** a rota, não a fecha; a defesa independente de quem escreveu continua sendo `verify.sh` + `check-module.py`, que leem o disco |
| **AG-026** (pasta no gate é regex de caminho, não prefixo de diretório) | **PROMOVIDA → `verify.sh`** (spec 090): o argumento de pasta é **normalizado** com `/` final (inclusive caminho absoluto) e o resumo **declara** que normalizou; o step passou a carregar **quantas suítes** o pattern casou. Medido: `donors/donors` ia de 282 para 12. **Limite**: a normalização só alcança pasta que existe como diretório — `donors/donorss/` inexistente segue passando com 0 suítes |
| **FE-020** (troca de modo de montagem destrói/congela estado) | **verifier audita** — num diff que troque condicional ⇄ `display` ⇄ aba, checar cada `useState` do componente afetado |
| BE-010 (CryptoProvider em campos sensíveis) | verifier audita (check `sensitive-field`) |
| **AG-022** (tipo do frontend nunca conferido contra a resposta do backend) | **PROMOVIDA (parcial) → `check-module.py --contract`** (spec 087): campos do `ICreate…DTO` × interface `I<Modulo>`, por nome, como **INFO** — o julgamento de que lado corrige continua sendo do verifier (check `contract`) |
| AG-002 / FE-001..7 (vazamento do módulo de referência) | **PROMOVIDA → `check-module.py --ref`** (spec 087). Sem `--ref` a checagem é PULADA e o resumo diz isso — não cala |
| FE-013 (componente novo nunca montado) | **PROMOVIDA → `check-module.py`** (spec 087) — o hook enxerga 1 arquivo por vez; o script varre o `src/` inteiro atrás do import |
| AG-009 (find antes de declarar sucesso) | **PROMOVIDA → `check-module.py`** (spec 087): compara a pasta com os destinos que o `scaffold.py` geraria — a lista vive num lugar só |
| AG-010 (formato de batch response) | verifier audita |
| BE-015 (enum espelhado com valores quase iguais) | verifier audita |
| **AG-027** (`--scope` sobre workspace limpo mede diff vazio) | **PROMOVÍVEL — não promovida** (spec 092). O `verify.sh` já conhece o tamanho da lista de arquivos: quando `mode=scope` e o conjunto é vazio, gravar `rc: 0` produz evidência indistinguível de um gate real. A promoção é recusar ou marcar a evidência como não-conclusiva. Enquanto não for, a defesa é humana: **ler o `N` em `eslint (N arquivo(s) do diff)` antes de aceitar o verde** |
| **AG-028** (fechamento exige `--full`) | **PROMOVÍVEL — não promovida** (spec 092). É uma linha no passo 2 do `.claude/commands/finish-task.md`, que hoje manda repetir o comando da task — e o comando da task é `--scope`. Achou 2 defeitos invisíveis ao `--scope` no fechamento da 092: um de 14 dias, um de 2 minutos |
| **AG-029** (sessão concorrente no mesmo workspace) | **NÃO promovível** (spec 092): `stash` defensivo mexe em trabalho alheio e comparar `mtime` daria falso positivo em toda feature. Promovível só a **regra de leitura** — o gate poderia sinalizar quando o `tsc` acusa linha que não existe no arquivo. Julgamento humano |
| **FE-025 — emenda** (2ª ocorrência, 4 defeitos) | **candidata a re-promoção: `verifier` → `tsc`** (spec 092). O `payload: object` nas assinaturas dos services HTTP do frontend é o que apaga o typecheck. Tipá-los põe a checagem dentro de **um** workspace, contornando a objeção original ("cruzaria dois `.git`"). Não resolve divergência de valor; mata "chave que a rota não conhece" e "obrigatória omitida" |
| BE-016 (`Joi.boolean()` em QUERY comparado com `'true'`) | **PROMOVIDA → hook** (spec 087): bloqueia `Joi.boolean()` dentro de `[Segments.QUERY]` em `*.routes.ts`, sobre o código. Medido antes de promover: zero ocorrências na base, 6 rotas já na convenção correta — nasceu sem falso positivo. Também no `check-module.py` |
| FE-014 (espelho de regra deve errar para o lado permissivo) | verifier audita — irmã da FE-013 |
| **AG-017** (remoção conferida pelo termo novo) | **PROMOVIDA → `_templates/tasks.md`** (task obrigatória de grep do termo VELHO quando a feature remove algo) + verifier audita. Hook é inviável: `post-edit-check.sh` recebe só `file_path`, sem diff |
| **AG-011** (corrigir sem confirmar que o estado é alcançável) | **verifier audita** — 2 checagens: estado alcançável pelo fluxo que gerou o bug + asserção que falharia se a correção fosse revertida |
| **AG-019** (gate vermelho que acusa o ambiente) | **verifier audita** — escrita em `agents/verifier.md` §Gate mecânico, ao lado da AG-012. **PROMOVIDA → `verify.sh` (spec 084)**: toolchain ausente é exit 65 `TOOLCHAIN AUSENTE`, com a lista em `missing` na evidência — ambiente errado e código errado deixaram de reprovar igual |
| Demais (BE-005, BE-006, BE-009, BE-011, AG-008) | lesson textual |

## Como usar

1. **Antes de gerar código**: ler os arquivos de lição do contexto (backend e/ou frontend).
2. **Erro novo encontrado**: documentar no arquivo correspondente seguindo o padrão abaixo
   **e aplicar a política de promoção** — se for automatizável, a entrega inclui a regra no
   hook/ESLint, não só o texto.
3. **Agentes**: ler `.claude/lessons/backend.md` e/ou `frontend.md` + `agents.md` antes de escrever arquivos.

## Arquivos de lição

| Arquivo | Escopo |
|---------|--------|
| [backend.md](backend.md) | Erros em services, entities, repositories, routes, migrations |
| [frontend.md](frontend.md) | Erros em contexts, components, types, services HTTP |
| [agents.md](agents.md) | Erros específicos de agentes gerando múltiplos arquivos |

## Padrão de documentação de uma lição

```markdown
### [LESSON-XXX] Título curto do erro

**Contexto**: onde acontece
**Erro cometido**: o que foi gerado de errado
**Regra correta**: o que deve ser feito
**Automatizável?**: sim (hook/eslint/verifier) | não — se sim, onde foi implementada
**Exemplo errado**: ...
**Exemplo correto**: ...
```
