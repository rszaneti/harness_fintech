#!/usr/bin/env bash
# ============================================================================
# sprint-status.sh — o que falta em cada feature de em_andamento/ (spec 089/F6)
#
# Mede, não adivinha. A spec 089 nasceu da suspeita "há N features paradas
# esperando validação humana"; no piloto V-Corp essa suspeita estava ERRADA —
# eram tasks abertas que ninguém marcou. Aqui a suspeita foi medida antes de o
# comando existir, e estava meio certa: metade fecha sem escrever código, mas
# não por esperar validação humana.
#
# ⚠️ O classificador é HEURÍSTICA DE PALAVRA e vai errar. A primeira versão dele
#    (duas vias, sem a categoria "tela") classificou como "construção" quatro
#    tasks que eram permissão a cadastrar e dado de teste — o mesmo erro de
#    diagnóstico que esta spec existe para consertar, cometido ao desenhá-la.
#    Por isso a saída SEMPRE imprime o texto da task ao lado da categoria: um
#    classificador que mostra só o rótulo treina a confiar nele.
#
# Uso:
#   bash .claude/scripts/sprint-status.sh [--self-test]
# ============================================================================
set -uo pipefail

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
SPECS="$ROOT/.claude/specs"

usage() {
  awk 'NR > 2 && /^# =+$/ { exit } NR > 1 { sub(/^# ?/, ""); print }' "${BASH_SOURCE[0]}"
}

# ---------------------------------------------------------------- classificar
# Uma task aberta recebe UMA categoria. A feature herda a mais pesada que tiver:
#   construção (4) > tela (3) > humano (2) > gate (1)
#
# gate  — o fim do processo: rodar o gate, chamar o verifier, confirmar
# tela  — operação manual no sistema rodando: permissão, dado de teste, validação
# constr— código a escrever
#
# ⚠️ `[humano]` vem PRIMEIRO, e é **tela**, não gate. A primeira versão fazia o
# contrário ("gate vence porque é o passo final") e o CA-02 a reprovou em 2 dos
# 4 casos da amostra: a 069 caiu em "fecha só com gate" e seus quatro critérios
# são "preenchidos NA TELA", "percorre PELAS ABAS", "fechar a ficha e REABRI-LA".
# Neste projeto, critério `[humano]` quase sempre significa operar o sistema
# rodando — não é um "ok" de leitura.
#
# O limite honesto: o texto **não** distingue com segurança "confirmar lendo" de
# "validar operando" (a 088 tem `[humano]` sobre relatório, não sobre tela). A
# escolha é conservadora — classificar para onde exige mais do usuário — e a
# linha "↳" mostra o texto para quem lê decidir.
RE_HUMANO='\[humano\]'
RE_GATE='/finish-task|verifier|verify\.sh|GATE|check-module'
# "operação" = alguém opera o sistema; não há código a escrever.
# ⚠️ Terceira variante do mesmo erro, achada pela auditoria da T-15: 7 das 12
# features que caíam em "construção" não tinham uma linha de código — eram
# migration a EXECUTAR, rebuild de container, configuração no DocuSign, carga
# inicial de dados. O vocabulário operacional deste projeto não é só "permissão".
#
# ⚠️ O verbo é que decide em `migration`: "criar a migration Alter…" é código;
# "executar a migration", "migration aplicada no banco", "migration:run" é
# operação. Por isso as alternativas de migration exigem o verbo junto — um
# `migration` solto colocaria toda task de escrever migration no balde errado.
RE_TELA='permiss|manual|na tela|cadastrad|seed|dados m[íi]nimos|teste humano|atribu[íi]d'
RE_TELA="$RE_TELA"'|migration:run|migration aplicada|migration executada|executar a migration'
RE_TELA="$RE_TELA"'|no banco|de banco|rebuild|CONFIGURA[ÇC][ÃA]O'
# ⚠️ `container` FOI REMOVIDO daqui, e a medição é decisiva: das 51 tasks do
# corpus que citam "container", **50 são código**. Neste monorepo a palavra quer
# dizer (a) `src/shared/container/` — o container de IoC que TODA task de
# scaffold backend toca — e (b) a família `StorageContainer*`, um módulo de
# negócio inteiro: o produto É sobre containers refrigerados, está na primeira
# linha do CLAUDE.md. Com `container` na lista, toda feature cuja pendência
# fosse "Provider IoC + import em shared/container" sairia de "construção" e
# viraria "operação manual" — a inversão que esta spec existe para evitar.
# Benefício zero, aliás: com ele fora, a saída é BYTE A BYTE idêntica, porque o
# único caso real ("Rebuild do container do backend") já é pego por `rebuild`.
RE_TELA="$RE_TELA"'|carga inicial|dados de cat[áa]logo|fornecer os dados'

classificar_status() { # <texto da task> -> gate|humano|tela|constr
  local t="$1"
  if printf '%s' "$t" | grep -qiE "$RE_HUMANO"; then echo humano
  elif printf '%s' "$t" | grep -qiE "$RE_GATE"; then echo gate
  elif printf '%s' "$t" | grep -qiE "$RE_TELA"; then echo tela
  else echo constr; fi
}

# ------------------------------------------------------------------ self-test
self_test() {
  local falhas=0 esperado obtido
  echo "sprint-status --self-test"
  echo
  echo "  UM CASO POR ALTERNATIVA — cada texto exercita UMA palavra, e só."
  echo "  (a versão anterior usava casos sobredeterminados: 'Permissões … cadastradas"
  echo "   (manual via tela)' casa 4 alternativas, então apagar 11 das 13 passava verde)"
  echo "  Medido na versão de hoje: 25 alternativas reais, 25 pegas ao serem apagadas."
  while IFS='|' read -r esperado texto; do
    obtido=$(classificar_status "$texto")
    if [ "$obtido" = "$esperado" ]; then
      printf '    ✅ %-6s %s\n' "$obtido" "${texto:0:64}"
    else
      printf '    ❌ %-6s (esperado %s) %s\n' "$obtido" "$esperado" "${texto:0:50}"; falhas=$((falhas+1))
    fi
  done <<'CASOS'
humano|T-38 Criterios [humano] validados pelo usuario
gate|T-17 concluir via /finish-task
CASOS

  echo
  echo "  PRECEDÊNCIA — texto que casa DUAS categorias tem de cair na certa."
  echo "  (sem estes, inverter a ordem dos ramos passava verde — e 30 das 146"
  echo "   tasks abertas casam [humano] E uma palavra de gate ao mesmo tempo)"
  echo "  A ordem gate > tela saiu de MEDIÇÃO, não de intuição: há UM caso real"
  echo "  ambíguo em 146 — 'Conclusão via /finish-task (… nunca manualmente)' —"
  echo "  e ele é gate. Minha expectativa inicial era 'tela', e estava errada." 
  while IFS='|' read -r esperado texto; do
    obtido=$(classificar_status "$texto")
    if [ "$obtido" = "$esperado" ]; then
      printf '    ✅ %-6s %s\n' "$obtido" "${texto:0:64}"
    else
      printf '    ❌ %-6s (esperado %s) %s\n' "$obtido" "$esperado" "${texto:0:50}"; falhas=$((falhas+1))
    fi
  done <<'CASOS'
humano|T-24 Criterios [humano] CA-06 validados pelo usuario via /finish-task
humano|T-19 Criterios de aceite [humano] validados pelo usuario (via /finish-task)
humano|T-33 Criterios [humano] validados apos as permissoes cadastradas
humano|T-40 [humano] conferir depois do verifier aprovar
gate|T-44 Conclusao via /finish-task (move para concluido - nunca manualmente)
constr|T-09 CreateContainerService e o repository do modulo
constr|T-04 Provider IoC providers/index.ts e import em shared/container/index.ts
constr|T-11 StorageContainerFormStockMovementModal com motivo obrigatorio
gate|T-64 subagente verifier rodou auditoria
gate|T-12 rodar verify.sh backend
gate|T-11 GATE de conclusao
gate|T-40 rodar check-module nos modulos
tela|T-14 permissoes do modulo
tela|T-09 ajuste manual no perfil
tela|T-31 conferir na tela de perfis
tela|T-22 grupos cadastrados
tela|T-07 rodar o seed de exemplo
tela|T-25 dados minimos para o teste
tela|T-19 teste humano do fluxo
tela|T-33 grupos atribuidos ao perfil
tela|T-17 rodar migration:run
tela|T-18 migration aplicada
tela|T-29 migration executada
tela|T-30 executar a migration 642
tela|T-21 conferencia no banco depois do backfill
tela|T-18 verificacao de banco do CA-17 backfill
tela|T-66 rebuild do ambiente
tela|T-34 CONFIGURACAO do provedor externo
tela|T-15 carga inicial dos protocolos
tela|T-28 dados de catalogo do laboratorio
tela|T-16 bloqueada ate o usuario fornecer os dados
constr|T-05 CreateXService com validacao de duplicidade
constr|T-11 pages/donors/DonorFormX listagem v2
constr|T-03 migration AlterTableDonorsAddY
constr|T-08 entity e DTO do modulo
CASOS

  echo
  echo "  PREFIXO DUPLICADO — a acusação funciona?"
  # A pasta forjada tem de ficar no MESMO nível das features reais — o glob do
  # dup_check é "$SPECS/*/[0-9]*/", então uma pasta aninhada não é vista. Foi
  # assim que a primeira versão deste self-test deu falso "não acusou": o
  # detector estava certo e o CASO é que estava no lugar errado. Vazio de
  # propósito, e removido por `rmdir` (falha se alguém puser algo dentro).
  local real; real=$(ls -d "$SPECS"/em_andamento/[0-9]*/ 2>/dev/null | head -1)
  if [ -z "$real" ]; then
    echo "    ⚠️  sem feature para forjar o caso — pulado"
  else
    local pref tmp
    pref=$(basename "$real" | cut -c1-3)
    tmp="$SPECS/a_fazer/${pref}-zz-selftest-remover-se-sobrar"
    mkdir -p "$tmp"
    if dup_check | grep -q "^${pref}$"; then
      echo "    ✅ prefixo $pref forjado foi acusado"
    else
      echo "    ❌ prefixo $pref forjado NÃO foi acusado"; falhas=$((falhas+1))
    fi
    rmdir "$tmp" 2>/dev/null || { echo "    ⚠️  não removi $tmp — confira"; falhas=$((falhas+1)); }
    if dup_check | grep -q .; then
      echo "    ❌ acusou mesmo depois de remover o forjado (não-caso)"; falhas=$((falhas+1))
    else
      echo "    ✅ sem o forjado, não acusa (não-caso)"
    fi
  fi

  echo
  if [ "$falhas" -eq 0 ]; then echo "✅ self-test aprovado"; return 0
  else echo "❌ $falhas falha(s)"; return 1; fi
}

dup_check() {
  ls -d "$SPECS"/*/[0-9]*/ 2>/dev/null | xargs -n1 basename 2>/dev/null \
    | cut -c1-3 | sort | uniq -d
}

# --------------------------------------------------------------------- medida
# Uma feature de harness NÃO tem workspace: nenhum gate a alcança (dívida da
# spec 087). Sem bloco próprio ela apareceria para sempre como "fecha só com
# gate" sobre um gate que não existe.
eh_harness() { case "$1" in *harness*) return 0 ;; *) return 1 ;; esac; }

# ⚠️ `grep -oP` sem PCRE FALHA E PRODUZ NÚMERO PLAUSÍVEL: com um grep sem -P no
# PATH a saída vira "0 tasks abertas" e 49 features em "falta só rodar o gate",
# com rc=0 e nenhum aviso. É a mesma classe do `grep -c` (imprime 0 e sai 1) já
# corrigida aqui. Achado pela auditoria da T-15, com shim de grep.
exigir_pcre() {
  if ! printf 'x' | grep -qP 'x' 2>/dev/null; then
    echo "❌ este grep não tem PCRE (-P), e sem ele TODA contagem sai zero em silêncio." >&2
    echo "   Instale GNU grep com PCRE ou rode noutro ambiente. Nada foi medido." >&2
    exit 65
  fi
}

main() {
  exigir_pcre
  local f nome tasks spec abertas humano ultima cat pior primeira
  local -a L_GATE=() L_HUMANO=() L_TELA=() L_CONSTR=() L_HARNESS=() L_QUEBRADA=()
  local tot_ab=0 tot_hu=0 tot_hu_t=0 h1 h2

  for f in "$SPECS"/em_andamento/*/; do
    [ -d "$f" ] || continue
    nome=$(basename "$f")
    case "$nome" in [0-9]*) ;; *) continue ;; esac
    tasks="$f/tasks.md"; spec="$f/spec.md"
    # Pasta sem tasks.md não é "construção": é pasta quebrada. Ia para o balde
    # menos confiável e ainda imprimia "sem tasks.md" na COLUNA [humano].
    [ -f "$tasks" ] || { L_QUEBRADA+=("$nome|0|0/0|—|⚠️ pasta SEM tasks.md — corrigir"); continue; }

    abertas=0; pior=0; primeira=""
    while IFS= read -r linha; do
      abertas=$((abertas+1))
      cat=$(classificar_status "$linha")
      case "$cat" in constr) [ 4 -gt "$pior" ] && pior=4 ;;
                     tela)   [ 3 -gt "$pior" ] && pior=3 ;;
                     humano) [ 2 -gt "$pior" ] && pior=2 ;;
                     gate)   [ 1 -gt "$pior" ] && pior=1 ;; esac
      # ⚠️ NÃO usar `cut -c` aqui: ele corta por BYTE e parte caractere UTF-8 no
      # meio (texto em português é cheio deles). Medido na 1ª execução real: a
      # linha da 087 saiu crua e a da 086 terminou em "�". `${var:0:n}` do bash
      # conta CARACTERE. O `tr` remove qualquer `|` que reste — ele é o
      # separador dos registros, e um `|` no texto da task desmontaria a linha.
      if [ -z "$primeira" ]; then
        primeira=$(printf '%s' "$linha" | sed -e 's/^\*\*\(T-[0-9]*\)\*\* */\1 /' -e 's/`//g' | tr '|' '/')
        primeira="${primeira:0:72}"
      fi
    # ⚠️ Limite declarado: `\K.*` não casa comprimento zero, então uma linha
    # `- [ ]` SEM texto não é contada. É defeito do `tasks.md`, não daqui — mas
    # some em silêncio, ao contrário da pasta sem `tasks.md`, que ganhou bloco
    # próprio. Hoje não há nenhum em 55 features (medido).
    done < <(grep -oP '^\s*-\s*\[ \]\s*\K.*' "$tasks" 2>/dev/null)

    # ⚠️ `grep -c` IMPRIME "0" e SAI 1 quando não acha nada. Um `|| echo 0` aqui
    # concatena um segundo zero e o `$((…))` seguinte quebra com
    # "syntax error in expression". Medido ao rodar sobre as 54 pela 1ª vez.
    # RN-03 pede `[humano]` pendente da spec **E** do tasks. Contar só a spec
    # deixava 005, 014, 030, 043, 047, 054 e 069 com "0 [humano]" no relatório
    # estando no balde "aguarda validação" justamente por `[humano]` no tasks.
    humano=0
    local h1=0 h2=0
    if [ -f "$spec" ]; then
      h1=$(grep -cP '^\s*-\s*\[ \].*\[humano\]' "$spec" 2>/dev/null) || true
      case "$h1" in ''|*[!0-9]*) h1=0 ;; esac
    fi
    h2=$(grep -cP '^\s*-\s*\[ \].*\[humano\]' "$tasks" 2>/dev/null) || true
    case "$h2" in ''|*[!0-9]*) h2=0 ;; esac
    # ⚠️ NÃO somar os dois: são unidades diferentes. Na spec a unidade é
    # *critério de aceite*; no tasks é *linha de task*, e 16 das 55 features
    # contam o MESMO critério duas vezes (a CA aberta na spec + a task que a
    # valida) — 8 exibiam mais "[humano]" do que tasks abertas, mandando o
    # leitor procurar pendência que não existe. Duas colunas dizem o que a soma
    # escondia: se a pendência é critério a validar ou passo a executar.
    humano="$h1/$h2"
    ultima=$(awk '/^## Registro de execução/,0' "$tasks" 2>/dev/null \
             | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | sort | tail -1)
    [ -z "$ultima" ] && ultima="—"
    tot_ab=$((tot_ab+abertas)); tot_hu=$((tot_hu+h1)); tot_hu_t=$((tot_hu_t+h2))
    [ "$abertas" -eq 0 ] && primeira="(todas marcadas)"

    local linha_out="$nome|$abertas|$humano|$ultima|$primeira"
    if eh_harness "$nome"; then L_HARNESS+=("$linha_out")
    else case "$pior" in 4) L_CONSTR+=("$linha_out") ;; 3) L_TELA+=("$linha_out") ;;
                         2) L_HUMANO+=("$linha_out") ;; *) L_GATE+=("$linha_out") ;; esac; fi
  done

  bloco() { # título, explicação, itens...
    local titulo="$1" expl="$2"; shift 2
    printf '\n%s  (%d)\n' "$titulo" "$#"
    [ -n "$expl" ] && printf '  %s\n' "$expl"
    [ "$#" -eq 0 ] && { printf '  —\n'; return; }
    printf '%s\n' "$@" | sort -t'|' -k2,2n | while IFS='|' read -r n a h u p; do
      printf '  %-48s %2s abertas  [humano] %-5s  %s\n' "${n:0:48}" "$a" "$h" "$u"
      printf '      ↳ %s\n' "$p"
    done
  }

  echo "======================================================================"
  echo " SPRINT STATUS — $(date +%Y-%m-%d\ %H:%M)"
  echo " $(( ${#L_GATE[@]} + ${#L_HUMANO[@]} + ${#L_TELA[@]} + ${#L_CONSTR[@]} + ${#L_HARNESS[@]} + ${#L_QUEBRADA[@]} )) features em em_andamento/ · $tot_ab tasks abertas · [humano] pendente: $tot_hu na spec / $tot_hu_t no tasks"
  echo "======================================================================"

  bloco "FALTA SÓ RODAR O GATE" \
        "mecânico: gate, verifier, /finish-task — ninguém precisa olhar tela" "${L_GATE[@]}"
  bloco "AGUARDA VALIDAÇÃO DO USUÁRIO" \
        "critério [humano] em aberto. A linha ↳ diz se é confirmar lendo ou operar o sistema — o texto não distingue sozinho" "${L_HUMANO[@]}"
  bloco "PRECISA DE OPERAÇÃO MANUAL" \
        "permissão a cadastrar, dado de teste a criar" "${L_TELA[@]}"
  bloco "EM CONSTRUÇÃO DE FATO" \
        "código a escrever" "${L_CONSTR[@]}"
  bloco "HARNESS — nenhum gate as alcança" \
        "sem workspace: verify.sh não lê .py/.sh/.md (dívida da spec 087)" "${L_HARNESS[@]}"
  [ "${#L_QUEBRADA[@]}" -gt 0 ] && bloco "⚠️  PASTA QUEBRADA" \
        "sem tasks.md — não dá para medir nada" "${L_QUEBRADA[@]}"

  echo
  echo "----------------------------------------------------------------------"
  local dups; dups=$(dup_check)
  if [ -n "$dups" ]; then
    echo "❌ PREFIXO NUMÉRICO DUPLICADO entre estados: $(echo "$dups" | tr '\n' ' ')"
  else
    echo "✅ nenhum prefixo numérico duplicado entre a_fazer/em_andamento/concluido"
  fi
  cat <<'NOTA'

⚠️  A categoria é HEURÍSTICA DE PALAVRA e erra. O texto da task vai junto de
    propósito: confira a linha "↳" antes de agir sobre a categoria. Já houve um
    caso real — a primeira versão deste classificador pôs "permissão a cadastrar"
    em "construção". Divergência é achado sobre o script, não sobre a feature.
NOTA
}

case "${1:-}" in
  --self-test) self_test ;;
  -h|--help)   usage ;;
  "")          main ;;
  *)           usage; exit 64 ;;
esac
