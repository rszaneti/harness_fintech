#!/usr/bin/env bash
# =============================================================================
# verify.sh — GATE ÚNICO DE VERIFICAÇÃO do harness  (v2.1 — spec 084 do ERP; spec 001: workspaces
#             de .claude/workspaces.json e alvo `harness`)
#
# Nenhuma task pode ser marcada como concluída sem este script passar.
#
# Uso:
#   bash .claude/scripts/verify.sh <alvo> [modulo] [--scope|--full] [--feature <nome>] [--since <ref>]
#   bash .claude/scripts/verify.sh --check-evidence <feature> <workspace|harness>
#
# Alvos (workspaces vêm de .claude/workspaces.json — nenhum caminho fixo aqui):
#   backend | operador | cliente | simulator   o workspace de mesma chave
#   frontend                                   todos os workspaces de kind=frontend
#   harness                                    o próprio harness (.claude/, CLAUDE.md, documentacao/):
#                                              bash -n, compilação dos .py e os --self-test (spec 001,
#                                              RN-16) — é o que lint/tsc/jest não alcançam
#   all                                        todos os workspaces + harness
#
# Modos:
#   --scope (padrão)  arquivos = diff do workspace (git diff <ref> + untracked), só .ts/.tsx de src/.
#                     ESLint com cache só nesses arquivos; tsc --noEmit (incremental via tsconfig);
#                     jest --findRelatedTests sobre eles (+ jest da pasta [modulo], se dada).
#   --full            cobertura completa: ESLint em tudo (com cache), tsc, suíte completa de jest
#                     (ou a pasta [modulo]). É o modo do fechamento de sprint.
#
# Flags:
#   --feature <nome>  grava a evidência em .claude/gate/<nome>.<workspace>.json (só este script
#                     escreve nesse diretório). O hash do diff sai no RESUMO DO GATE.
#   --since <ref>     base do diff (padrão HEAD). Ex.: --since sprint/2026-09-15
#                     Repositório SEM COMMIT (a raiz antes do commit inicial): HEAD vira a árvore
#                     vazia, e o resumo diz isso.
#   --check-evidence  recalcula o hash do diff atual e compara com o gravado.
#                     exit 0 = válida e aprovada · 3 = desatualizada · 4 = ausente
#                     · 5 = hash igual, mas o gate gravado NÃO aprovou (rc ≠ 0)
#
# Ambiente:
#   SKIP_TSC=1        pula o typecheck (só com autorização explícita do usuário)
#   VERIFY_ROOT=<dir> sobrescreve a raiz do monorepo — só para o teste de sandbox (CA-03)
#
# Códigos de saída: 0 aprovado · 1 etapa reprovada · 3/4/5 (--check-evidence) · 64 uso · 65 TOOLCHAIN AUSENTE
#
# ⚠️ Toolchain ausente (eslint/tsc/jest fora de node_modules/.bin) NÃO é "PULADO": é exit 65.
#    Gate que não rodou não é gate (AG-019). Workspace cuja PASTA não existe neste checkout
#    vira aviso no resumo, com a spec que o cria (campo `spec` do workspaces.json), sem reprovar.
# ⚠️ Em --scope, diff SÓ de configuração (tsconfig, jest/eslint config) invalida o hash mas
#    produz "eslint (0 arquivos)" e "jest (0 arquivos)": só o tsc avalia algo. O --full da
#    sprint é quem cobre esse caso.
# =============================================================================
set -u

VERIFY_VERSION="2.1"
ROOT="${VERIFY_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"
# O harness que roda é sempre o DESTE script — mesmo com VERIFY_ROOT apontando para um sandbox.
HARNESS="$(cd "$(dirname "$0")/.." && pwd)"
WSPY="$HARNESS/scripts/workspaces.py"
EMPTY_TREE="4b825dc642cb6eb9a060e54bf8d69288fbee4904"
GATE_DIR="$ROOT/.claude/gate"
SKIP_TSC="${SKIP_TSC:-0}"

usage() {
  # Cabeçalho = linhas entre a régua de abertura (linha 2) e a régua de fechamento.
  awk 'NR > 2 && /^# =+$/ { exit } NR > 2 { print }' "$0" | sed 's/^# \{0,1\}//' >&2
  exit 64
}

# ----------------------------------------------------------------------------- argumentos
TARGET=""; MODULE=""; NORMALIZOU=""; MODE="scope"; FEATURE=""; SINCE="HEAD"; CHECK=""
while [ $# -gt 0 ]; do
  case "$1" in
    --scope) MODE="scope" ;;
    --full)  MODE="full" ;;
    --feature) [ $# -ge 2 ] || usage; FEATURE="$2"; shift ;;
    --since)   [ $# -ge 2 ] || usage; SINCE="$2"; shift ;;
    --check-evidence) [ $# -ge 3 ] || usage; CHECK="1"; FEATURE="$2"; TARGET="$3"; shift 2 ;;
    -h|--help) usage ;;
    --*) echo "flag desconhecida: $1" >&2; usage ;;
    *)
      if [ -z "$TARGET" ]; then TARGET="$1"
      elif [ -z "$MODULE" ]; then MODULE="$1"
      else usage; fi ;;
  esac
  shift
done
[ -n "$TARGET" ] || usage

ws_dir() { # ws -> caminho (harness = a raiz do monorepo)
  [ "$1" = "harness" ] && { echo "$ROOT"; return 0; }
  python3 "$WSPY" --root "$ROOT" --path "$1"
}
ws_kind() { python3 "$WSPY" --kind "$1"; }
ws_spec() { python3 "$WSPY" --spec "$1"; }

# O que o hash cobre, por alvo (pathspecs do git, um por linha). `harness` exclui o próprio gate
# (gravar a evidência mudaria o hash que ela registra) e as PASTAS DE ESTADO das features — o
# registro das features, não o harness: marcar `[x]` no tasks.md logo depois do gate, ou o
# /finish-task mudar o status, invalidaria a evidência que acabou de ser gravada (achado na T-19 da
# spec 001). `_templates/` e o README de specs SÃO harness e continuam no hash (BAIXA da 1ª
# auditoria: a 1ª exclusão levava `.claude/specs/` inteiro).
hash_spec() { # ws
  if [ "$1" = "harness" ]; then
    printf '%s\n' .claude CLAUDE.md documentacao .gitignore \
      ':(exclude).claude/gate' ':(exclude).claude/projects' ':(exclude).claude/settings.local.json' \
      ':(exclude).claude/specs/a_fazer' ':(exclude).claude/specs/em_andamento' \
      ':(exclude).claude/specs/concluido' ':(exclude).claude/specs/canceladas'
  else
    printf '%s\n' src tsconfig.json package.json babel.config.js jest.config.ts jest.config.js \
      eslint.config.cjs eslint.config.js eslint.config.mjs .eslintrc.js .eslintrc.json .eslintrc .eslintignore
  fi
}

# Base efetiva: `HEAD` num repositório sem commit vira a árvore vazia (spec 001 — a raiz nasce sem
# commit, e o gate da própria 001 tem de rodar ANTES do commit inicial, que é a última task dela).
resolve_base() { # dir base
  if [ "$2" = "HEAD" ] && ! git -C "$1" rev-parse --verify --quiet "HEAD^{commit}" >/dev/null 2>&1; then
    echo "$EMPTY_TREE"
  else
    echo "$2"
  fi
}

# ⚠️ RN-04 (spec 090; lesson AG-026): o argumento de módulo vira `jest <pattern>`, e o pattern do
# jest é **REGEX DE CAMINHO**, não prefixo de diretório. Sem a barra final,
# `src/modules/donors/donors` casa também `donors_freezings`, `donors_collections`… — medido:
# **282 suítes** sem a barra, **12** com. No piloto da 062 isso produziu um vermelho alheio
# convincente (um teste obsoleto da spec 074), custou uma decisão do usuário, e só apareceu quando
# alguém foi medir. **15 dos 176 módulos** são vítimas reais.
#
# Normalizar aqui, e DIZER que normalizou: correção silenciosa vira a próxima surpresa.
if [ -n "$MODULE" ]; then
  _d="$(ws_dir "$TARGET" 2>/dev/null)"
  # ⚠️ Caminho ABSOLUTO também tem de normalizar: `[ -d "$_d/$MODULE" ]` falha para ele, e sem a
  # barra o pattern volta a casar 282 suítes — o defeito da AG-026 intacto para essa forma.
  case "$MODULE" in
    */) : ;;
    /*) if [ -d "$MODULE" ]; then MODULE="$MODULE/"; NORMALIZOU="1"; fi ;;
    *)  if [ -n "$_d" ] && [ -d "$_d/$MODULE" ]; then
          MODULE="$MODULE/"
          NORMALIZOU="1"
        fi ;;
  esac
  unset _d
fi

# ----------------------------------------------------------------------------- hash / evidência
# O hash cobre: git diff <base> sobre src/ e os arquivos de configuração que mudam o resultado do
# gate (tsconfig, package.json, jest/eslint config), mais o CONTEÚDO de todo untracked em src/.
# Um untracked editado depois do gate muda o hash. yarn.lock regenerado (ver memória do lockfile)
# fica fora, de propósito: não altera lint/tsc/jest.
diff_hash() { # dir base ws
  V_DIR="$1" V_BASE="$(resolve_base "$1" "$2")" V_SPEC="$(hash_spec "${3:-}")" python3 - <<'PY'
import hashlib, os, subprocess, sys
d, base = os.environ["V_DIR"], os.environ["V_BASE"]
h = hashlib.sha256()
# A lista vem do `hash_spec` do shell: `src` + configs para workspace, `.claude` & cia. para harness.
spec = [s for s in os.environ["V_SPEC"].split("\n") if s]
untracked_spec = [s for s in spec if s.startswith(":(") or s in ("src", ".claude", "documentacao", "CLAUDE.md", ".gitignore")]
# check=True: git falhando (base inexistente, sem .git) NÃO pode virar o hash da string vazia —
# que é exatamente o hash de um workspace limpo. --no-ext-diff: diff.external local mudaria a saída.
try:
    h.update(subprocess.run(["git", "diff", "--no-ext-diff", base, "--", *spec],
                            cwd=d, capture_output=True, check=True).stdout)
    un = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "--", *untracked_spec],
                        cwd=d, capture_output=True, check=True).stdout.decode().split("\n")
except subprocess.CalledProcessError as e:
    sys.stderr.write("diff_hash: git falhou em %s (base '%s'): %s\n"
                     % (d, base, e.stderr.decode(errors="replace").strip()))
    sys.exit(1)
except OSError as e:  # pasta do workspace inexistente, git ausente
    sys.stderr.write("diff_hash: não foi possível rodar git em %s: %s\n" % (d, e))
    sys.exit(1)
for f in sorted(x for x in un if x):
    p = os.path.join(d, f)
    if os.path.isfile(p):
        h.update(f.encode() + b"\0")
        with open(p, "rb") as fh:
            h.update(fh.read())
print(h.hexdigest())
PY
}

# ⚠️ ACUMULA — não sobrescreve (spec 090, RN-01 a RN-03).
#
# Antes, esta função abria o arquivo em "w" e gravava. Um JSON por feature+workspace, sem merge,
# sem histórico, sem comparar `rc`. Consequência medida no piloto da spec 062: o lead rodou dois
# escopos no mesmo workspace — `donors/donors` deu rc=1 e `documents_files` deu rc=0, nessa ordem —
# e a evidência sobrevivente dizia **"rc": 0**, com o `steps` sem nenhum sinal da rodada vermelha.
# `--check-evidence` saía **0**. Falso verde na camada criada PARA impedir falso verde.
#
# Agora: funde os `steps` (as chaves já são únicas por escopo), acumula `scopes`, e o `rc` gravado
# é o **PIOR** entre o que havia e o novo.
#
# ⚠️ Por que o pior, e não "recusar sobrescrever com rc melhor": recusar cria vermelho grudento —
# depois de corrigir, a rodada verde não grava, e o caminho de menor resistência vira apagar o JSON
# à mão, que é desativar o gate por outro nome. O pior protege igual sem criar esse incentivo,
# porque a correção MUDA O DIFF: o hash muda e o arquivo recomeça sozinho (RN-02).
write_evidence() { # ws hash rc
  [ -n "$FEATURE" ] || return 0
  mkdir -p "$GATE_DIR"
  V_OUT="$GATE_DIR/$FEATURE.$1.json" V_FEATURE="$FEATURE" V_WS="$1" V_MODE="$MODE" V_BASE="$SINCE" \
  V_HASH="$2" V_RC="$3" V_FILES="$CUR_FILES" V_STEPS="$CUR_STEPS" V_MISSING="$CUR_MISSING" \
  V_SCOPE="${MODULE:-}" V_VERSION="$VERIFY_VERSION" python3 - <<'PY'
import datetime, json, os
e = os.environ
steps = {}
for line in e["V_STEPS"].split("\n"):
    if "\t" in line:
        k, v = line.split("\t", 1)
        # RN-03b: `suites`/`tests` quando o step os declarou (`ok\x1f12\x1f78`), senão só o status.
        partes = v.split("\x1f")
        d = {"status": partes[0]}
        if len(partes) == 3:
            d["suites"], d["tests"] = int(partes[1]), int(partes[2])
        steps[k] = d

rc = int(e["V_RC"])
escopo = e["V_SCOPE"] or "(workspace inteiro)"
scopes, antes = [escopo], None
try:
    with open(e["V_OUT"], encoding="utf-8") as fh:
        antes = json.load(fh)
except Exception:
    antes = None

# RN-02: só acumula enquanto o diff for o MESMO. Hash diferente = diff novo, acumulação anterior
# é lixo e o arquivo recomeça. É o mesmo invariante que o --check-evidence já usa.
missing = e["V_MISSING"].split()
# ⚠️ `--full` SUBSTITUI, não funde. `scope ⊂ full` para o mesmo workspace: uma rodada `--full`
# re-roda tudo que qualquer `--scope` poderia ter rodado, então fundi-la num scope vermelho
# anterior deixaria um vermelho que nada limpa — o "vermelho grudento" que a RN-01 evita. A
# assimetria é o ponto: `--scope` depois de `--full` continua fundindo (e o `rc` continua o pior),
# porque scope NÃO cobre o que full cobriu. `scopes` é preservado como histórico nos dois casos.
# ─────────────────────────────────────────────────────────────────────────────────────────────
# UMA RODADA QUE NÃO RODOU não substitui, não degrada e não define o modo.
#
# ⚠️ Este predicado nasceu de **três achados de auditoria que eram a mesma frase** — e só ficaram
# visíveis como uma coisa só quando alguém os leu juntos:
#
#   1. `rc=65` (toolchain ausente): a substituição `--full` apagava uma reprovação real. Cadeia
#      reproduzida: scope A vermelho → `--full` com o container morto → scope B verde = **rc 0**,
#      com o módulo A nunca tendo voltado a rodar e o código nunca tendo sido tocado.
#   2. `skip` (`SKIP_TSC=1`): um `--full` que NÃO fez typecheck substituía um scope que reprovou
#      NO typecheck. Autorizar pular o tsc numa rodada não é autorizar apagar um tsc que reprovou
#      noutra.
#   3. `mode`: a rodada inválida ainda gravava `"mode": "full"`, e daí em diante nenhum `--full`
#      verde conseguia mais substituir — vermelho grudento permanente, que é exatamente o que o
#      comentário da acumulação diz evitar. E nem corrigir resolvia, porque o hash não muda.
#
# Os três são manifestações de um conceito que o script não tinha com nome. Com nome, são um.
# A lição de método vale mais que os consertos: quando três achados seguidos couberem na mesma
# frase, o que falta não é a terceira correção — é o predicado.
_steps_novos = [v.split("\x1f")[0] for v in
                (l.split("\t", 1)[1] for l in e["V_STEPS"].split("\n") if "\t" in l)]
_rodada_valida = (e["V_RC"] != "65"
                  and not e["V_MISSING"].split()
                  and "skip" not in _steps_novos)
_substitui = (antes is not None
              and antes.get("diff_hash") == e["V_HASH"]
              and e["V_MODE"] == "full" and antes.get("mode") != "full"
              and _rodada_valida)
if _substitui:
    scopes = list(dict.fromkeys((antes.get("scopes") or []) + scopes))
    antes = None
if antes and antes.get("diff_hash") == e["V_HASH"]:
    velhos = antes.get("steps") or {}
    if velhos and isinstance(next(iter(velhos.values()), None), str):
        velhos = {k: {"status": v} for k, v in velhos.items()}  # formato anterior à 090
    # ⚠️ Reexecutar o MESMO escopo não pode APAGAR o `fail` anterior em silêncio: as chaves são
    # iguais e o `update` sobrescreveria. Quem corrigiu de verdade mudou o diff, e aí o hash muda e
    # o arquivo recomeça (RN-02). Enquanto o diff é o mesmo, o histórico do step fica no JSON.
    for k, novo in steps.items():
        ant = velhos.get(k)
        if ant and ant.get("status") == "fail" and novo.get("status") == "ok":
            novo = dict(novo); novo["antes"] = "fail"
        velhos[k] = novo
    steps = velhos
    # ⚠️ 65 (TOOLCHAIN AUSENTE) FICA FORA do `max()`. Ele não é "pior que 1": é outro eixo — o gate
    # NÃO RODOU (AG-019). Com 65 no max, `max(1,65)=65` mascararia uma reprovação genuína como
    # "ambiente quebrado", e reexecutar num ambiente são nunca limparia o 65. Regra: 65 só
    # sobrevive se a rodada nova TAMBÉM for 65.
    rc_antes = int(antes.get("rc", 0))
    if rc == 65 or rc_antes == 65:
        rc = 65 if (rc == 65 and rc_antes == 65) else max(
            0 if rc == 65 else rc, 0 if rc_antes == 65 else rc_antes)
    else:
        rc = max(rc, rc_antes)                      # RN-01: o PIOR
    # ⚠️ `missing` é o ÚLTIMO ESTADO CONHECIDO do ambiente, não união histórica.
    #
    # A 1ª correção do `rc=65` acumulava `missing`, e isso só mudou a grudência de lugar: uma
    # rodada 65 seguida de uma rodada verde completa dava `rc: 0` com `missing` NÃO vazio — e o
    # `verifier.md` exige `missing: []` para aceitar exit 0, tornando a condição inalcançável
    # depois de qualquer 65 no mesmo hash. O mecanismo e o procedimento discordavam sobre o mesmo
    # arquivo. Invariante restaurada: **`rc=0` ⇒ `missing=[]`**.
    missing = sorted(set(missing) | set(antes.get("missing") or []))
    scopes = list(dict.fromkeys((antes.get("scopes") or []) + scopes))

doc = {
    "feature": e["V_FEATURE"], "workspace": e["V_WS"],
    # ⚠️ Uma rodada inválida **não define o modo**: ela não é uma medição, é o registro de que o
    # ambiente falhou. Gravando `"mode": "full"` a partir de um `--full` que não rodou, nenhum
    # `--full` verde conseguia mais substituir — vermelho grudento que nem corrigir limpa, porque
    # o hash não muda. Manifestação nº 3 do `_rodada_valida`.
    "mode": e["V_MODE"] if (_rodada_valida or antes is None) else antes.get("mode", e["V_MODE"]),
    "base": e["V_BASE"],
    "diff_hash": e["V_HASH"],
    "files": [f for f in e["V_FILES"].split("\n") if f],
    # RN-03: o que se PRETENDIA cobrir. `steps` diz o que rodou; sem `scopes`, "o lead esqueceu o
    # módulo A" volta a ser invisível.
    "scopes": scopes,
    "steps": steps,
    # ⚠️ INVARIANTE, nas duas direções: `rc != 65` ⇒ `missing == []`.
    #
    # `missing` só descreve o ambiente quando o `rc` diz que o gate NÃO RODOU. Tentei antes uma
    # regra por caso ("o velho morre se o novo está são") e ela cobria só `65 → verde`; a ordem
    # inversa (`verde → 65`) deixava `rc=0` com `missing` não vazio, e aí `--check-evidence` saía
    # 0 enquanto o `verifier.md` — que exige `missing: []` para exit 0 — bloqueava. Mecanismo e
    # procedimento discordando sobre o mesmo arquivo.
    #
    # Uma rodada que não rodou **não degrada** uma medição feita quando o ambiente funcionava: o
    # `rc` já exclui 65 do pior (AG-019), e o `missing` segue a mesma lógica em uma linha.
    "missing": missing if rc == 65 else [],
    "rc": rc,
    "at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    "verify_sh": e["V_VERSION"],
}
with open(e["V_OUT"], "w", encoding="utf-8") as fh:
    json.dump(doc, fh, ensure_ascii=False, indent=2); fh.write("\n")
if len(scopes) > 1:
    print("   ↳ evidência ACUMULADA: %d escopos, rc = o pior (%d)" % (len(scopes), rc))
PY
  echo "📄 evidência: .claude/gate/$FEATURE.$1.json"
}

if [ -n "$CHECK" ]; then
  dir="$(ws_dir "$TARGET")" || usage
  f="$GATE_DIR/$FEATURE.$TARGET.json"
  if [ ! -f "$f" ]; then
    echo "EVIDÊNCIA $TARGET: ausente ($f)"; exit 4
  fi
  # ⚠️ RN-03: a checagem mecânica tem de EXPOR `scopes` e `missing`. Gravá-los num JSON que
  # ninguém lê deixa "o lead esqueceu de rodar o módulo A" invisível para tudo, menos para um
  # humano que pense em abrir o arquivo — e a RN não se cumpre com armazenamento.
  if ! fields=$(python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print(d.get('diff_hash',''),d.get('base','HEAD'),d.get('rc',1),d.get('mode','?'));print(', '.join(d.get('scopes') or ['—']));print(', '.join(d.get('missing') or ['—']))" "$f" 2>/dev/null); then
    echo "EVIDÊNCIA $TARGET: arquivo ilegível ($f não é JSON válido) — tratar como desatualizada"; exit 3
  fi
  # ⚠️ `read -r` quebra em ESPAÇO, e o rótulo padrão de escopo é `(workspace inteiro)` — que tem
  # um. A 1ª versão imprimia "escopos cobertos : (workspace" e "toolchain ausente: inteiro), …",
  # ou seja, a linha criada para acabar com uma invisibilidade produzia leitura errada no caso
  # mais comum (toda rodada sem módulo). Três linhas do python, lidas por `sed -n`.
  # (O `\x1f` é usado noutros dois pontos deste script, mas NÃO aqui — o comentário antigo
  # descrevia uma solução que não é a implementada.)
  read -r saved base rc mode <<< "$(printf '%s\n' "$fields" | head -1)"
  scopes_txt=$(printf '%s\n' "$fields" | sed -n '2p')
  missing_txt=$(printf '%s\n' "$fields" | sed -n '3p')
  if ! current=$(diff_hash "$dir" "$base" "$TARGET"); then
    echo "EVIDÊNCIA $TARGET: não foi possível recalcular o hash (base '$base' inexistente ou ${dir#$ROOT/} sem git) — tratar como desatualizada"; exit 3
  fi
  if [ "$saved" != "$current" ]; then
    echo "EVIDÊNCIA $TARGET: desatualizada (gravado ${saved:0:12} ≠ atual ${current:0:12}, base=$base)"; exit 3
  fi
  if [ "$rc" != "0" ]; then
    echo "EVIDÊNCIA $TARGET: hash igual, mas o gate gravado NÃO aprovou (rc=$rc, modo=$mode) — corrigir e rodar o gate de novo"
    echo "  escopos cobertos : $scopes_txt"
    echo "  toolchain ausente: $missing_txt"
    exit 5
  fi
  echo "EVIDÊNCIA $TARGET: válida (hash ${current:0:12}, rc=0, modo=$mode, base=$base)"
  echo "  escopos cobertos : $scopes_txt"
  echo "  toolchain ausente: $missing_txt"
  exit 0
fi

# ----------------------------------------------------------------------------- etapas
FAILED=0; TOOLCHAIN_MISSING=0; SUMMARY=""; HASHES=""
CUR_STEPS=""; CUR_FILES=""; CUR_MISSING=""; WS_FAILED=0

begin_ws() { CUR_STEPS=""; CUR_FILES=""; CUR_MISSING=""; WS_FAILED=0; }

# ⚠️ RN-03b (spec 090): o step grava `suites`/`tests` quando o comando é jest, não só o status.
# Achado da reauditoria da 062: o lead afirmou "12 suítes / 78 testes, era 77, +1 é o caso novo" e
# o `verifier` NÃO teve como conferir sem rodar o gate de novo — o JSON guardava só `"ok"`.
# Afirmação desse tipo passava a depender de confiança, que é o que o harness existe para dispensar.
# Separador \x1f (unit separator) porque \t já separa chave de valor e o texto do jest tem ambos.
step() { # ws key label dir comando...
  local ws="$1" key="$2" label="$3" dir="$4"; shift 4
  local saida rc_step conta=""
  echo ""; echo "▶ $ws: $label"
  if [ "${1##*/}" = "jest" ]; then
    saida="$( (cd "$dir" && "$@") 2>&1 )"; rc_step=$?
    printf '%s\n' "$saida"
    conta=$(printf '%s\n' "$saida" | awk '
      /^Test Suites:/ { for (i=1;i<=NF;i++) if ($i=="total") s=$(i-1) }
      /^Tests:/       { for (i=1;i<=NF;i++) if ($i=="total") t=$(i-1) }
      END { if (s != "" && t != "") printf "\x1f%s\x1f%s", s, t }')
  else
    (cd "$dir" && "$@"); rc_step=$?
  fi
  if [ "$rc_step" -eq 0 ]; then
    SUMMARY="${SUMMARY}
✅ $ws: $label"; CUR_STEPS="${CUR_STEPS}${key}	ok${conta}
"
  else
    SUMMARY="${SUMMARY}
❌ $ws: $label"; CUR_STEPS="${CUR_STEPS}${key}	fail${conta}
"; FAILED=1; WS_FAILED=1
  fi
}

skip_step() { # ws key texto
  SUMMARY="${SUMMARY}
⚠️ $1: $3"; CUR_STEPS="${CUR_STEPS}$2	skip
"
}

check_toolchain() { # ws dir binários...
  local ws="$1" dir="$2"; shift 2; local missing=""
  for b in "$@"; do
    [ "$b" = "tsc" ] && [ "$SKIP_TSC" = "1" ] && continue
    [ -x "$dir/node_modules/.bin/$b" ] || missing="$missing $b"
  done
  [ -z "$missing" ] && return 0
  echo "" >&2
  echo "❌ TOOLCHAIN AUSENTE em $ws:$missing — o gate NÃO rodou (não é reprovação nem aprovação)." >&2
  echo "   Esperado em $dir/node_modules/.bin/. Rode 'yarn install' no workspace certo, no ambiente certo." >&2
  SUMMARY="${SUMMARY}
❌ $ws: TOOLCHAIN AUSENTE —$missing"
  CUR_MISSING="${missing# }"; TOOLCHAIN_MISSING=1; WS_FAILED=1
  return 1
}

changed_files() { # dir -> lista (relativa ao workspace), só .ts/.tsx existentes em src/
  local dir="$1" base; base="$(resolve_base "$1" "$SINCE")"
  (
    cd "$dir" || exit 0
    git diff --name-only --relative --diff-filter=ACMR "$base" -- . 2>/dev/null
    git ls-files --others --exclude-standard -- src 2>/dev/null
  ) | sort -u | while read -r f; do
    case "$f" in
      src/*.ts|src/*.tsx) [ -f "$dir/$f" ] && printf '%s\n' "$f" ;;
    esac
  done
}

eslint_flags() { # dir -> "--no-warn-ignored" se a versão aceitar (ESLint 9+; o frontend usa 8)
  if (cd "$1" && ./node_modules/.bin/eslint --help 2>/dev/null | grep -q -- '--no-warn-ignored\|--warn-ignored'); then
    echo "--no-warn-ignored"
  fi
}

lint_step() { # ws dir alvo-full
  local ws="$1" dir="$2" full_target="$3"
  local flags; flags="$(eslint_flags "$dir")"
  if [ "$MODE" = "full" ]; then
    # shellcheck disable=SC2086
    step "$ws" "eslint" "eslint (full, com cache)" "$dir" \
      ./node_modules/.bin/eslint --cache --cache-location .eslintcache $flags "$full_target"
    return
  fi
  if [ -z "$CUR_FILES" ]; then
    SUMMARY="${SUMMARY}
✅ $ws: eslint (0 arquivos no diff)"; CUR_STEPS="${CUR_STEPS}eslint	ok
"
    return
  fi
  local -a files; mapfile -t files <<< "$CUR_FILES"
  # shellcheck disable=SC2086
  step "$ws" "eslint" "eslint (${#files[@]} arquivo(s) do diff, com cache)" "$dir" \
    ./node_modules/.bin/eslint --cache --cache-location .eslintcache $flags "${files[@]}"
}

tsc_step() { # ws dir
  if [ "$SKIP_TSC" = "1" ]; then
    skip_step "$1" "tsc" "typecheck PULADO (SKIP_TSC=1 — só com autorização do usuário)"
  else
    step "$1" "tsc" "typecheck (tsc --noEmit, incremental)" "$2" ./node_modules/.bin/tsc --noEmit
  fi
}

check_base() { # ws dir — ref inexistente é erro de uso, não reprovação
  local base onde; base="$(resolve_base "$2" "$SINCE")"
  onde="${2#$ROOT/}"; [ "$2" = "$ROOT" ] && onde="a raiz do monorepo"
  if [ "$base" = "$EMPTY_TREE" ]; then
    SUMMARY="${SUMMARY}
ℹ️ $1: $onde sem nenhum commit — base do diff = árvore vazia (tudo conta como novo)"
    return 0
  fi
  if ! git -C "$2" rev-parse --verify --quiet "$base^{commit}" >/dev/null 2>&1; then
    echo "❌ $1: ref '$SINCE' não existe em ${2#$ROOT/}" >&2; exit 64
  fi
}

# ----------------------------------------------------------------------------- harness (spec 001)
# O harness é .py/.sh/.md: lint, tsc e jest não o leem, e TODOS os defeitos ALTA das fases F4, F5 e
# F7 do ERP estavam em arquivos que nenhum gate lia. Estas etapas são a prova que substitui, na
# forma que o `verifier-checks/harness.md` (pergunta 4) já exigia: `bash -n`, compilação e o
# `--self-test` de cada peça que o tem. Etapa nova entra AQUI, na task que cria a peça — nunca como
# etapa condicional ("roda se existir"): etapa que some quando a peça some é falso verde.
harness_files() { # sufixo -> arquivos do harness (fora de gate/, projects/, _backup_*, __pycache__)
  (cd "$HARNESS" && find . -type f -name "*$1" \
     -not -path './gate/*' -not -path './projects/*' -not -path './_backup*' -not -path '*/__pycache__/*' \
     | sort)
}

verify_harness() {
  local dir="$ROOT" ws="harness"
  begin_ws
  check_base "$ws" "$dir"
  local hash
  if ! hash="$(diff_hash "$dir" "$SINCE" "$ws")"; then
    echo "❌ $ws: falha ao calcular o hash do diff" >&2; exit 64
  fi
  HASHES="${HASHES}
HASH $ws: ${hash:0:12} (base $SINCE)"
  local -a shs pys
  mapfile -t shs < <(harness_files .sh)
  mapfile -t pys < <(harness_files .py)
  step "$ws" "bash-n" "bash -n (${#shs[@]} .sh)" "$HARNESS" \
    bash -c 'r=0; for f in "$@"; do bash -n "$f" || r=1; done; exit $r' _ "${shs[@]}"
  # compile() e não py_compile: py_compile grava .pyc, e o gate não deixa rastro no que audita.
  step "$ws" "py-compile" "compilação dos .py (${#pys[@]})" "$HARNESS" \
    python3 -c 'import sys
r = 0
for f in sys.argv[1:]:
    try: compile(open(f, encoding="utf-8").read(), f, "exec")
    except SyntaxError as e: print(f"{f}: {e}"); r = 1
sys.exit(r)' "${pys[@]}"
  step "$ws" "workspaces" "workspaces.py --self-test" "$HARNESS" python3 scripts/workspaces.py --self-test
  # CA-06 como guarda PERMANENTE: executável do harness que cita workspace fora do JSON reprova.
  step "$ws" "workspaces-scan" "workspaces.py --scan (nenhum workspace fora do JSON)" "$HARNESS" python3 scripts/workspaces.py --scan
  step "$ws" "placeholders" "scaffold.py --list-placeholders" "$HARNESS" python3 scaffold/scaffold.py --list-placeholders
  step "$ws" "scaffold-static" "scaffold.py --self-test static (sem workspace)" "$HARNESS" python3 scaffold/scaffold.py --self-test static
  step "$ws" "check-module" "check-module.py --self-test" "$HARNESS" python3 scripts/check-module.py --self-test
  step "$ws" "diff-classify" "diff-classify.py --list-tags" "$HARNESS" python3 scripts/diff-classify.py --list-tags
  step "$ws" "jest-mock-factory" "hooks/jest-mock-factory.py --self-test" "$HARNESS" python3 hooks/jest-mock-factory.py --self-test
  step "$ws" "block-shell-write-ts" "hooks/block-shell-write-ts.py --self-test" "$HARNESS" python3 hooks/block-shell-write-ts.py --self-test
  local fin
  for fin in money-bigint ledger-immutable idempotency-required no-secret-in-code; do
    step "$ws" "$fin" "hooks/$fin.py --self-test" "$HARNESS" python3 "hooks/$fin.py" --self-test
  done

  local rc=0
  [ "$WS_FAILED" -ne 0 ] && rc=1
  write_evidence "$ws" "$hash" "$rc"
}

verify_workspace() { # ws
  local ws="$1" dir; dir="$(ws_dir "$ws")"
  begin_ws
  if [ ! -d "$dir" ]; then
    SUMMARY="${SUMMARY}
⚠️ $ws: pasta ${dir#$ROOT/} não existe neste checkout (nasce na spec $(ws_spec "$ws")) — nada a verificar"
    return 0
  fi
  check_base "$ws" "$dir"

  local hash
  if ! hash="$(diff_hash "$dir" "$SINCE" "$ws")"; then
    echo "❌ $ws: falha ao calcular o hash do diff em ${dir#$ROOT/}" >&2; exit 64
  fi
  HASHES="${HASHES}
HASH $ws: ${hash:0:12} (base $SINCE)"
  CUR_FILES="$(changed_files "$dir")"

  case "$(ws_kind "$ws")" in
    backend)
      if check_toolchain "$ws" "$dir" eslint tsc jest; then
        lint_step "$ws" "$dir" "."
        tsc_step "$ws" "$dir"
        if [ "$MODE" = "full" ]; then
          if [ -n "$MODULE" ]; then
            step "$ws" "jest($MODULE)" "jest ($MODULE)" "$dir" ./node_modules/.bin/jest --passWithNoTests "$MODULE"
          else
            step "$ws" "jest" "jest (suíte completa)" "$dir" ./node_modules/.bin/jest --passWithNoTests
          fi
        else
          if [ -n "$CUR_FILES" ]; then
            local -a files; mapfile -t files <<< "$CUR_FILES"
            step "$ws" "jest(related)" "jest (relacionado a ${#files[@]} arquivo(s) do diff)" "$dir" \
              ./node_modules/.bin/jest --passWithNoTests --findRelatedTests "${files[@]}"
          else
            SUMMARY="${SUMMARY}
✅ $ws: jest (0 arquivos no diff)"; CUR_STEPS="${CUR_STEPS}jest(related)	ok
"
          fi
          if [ -n "$MODULE" ]; then
            # RN-04: declarar QUANTAS suítes o pattern casou. É o que torna o desvio visível sem
            # ninguém procurar — e a diferença entre 12 e 282 é a diferença entre medir o módulo e
            # medir o contexto inteiro.
            # ⚠️ `wc -l` conta 1 para a linha vazia que o `--listTests` imprime quando NÃO casa
            # nada — e é justamente o caso que a RN-04 existe para expor. `grep -c .` conta só
            # linha com conteúdo. Medido: pattern inexistente dava "1 suíte(s)", agora dá 0.
            _n=$(cd "$dir" && ./node_modules/.bin/jest --listTests "$MODULE" 2>/dev/null | grep -c . || true)
            [ -n "$NORMALIZOU" ] && SUMMARY="${SUMMARY}
ℹ️ $ws: pattern normalizado para '$MODULE' (com barra final) — sem ela o jest casa os módulos irmãos (AG-026)"
            step "$ws" "jest($MODULE)" "jest ($MODULE — $_n suíte(s) casada(s))" "$dir" ./node_modules/.bin/jest --passWithNoTests "$MODULE"
            unset _n
          fi
        fi
      fi ;;
    frontend)
      if check_toolchain "$ws" "$dir" eslint tsc; then
        lint_step "$ws" "$dir" "src/**/*.{ts,tsx}"
        tsc_step "$ws" "$dir"
      fi ;;
  esac

  local rc=0
  [ "$WS_FAILED" -ne 0 ] && rc=1
  [ -n "$CUR_MISSING" ] && rc=65
  write_evidence "$ws" "$hash" "$rc"
}

case "$TARGET" in
  harness) verify_harness ;;
  all)
    while read -r w; do verify_workspace "$w"; done <<< "$(python3 "$WSPY" --group all)"
    verify_harness ;;
  *)
    if ! _grupo="$(python3 "$WSPY" --group "$TARGET")"; then
      echo "alvo desconhecido: $TARGET" >&2; usage
    fi
    while read -r w; do verify_workspace "$w"; done <<< "$_grupo"
    unset _grupo ;;
esac

echo ""
echo "================ RESUMO DO GATE ($MODE) ================"
printf '%s\n' "$SUMMARY"
printf '%s\n' "$HASHES"
echo "========================================================"

if [ "$TOOLCHAIN_MISSING" -ne 0 ]; then
  echo "❌ TOOLCHAIN AUSENTE — o gate NÃO rodou. Não é reprovação nem aprovação: reexecute no ambiente certo."
  exit 65
fi
if [ "$FAILED" -ne 0 ]; then
  echo "❌ GATE REPROVADO — a task NÃO pode ser concluída. Corrija e rode novamente."
  exit 1
fi
echo "✅ GATE APROVADO."
exit 0
