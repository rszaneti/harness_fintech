#!/usr/bin/env bash
# =============================================================================
# Hook PostToolUse (Edit|Write) — verificação mecânica pós-edição
#
# Roda automaticamente após cada Edit/Write do Claude:
#   1. Checagens de lessons promovidas (regras automatizáveis de .claude/lessons/)
#   2. ESLint no arquivo editado (no workspace que o contém — ver .claude/workspaces.json)
#
# Exit 2 => o erro é devolvido ao Claude, que deve corrigir imediatamente.
# =============================================================================

INPUT=$(cat)

FILE=$(printf '%s' "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('file_path', ''))
except Exception:
    pass
" 2>/dev/null)

[ -z "$FILE" ] && exit 0
[ ! -f "$FILE" ] && exit 0

# -----------------------------------------------------------------------------
# [BE-007] no PLAN, antes de virar migration — 3a ocorrencia da mesma causa
#
# A checagem de migration (mais abaixo) audita a SAIDA. Esta audita a ENTRADA: o
# `_templates/plan.md` trazia `gen_random_uuid()` na linha de exemplo da PK, e
# todo plan gerado por /spec-plan herdava a orientacao proibida antes de existir
# qualquer codigo. Pegar aqui custa um grep e evita o erro em toda feature.
# -----------------------------------------------------------------------------
case "$FILE" in
  */.claude/specs/*plan.md|*/.claude/specs/*tasks.md)
    # ⚠️ EXCECAO POR OCORRENCIA, NAO POR ARQUIVO. A versao anterior liberava o
    # arquivo inteiro se a string "BE-007" aparecesse em QUALQUER lugar — e os
    # plans desta casa trazem uma tabela de lessons na secao de riscos. Um plan
    # que citasse BE-007 la e escrevesse `default: gen_random_uuid()` na tabela
    # de entidades passava em silencio, que e exatamente o caso que a guarda
    # nasceu para pegar. Agora a marca tem que estar NA MESMA LINHA da mencao.
    if grep -nE "uuid_generate_v4\(\)|gen_random_uuid\(\)" "$FILE" | grep -qv "BE-007"; then
      echo "[BE-007] Este plan/tasks propoe funcao de geracao de uuid do Postgres para a PK, numa linha que nao explica que ela NAO entra. O id vem do uuidv4() da APLICACAO, no create do repositorio — nem uuid_generate_v4(), nem gen_random_uuid() (que nao existe neste banco). Corrija o plan ANTES de gerar a migration." >&2
      exit 2
    fi
    exit 0
    ;;
esac

# Só verifica TypeScript
case "$FILE" in
  *.ts|*.tsx) ;;
  *) exit 0 ;;
esac

# Detecta o workspace do arquivo — pela lista de .claude/workspaces.json (spec 001). Até a 001 isto
# era um `case` com os caminhos fixos, e workspace novo tinha de ser lembrado AQUI na task que o
# criava; esquecer fazia os arquivos dele nascerem fora do harness, sem ESLint e sem as lessons
# promovidas. Agora workspace novo é uma linha no JSON, e o `verify.sh harness` confere a lista.
WSPY="$(dirname "$0")/../scripts/workspaces.py"
# ⚠️ A detecção falhar (JSON quebrado) NÃO pode virar "arquivo fora de workspace": isso desligava em
# silêncio ESLint, lessons e os 4 hooks (achado MÉDIA da 1ª auditoria da spec 001).
if ! WS=$(python3 "$WSPY" --which-dir "$FILE" 2>&1); then
  echo "❌ .claude/workspaces.json ilegível — a verificação pós-edição NÃO RODOU para $FILE:" >&2
  echo "$WS" | tail -3 >&2
  exit 2
fi
WS_KEY=""
[ -n "$WS" ] && WS_KEY=$(python3 "$WSPY" --which "$FILE" 2>/dev/null)

ERRORS=""

# CÓDIGO SEM COMENTÁRIO, para as regras abaixo (AG-013).
#
# ⚠️ Até a spec 087 a FE-009 fazia grep no arquivo CRU e a FE-024 filtrava só linha inteira de
# comentário. Nenhum dos dois cobre o comentário JSX `{/* … */}` nem o bloco `/* … */`, e o
# resultado é a AG-013 ao contrário: o arquivo que ADVERTE contra o antipadrão é reprovado por
# exibi-lo. Quem pegou foram as fixtures de `.claude/scripts/tests/check-module/`, escritas
# justamente para provar que comentário não acusa — e que o hook reprovou.
#
# `code-only.py` importa o `strip_comments` do scaffold: um autômato de estado de string, num
# lugar só. Se ele não estiver disponível, a regra cai no filtro antigo em vez de sumir.
CODE_ONLY="$(dirname "$0")/code-only.py"
if [ -f "$CODE_ONLY" ]; then
  TSX_CODE=$(python3 "$CODE_ONLY" "$FILE" 2>/dev/null) || TSX_CODE=""
fi
[ -z "${TSX_CODE:-}" ] && TSX_CODE=$(grep -vE '^[[:space:]]*(//|\*|/\*)' "$FILE")


# -----------------------------------------------------------------------------
# LESSONS PROMOVIDAS — regras de .claude/lessons/ que viraram verificação mecânica
# -----------------------------------------------------------------------------

# [BE-007] PK uuid: nunca usar uuid_generate_v4()
# ⚠️ A versão anterior desta regra dizia "usar 'gen_random_uuid()'" — orientação
# INVERTIDA, e ela vazou para o código: as migrations de `patients` (spec 049)
# nasceram com esse default, a função NÃO existe neste PostgreSQL, e a fila de
# migrations travou para todas as features seguintes. O id vem do `uuidv4()` da
# APLICAÇÃO; nenhuma função do banco entra aqui.
case "$FILE" in
  */migrations/*)
    if grep -qE "uuid_generate_v4|gen_random_uuid" "$FILE"; then
      # Comentário explicando a ausência é legítimo; default de coluna, não.
      if grep -qE "default:\s*['\"](uuid_generate_v4|gen_random_uuid)\(\)" "$FILE"; then
        ERRORS="${ERRORS}
[BE-007] PK uuid com 'default' de geração no banco. O id vem do uuidv4() da aplicação, no create do repositório — nenhuma função do Postgres (nem uuid_generate_v4, nem gen_random_uuid)."
      fi
    fi

    # [BE-022] Seed tem que poder rodar duas vezes.
    case "$FILE" in
      *SeedTable*)
        if grep -q "INSERT INTO" "$FILE" && ! grep -qi "NOT EXISTS" "$FILE"; then
          ERRORS="${ERRORS}
[BE-022] Migration de seed com INSERT sem guarda 'NOT EXISTS'. Reprocessar estoura por chave duplicada e trava a fila de migrations inteira."
        fi
        ;;
    esac

    # [BE-022] ALTER tem que poder rodar duas vezes -- mesma razao do seed.
    #
    # ⚠️ ATE 2026-08-20 ESTA REGRA COBRIA SO 'SeedTable*', e a skill so tinha
    # template de createTable: toda migration de alter nascia improvisada e sem
    # guarda. Medicao na data: 27 dos 41 arquivos AlterTable* com addColumn
    # estavam sem nenhuma. `migration:run` e SEQUENCIAL -- uma que estoure ao
    # reprocessar trava a fila para TODAS as features seguintes, nao so a sua
    # (no ERP de origem, a spec 049 parou a spec 032 exatamente assim).
    #
    # Escopo: nome AlterTable* OU presenca de addColumn (que so faz sentido em
    # tabela existente). CreateTable* nao entra: ali FK e indice vem logo apos o
    # createTable, sobre tabela recem-criada e vazia -- guarda seria ruido.
    #
    # As migrations ja versionadas nao sao afetadas: protect-migrations.sh
    # bloqueia a edicao delas antes de este hook rodar.
    #
    # ⚠️ AS CHECAGENS RODAM SOBRE O CODIGO, NAO SOBRE O ARQUIVO CRU. Sem isso a
    # primeira vitima e o proprio template da skill, que DOCUMENTA o antipadrao
    # do `return` no topo num comentario para o gerador nao copia-lo -- e era
    # reprovado por exibir exatamente o que manda evitar. Vale nos dois sentidos:
    # comentario nao dispara a regra, e comentario tambem nao serve de guarda.
    CODE=$(grep -vE '^[[:space:]]*(//|\*|/\*)' "$FILE")

    IS_ALTER=""
    case "$FILE" in
      *AlterTable*) IS_ALTER="1" ;;
    esac
    if [ -z "$IS_ALTER" ] && printf '%s\n' "$CODE" | grep -qE 'addColumns?\('; then
      IS_ALTER="1"
    fi

    if [ -n "$IS_ALTER" ]; then
      if printf '%s\n' "$CODE" | grep -qE 'addColumns?\(' \
         && ! printf '%s\n' "$CODE" | grep -qE 'hasColumn|findColumnByName'; then
        ERRORS="${ERRORS}
[BE-022] addColumn sem guarda de existencia. Envolver em 'if (!(await queryRunner.hasColumn(tabela, coluna)))'. Reprocessar estoura e trava a fila de migrations inteira. Template: .claude/scaffold/templates/backend/migration-alter.ts.tpl (scaffold.py migration alter)"
      fi

      if printf '%s\n' "$CODE" | grep -qE 'queryRunner\.createForeignKey\(' \
         && ! printf '%s\n' "$CODE" | grep -qE 'foreignKeys'; then
        ERRORS="${ERRORS}
[BE-022] createForeignKey em migration de alter sem guarda. Nomear a FK e checar 'table.foreignKeys.some((f) => f.name === ...)' antes de criar."
      fi

      if printf '%s\n' "$CODE" | grep -qE 'queryRunner\.createIndex\(' \
         && ! printf '%s\n' "$CODE" | grep -qE 'indices'; then
        ERRORS="${ERRORS}
[BE-022] createIndex em migration de alter sem guarda. Nomear o indice e checar 'table.indices.some((i) => i.name === ...)' antes de criar."
      fi

      # ADD COLUMN por SQL cru escapa das checagens acima -- ali a guarda e o
      # proprio IF NOT EXISTS.
      if printf '%s\n' "$CODE" | grep -qiE 'ADD COLUMN' \
         && ! printf '%s\n' "$CODE" | grep -qiE 'ADD COLUMN IF NOT EXISTS'; then
        ERRORS="${ERRORS}
[BE-022] 'ADD COLUMN' em SQL cru sem 'IF NOT EXISTS'."
      fi

      # Guarda POR OPERACAO, nunca um return no topo. Com a coluna presente mas
      # FK/indice ausentes (reprocessamento parcial), o return sai 'com sucesso'
      # e deixa o schema incompleto em silencio.
      if printf '%s\n' "$CODE" | grep -qE '(hasColumn|findColumnByName)\(.*\)[^;]*\breturn\b' \
         && printf '%s\n' "$CODE" | grep -qE 'queryRunner\.(createForeignKey|createIndex)\('; then
        ERRORS="${ERRORS}
[BE-022] Guarda de coluna usada como 'return' no topo, com FK/indice depois. Se a coluna ja existir mas a FK/indice nao, eles sao pulados em silencio. Guardar CADA operacao separadamente."
      fi
    fi
    ;;
esac

# [BE-001]/[AG-004] import de AppError sem uso
# Aceita 'throw new AppError' (caso comum) e também 'new AppError' passado como
# valor — em middlewares e callbacks do Express o erro é ENCAMINHADO via next(err)
# ou callback(err), nunca lançado. O caso que a lesson combate (importar e nunca
# referenciar) continua sendo pego.
case "$FILE" in
  *AppError.ts|*/errors/*) ;;
  *)
    if grep -q "import AppError" "$FILE" && ! grep -q "new AppError" "$FILE"; then
      ERRORS="${ERRORS}
[BE-001] Arquivo importa AppError mas nunca instancia 'new AppError(...)' — remover o import."
    fi
    ;;
esac

# [BE-023] `auditDelete` NAO EXISTE neste repositorio.
# No ERP de origem, o `CLAUDE.md` do workspace e a documentacao de arquitetura mandavam
# usar o util — e a instrucao ja derrubou o tsc de 12 repositorios na spec 054. O import
# compila no editor (o path alias existe) e o ESLint nao resolve modulos: so o
# `tsc --noEmit` acusa, entao quem roda apenas o lint entrega o modulo quebrado.
# Padrao real: `await this.ormRepository.delete(ids)`.
case "$FILE" in
  */infra/typeorm/repositories/*.ts)
    # Mencao em comentario e legitima (documenta a ausencia); import/chamada, nao.
    # Descarta o comentario ANTES de procurar (AG-013). Tem de cobrir comentario de
    # FIM DE LINHA tambem: o filtro so-de-linha-inteira deixa passar
    # `this.ormRepository.delete(ids) // nao existe auditDelete` e acusa o arquivo
    # justamente por documentar a regra.
    # Mesmo filtro da FE-009/FE-024 (spec 087): o `sed` de antes não cobria bloco nem JSX.
    if printf '%s\n' "$TSX_CODE" | grep -q "auditDelete"; then
      ERRORS="${ERRORS}
[BE-023] Uso de 'auditDelete' — este util NAO EXISTE (o tsc reprova). Usar 'await this.ormRepository.delete(ids)'."
    fi
    ;;
esac

# [BE-016] `Joi.boolean()` no `Segments.QUERY` entrega BOOLEAN ao controller.
#
# O celebrate roda o Joi com `convert: true` e SUBSTITUI `req.query` pelo objeto convertido. O
# controller que compara com `'true'` recebe um boolean, `true === 'true'` é false, e o filtro
# devolve o OPOSTO do pedido: na spec 025, filtrar "Ativo: Sim" listava os protocolos inativos.
# Nenhum gate pegava — para o tsc tudo é string|boolean válido, o ESLint não sabe de semântica, e
# os specs de service recebem o valor JÁ convertido.
#
# Promovida na spec 087. Medido antes de promover: ZERO rotas usam este padrão hoje e 6 já usam a
# convenção correta — a regra nasce sem falso positivo. Verificável dentro de um arquivo só, como
# a BE-014 — por isso vive aqui, e não só no verifier.
case "$FILE" in
  *.routes.ts)
    BOOL_QUERY=$(python3 - "$FILE" "$(dirname "$0")/../scaffold" <<'PY' 2>/dev/null
import re, sys
# Sobre o CÓDIGO: um comentário que ADVERTE contra o padrão não pode acusar o arquivo (AG-013).
# ⚠️ A 1ª versão filtrava só `//` com regex e reprovava um aviso escrito em bloco `/* */` — a
# AG-013 literal dentro da regra escrita para evitá-la. O autômato mora no scaffold.py.
# ⚠️ O caminho do scaffold vem por ARGUMENTO. A 1ª correção o derivava de `sys.argv[0]`, que num
# `python3 -` vale `'-'`: o import falhava em todo cwd que não fosse a raiz, o erro ia para o
# `2>/dev/null` e a regra virava no-op SILENCIOSO — justamente no fluxo que o CLAUDE.md documenta
# como normal ("abra o Claude Code dentro do workspace"). Achado da 2ª auditoria da 087.
sys.path.insert(0, sys.argv[2])
from scaffold import strip_comments_keep_lines
src = strip_comments_keep_lines(open(sys.argv[1], encoding='utf-8').read())
# Os dois idiomas de QUERY no repositório: objeto literal e `Joi.object().keys({`.
for m in re.finditer(r"\[Segments\.QUERY\]\s*:\s*(?:Joi\.object\(\)\.keys\()?\s*\{", src):
    i, depth = m.end(), 1
    while i < len(src) and depth:
        if src[i] == '{': depth += 1
        elif src[i] == '}': depth -= 1
        i += 1
    bloco = src[m.end():i]
    base = src[:m.end()].count('\n')
    for f in re.finditer(r"(\w+)\s*:\s*Joi\.boolean\(\)", bloco):
        print(f"  linha {base + bloco[:f.start()].count(chr(10)) + 1}: {f.group(1)}")
PY
)
    if [ -n "$BOOL_QUERY" ]; then
      ERRORS="${ERRORS}
[BE-016] Campo declarado 'Joi.boolean()' dentro de [Segments.QUERY]. O celebrate converte e o controller recebe BOOLEAN — comparar com 'true' inverte o filtro (a tela lista o oposto do pedido). Use Joi.string().valid('true','false') e converta com um helper puro (ver parseOptionalBoolean em laboratories/exams_protocols/helpers/), preservando o undefined de \"sem filtro\".
${BOOL_QUERY}"
    fi
    ;;
esac

# [BE-014] Rota de caminho literal registrada DEPOIS de rota '/:param' do mesmo verbo.
# O Express casa na ordem de registro: com '/:id' antes, um DELETE '/file' cai no
# handler de '/:id' com id='file' e morre no celebrate, sem nunca chegar ao controller.
# Verificável dentro de um único arquivo — por isso vive aqui, e não só no verifier.
case "$FILE" in
  *.routes.ts)
    SHADOW=$(python3 -c "
import re, sys
src = open(sys.argv[1], encoding='utf-8').read()
pairs = re.findall(r\"\.(get|post|put|patch|delete)\(\s*['\\\"]([^'\\\"]*)['\\\"]\", src)
seen = {}
for verb, path in pairs:
    stripped = path.strip('/')
    seg = stripped.split('/')[0] if stripped else ''
    if seg.startswith(':'):
        seen.setdefault(verb, path)
    elif seg and verb in seen:
        print(f\"  {verb.upper()} '{path}' vem DEPOIS de {verb.upper()} '{seen[verb]}'\")
" "$FILE" 2>/dev/null)
    if [ -n "$SHADOW" ]; then
      ERRORS="${ERRORS}
[BE-014] Rota literal sombreada por rota com parâmetro (Express casa na ordem de registro):
${SHADOW}
  Mover as rotas de caminho literal para ANTES das rotas '/:param' do mesmo verbo."
    fi
    ;;
esac

# [AG-024] Renomeacao em lote a partir de modulo-molde atropela identificador que
# NAO e do dominio. Duas variantes, ambas pegas por padrao de texto:
#
#   (a) chave de opcao de biblioteca. `position: toast.POSITION.TOP_CENTER` virou
#       `sampletype: toast.POSITION.TOP_CENTER` ao copiar de `positions`. O
#       react-toastify ignora chave desconhecida em silencio: o toast some do
#       canto e nada acusa. Nem ESLint nem tsc pegam -- o objeto de opcoes e
#       Partial<ToastOptions> e a chave extra e aceita.
#
#   (b) nome de tabela no @Entity. `@Entity('sample_types')` virou
#       `@Entity('sampletypes')`, divergindo da tabela que a migration cria. O
#       tsc compila, o lint passa, e o modulo so quebra em runtime na 1a query.
#
# Ocorrencia real: specs 080/081/082 (2026-09-11), moldadas em `positions`.
if [ "${FILE##*.}" = "tsx" ] || [ "${FILE##*.}" = "ts" ]; then
  BADTOAST=$(grep -nE "[A-Za-z_][A-Za-z0-9_]*: *toast\.POSITION\." "$FILE" \
             | grep -vE "(^|[^A-Za-z0-9_])position: *toast\.POSITION\.")
  if [ -n "$BADTOAST" ]; then
    ERRORS="${ERRORS}
[AG-024] Chave de opcao do react-toastify renomeada — a opcao chama-se 'position' e
qualquer outro nome e ignorado EM SILENCIO (o toast perde o posicionamento):
${BADTOAST}
  Restaure 'position: toast.POSITION.…'. Se veio de copia de modulo-molde, procure
  outros identificadores de biblioteca atropelados pela mesma renomeacao."
  fi
fi

# A variante (b) NAO vive aqui: os dois detectores obvios sao ruidosos demais para
# hook bloqueante, e foram medidos antes de decidir.
#   - @Entity vs nome da pasta: 63 de 203 entities (31%) divergem LEGITIMAMENTE —
#     entity-filha mora na pasta do pai (`customers_addresses` em `address/`).
#   - @Entity vs tabela criada por alguma migration: 35 de 203 (17%) sao tabelas
#     legadas, anteriores ao historico de migrations (`companies`, `fiscal_*`).
# Hook que erra 1 em 3 deixa de ser lido. A checagem (b) fica com o `verifier`, que
# tem contexto para distinguir filha legitima de erro de renomeacao — ver AG-024.

# [FE-009] inputProps deprecated no MUI v7 — usar slotProps.htmlInput
if [ "${FILE##*.}" = "tsx" ] && printf '%s\n' "$TSX_CODE" | grep -qE "inputProps=\{"; then
  ERRORS="${ERRORS}
[FE-009] Uso de 'inputProps={...}' (deprecated no MUI v7) — usar slotProps={{ htmlInput: { ... } }}."
fi

# [FE-024] slots={{ backdrop: Backdrop }} poe o escurecimento NA FRENTE do modal.
#
# O `Modal` do MUI usa por padrao o seu proprio backdrop --
# `styled(Backdrop)({ zIndex: -1 })`. Passar o `Backdrop` cru descarta esse -1, e
# sem ele o backdrop vira elemento posicionado de z-index auto: pela ordem de
# pintura do CSS fica ACIMA do fundo do cartao (bloco nao posicionado) e ABAIXO
# dos inputs (position: relative). O cartao aparece todo cinza com so os campos
# brancos.
#
# As 62 chamadas v1 passam esse slots, e a migracao mecanica traz junto. O
# `CssModalForm` v2 ja repoe o -1, entao isto e a segunda barreira -- e a que
# ensina, porque o override some do codigo em vez de ficar la sendo neutralizado.
#
# Escopo: so quem ja esta no v2. Arquivo v1 nao e reprovado por ainda ser v1.
#
# ⚠️ SOBRE O CODIGO, NAO SOBRE O ARQUIVO CRU -- mesma razao da BE-022. A
# primeira vitima desta regra foi a propria aba de contatos, que traz um
# comentario explicando por que o override NAO deve ser usado: a mensagem que
# ensina a evitar o antipadrao nao pode ser reprovada por exibi-lo.
# Mesmo filtro da FE-009 (spec 087): cobre comentário JSX e bloco multilinha, que o filtro
# só-de-linha-inteira não cobria.
MODAL_CODE="$TSX_CODE"
if [ "${FILE##*.}" = "tsx" ] \
   && grep -q "globalMaterialUi_v2" "$FILE" \
   && printf '%s\n' "$MODAL_CODE" | grep -qE "slots=\{\{[[:space:]]*backdrop:"; then
  ERRORS="${ERRORS}
[FE-024] 'slots={{ backdrop: Backdrop }}' numa tela ja no v2. O Backdrop cru nao tem o 'z-index: -1' do slot padrao do Modal, e sem ele o escurecimento pinta NA FRENTE do cartao (so os inputs, que sao position:relative, ficam por cima). Remova o 'slots' e o import do Backdrop -- o 'slotProps={{ backdrop: { timeout } }}' funciona sozinho, mesclado no slot padrao."
fi

# [FE-023] Crase dentro de comentario CSS de um styled-component.
#
# No template de um `styled.div\`...\`` o /* */ nao e comentario de JS: e TEXTO
# da string. Uma crase ali FECHA o template no meio.
#
# Promovida porque o ESLint pega mas ENGANA: sai `Parsing error: ',' expected`
# apontando a linha do comentario, o que manda procurar erro de sintaxe em
# objeto/argumento -- que e onde nao esta. Aconteceu duas vezes na mesma sessao,
# a segunda depois de a lesson textual ja estar escrita: ler nao protegeu.
#
# A crase ESCAPADA (\`) e legitima e o detector a aceita -- global_v2.tsx ja a
# usa no reset para citar `typography.htmlFontSize`.
case "$FILE" in
  *.ts|*.tsx)
    STYLED_TICK="$(dirname "$0")/styled-template-backtick.py"
    if [ -f "$STYLED_TICK" ] && grep -q "styled" "$FILE"; then
      TICK_OUT=$(python3 "$STYLED_TICK" "$FILE" 2>/dev/null)
      if [ -n "$TICK_OUT" ]; then
        ERRORS="${ERRORS}
[FE-023] Crase dentro de comentario CSS de um styled-component -- ela fecha o template literal ali. O ESLint vai reportar isso como 'Parsing error' numa linha de comentario, que nao e onde esta a causa.
${TICK_OUT}"
      fi
    fi
    ;;
esac

# [FE-021] Implementacao de mock dentro da factory do `jest.mock` (CRA + resetMocks).
#
# O CRA liga `resetMocks: true`: implementacao declarada dentro da factory e
# APAGADA antes de cada teste, e o service passa a devolver `undefined`. O spec
# parece configurado e nao esta -- o componente quebra em todo lugar que consome
# aquele service, com erros sem relacao com o que se investiga.
#
# A janela (entre `jest.mock(` e o parentese que o fecha) mora em
# jest-mock-factory.py: grep simples nao distingue a factory do `beforeEach`, onde
# o MESMO texto e correto.
case "$FILE" in
  */frontend/*/src/*.spec.tsx|*/frontend/*/src/*.spec.ts)
    JEST_MOCK="$(dirname "$0")/jest-mock-factory.py"
    if [ -f "$JEST_MOCK" ]; then
      JEST_OUT=$(python3 "$JEST_MOCK" "$FILE" 2>/dev/null)
      if [ -n "$JEST_OUT" ]; then
        ERRORS="${ERRORS}
[FE-021] Implementacao de mock dentro da factory do jest.mock. O CRA liga 'resetMocks: true' e APAGA essa implementacao antes de cada teste -- o service devolve undefined e o componente quebra longe da causa. Declare 'jest.fn()' vazio na factory e implemente no beforeEach.
${JEST_OUT}"
      fi
    fi
    ;;
esac

# [FE-019] Piso de legibilidade: nenhum texto abaixo de 1.2rem.
#
# A regra supoe `:root { font-size: 62.5% }` -- 1rem = 10px --, entao 1.2rem = 12px.
# No ERP de origem, dois SPAs nasceram SEM essa base (la 1rem valia 16px) e a mesma
# string significou tamanhos diferentes em SPAs diferentes ate 2026-08-20. Todo
# frontend desta plataforma nasce com a base, ou esta regra mente. Ver FE-019.
#
# A comparacao e NUMERICA e mora em font-size-floor.py -- grep so compara texto,
# e uma lista de valores proibidos erra no primeiro valor novo que aparecer.
case "$FILE" in
  */frontend/*/src/*)
    FONT_FLOOR="$(dirname "$0")/font-size-floor.py"
    if [ -f "$FONT_FLOOR" ]; then
      FONT_OUT=$(python3 "$FONT_FLOOR" "$FILE" 2>/dev/null)
      if [ -n "$FONT_OUT" ]; then
        ERRORS="${ERRORS}
[FE-019] font-size abaixo do piso de 1.2rem (= 12px). Vocabulario desta casa: 1.6rem corpo, 1.4rem tabela/DataGrid, 1.2rem o MENOR texto legivel (helper, legenda, chip). Nao ha nada abaixo disso.
${FONT_OUT}"
      fi
    fi
    ;;
esac

# -----------------------------------------------------------------------------
# REGRAS FINANCEIRAS (spec 001, RN-11 a RN-14) — moram em financial_rules.py
# -----------------------------------------------------------------------------
# Um ponto de entrada por regra; cada um decide sozinho se o arquivo está no escopo dele (contexto
# financeiro, módulo append-only, arquivo de rotas, src/ de workspace). Exit 1 = achado. Qualquer
# OUTRO código é o hook quebrado — e hook quebrado não pode virar "passou" em silêncio (AG-019).
if [ -n "$WS_KEY" ]; then
  for FIN in "money-bigint:RN-11:dinheiro em contexto financeiro e bigint em centavos (*_cents)" \
             "ledger-immutable:RN-12:modulo append-only nao altera nem apaga registro" \
             "idempotency-required:RN-13:rota POST/PUT/PATCH exige ensureIdempotency" \
             "no-secret-in-code:RN-14:segredo literal no codigo"; do
    FIN_NAME="${FIN%%:*}"; FIN_REST="${FIN#*:}"; FIN_RN="${FIN_REST%%:*}"; FIN_DESC="${FIN_REST#*:}"
    FIN_HOOK="$(dirname "$0")/$FIN_NAME.py"
    FIN_OUT=$(python3 "$FIN_HOOK" "$FILE" 2>&1); FIN_RC=$?
    if [ "$FIN_RC" -eq 1 ]; then
      ERRORS="${ERRORS}
[$FIN_RN] $FIN_DESC ($FIN_NAME):
${FIN_OUT}"
    elif [ "$FIN_RC" -ne 0 ]; then
      ERRORS="${ERRORS}
[$FIN_RN] o hook $FIN_NAME NAO RODOU (exit $FIN_RC) — corrija o hook; arquivo nao verificado:
${FIN_OUT}"
    fi
  done
fi

# -----------------------------------------------------------------------------
# ESLINT no arquivo editado
# -----------------------------------------------------------------------------
# ⚠️ CONFIG É PRÉ-REQUISITO, NÃO SÓ O BINÁRIO. Workspace que traz o eslint
# transitivamente (react-scripts) mas não tem arquivo de configuração devolve
# "couldn't find a configuration file" — no ERP de origem o hook rejeitava TODA
# edição em dois SPAs assim, com um erro que nem apontava para a causa. Sem config,
# o passo é pulado e o `tsc` do verify.sh continua cobrindo o workspace.
HAS_ESLINT_CONFIG=""
if [ -n "$WS" ]; then
  for cfg in \
    "$WS/eslint.config.js" "$WS/eslint.config.mjs" "$WS/eslint.config.cjs" \
    "$WS/.eslintrc" "$WS/.eslintrc.js" "$WS/.eslintrc.cjs" \
    "$WS/.eslintrc.json" "$WS/.eslintrc.yml" "$WS/.eslintrc.yaml"; do
    [ -f "$cfg" ] && HAS_ESLINT_CONFIG="1" && break
  done
  # CRA e afins podem declarar a config dentro do package.json.
  if [ -z "$HAS_ESLINT_CONFIG" ] && [ -f "$WS/package.json" ] \
     && grep -q '"eslintConfig"' "$WS/package.json"; then
    HAS_ESLINT_CONFIG="1"
  fi
fi

if [ -n "$WS" ] && [ -n "$HAS_ESLINT_CONFIG" ] && [ -x "$WS/node_modules/.bin/eslint" ]; then
  # --no-warn-ignored só existe no ESLint 9+ (backend usa 10, frontend usa 8) —
  # no ESLint 8 a flag derruba o comando com "Invalid option", então detecta antes.
  ESLINT_FLAGS=""
  if (cd "$WS" && ./node_modules/.bin/eslint --help 2>/dev/null | grep -q -- '--no-warn-ignored\|--warn-ignored'); then
    ESLINT_FLAGS="--no-warn-ignored"
  fi
  # shellcheck disable=SC2086
  LINT_OUT=$(cd "$WS" && ./node_modules/.bin/eslint $ESLINT_FLAGS "$FILE" 2>&1)
  LINT_EXIT=$?
  if [ $LINT_EXIT -ne 0 ]; then
    ERRORS="${ERRORS}
--- ESLint ---
${LINT_OUT}"
  fi
fi

# -----------------------------------------------------------------------------
if [ -n "$ERRORS" ]; then
  {
    echo "❌ VERIFICAÇÃO PÓS-EDIÇÃO FALHOU em: $FILE"
    echo "Corrija os pontos abaixo ANTES de prosseguir com a próxima etapa:"
    printf '%s\n' "$ERRORS"
  } >&2
  exit 2
fi

# -----------------------------------------------------------------------------
# AVISOS (não bloqueiam) — chegam ao modelo via hookSpecificOutput.additionalContext, exit 0.
#
# [spec 085] Placeholder do scaffold (`__X__`) em LINHA DE CÓDIGO de um .ts/.tsx. O scaffold deixa
# os marcadores de bloco de propósito, em COMENTÁRIO, para o agente preencher — por isso é aviso e
# não bloqueio: se bloqueasse, preencher o segundo marcador seria impossível sem reprovar a edição
# legítima do primeiro. Marcador em comentário é o estado normal de um módulo recém-gerado e não
# avisa. Quem bloqueia placeholder vazado é o `verifier` (severidade alta).
# Filtro de comentário sobre o código (AG-013): fim de linha, linhas de continuação `*`, JSX
# `{/* */}` e a linha de abertura `/*`.
# -----------------------------------------------------------------------------
WARNINGS=""
PLACEHOLDER_HITS=$(sed -e 's|//.*||' -e 's|^[[:space:]]*\*.*||' -e 's|{/\*.*\*/}||' -e 's|/\*.*||' "$FILE" \
  | grep -nE "__[A-Za-z][A-Za-z_]*__" | head -n 10)
if [ -n "$PLACEHOLDER_HITS" ]; then
  WARNINGS="${WARNINGS}⚠️ [spec 085] placeholder do scaffold em linha de CÓDIGO de ${FILE##*/} — o módulo não está pronto até isso ser preenchido ou removido (o verifier reprova):
${PLACEHOLDER_HITS}"
fi

if [ -n "$WARNINGS" ]; then
  python3 -c "
import json, sys
print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse', 'additionalContext': sys.argv[1]}}, ensure_ascii=False))
" "$WARNINGS"
fi

exit 0
