#!/usr/bin/env bash
# =============================================================================
# Hook PreToolUse (Edit|Write) — proteção de migrations versionadas
#
# Bloqueia a edição de qualquer migration que já esteja versionada no git
# (potencialmente já executada em outros ambientes). Alteração de schema
# deve SEMPRE ser feita via NOVA migration.
#
# Migrations recém-criadas na sessão (ainda não commitadas) podem ser editadas.
# Exit 2 => bloqueia a ferramenta e devolve a explicação ao Claude.
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

# Só interessa a pasta de migrations — e não as fixtures dos hooks financeiros (spec 001), que
# imitam essa pasta dentro de .claude/scripts/tests/ e precisam continuar editáveis depois de versionadas.
case "$FILE" in
  */.claude/scripts/tests/*) exit 0 ;;
  */src/shared/infra/typeorm/migrations/*) ;;
  *) exit 0 ;;
esac

# Workspace = tudo antes de /src/shared/...
WS="${FILE%%/src/shared/*}"
REL="${FILE#"$WS"/}"

if git -C "$WS" ls-files --error-unmatch "$REL" >/dev/null 2>&1; then
  {
    echo "🛑 BLOQUEADO: '$REL' é uma migration já versionada no git (potencialmente executada em outros ambientes)."
    echo "Nunca editar migration existente. Para alterar o schema, crie uma NOVA migration (/new-migration)."
    echo "Se for uma migration criada agora mas já commitada por engano, peça ao usuário para autorizar manualmente."
  } >&2
  exit 2
fi

exit 0
