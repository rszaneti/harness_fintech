#!/usr/bin/env python3
# =============================================================================
# [FE-019] Piso de legibilidade do frontend — 1.2rem
#
# Auxiliar de `post-edit-check.sh`. Recebe UM arquivo e imprime uma linha por
# violacao; saida vazia = aprovado. Nao edita nada.
#
# Por que existe como script separado e nao como grep no hook: a regra precisa
# COMPARAR NUMEROS, e um grep so compara texto. Uma regex que tentasse listar os
# valores proibidos ('1.1rem', '1rem', '0.9rem', 11, '11px', ...) erraria por
# omissao no primeiro valor novo que alguem inventasse.
# =============================================================================
import re
import sys

# [FE-019] Piso de legibilidade: 1.2rem. Os tres SPAs rodam com
# `:root { font-size: 62.5% }` (1rem = 10px), entao 1.2rem = 12px em todos.
MIN_PX = 12.0
REM_PX = 10.0

# Palavras-chave e enums do MUI que ocupam a mesma prop sem serem tamanho.
SKIP_WORDS = {
    'small', 'medium', 'large', 'inherit', 'initial', 'unset', 'revert',
    'auto', 'smaller', 'larger', 'xx-small', 'x-small',
}

VALUE = re.compile(
    r"""font-?[sS]ize\s*[:=]\s*        # fontSize: | font-size: | fontSize=
        \{?\s*['"]?\s*                 # abre {, aspas opcionais
        (?P<num>-?\d+(?:\.\d+)?)       # o numero
        \s*(?P<unit>rem|px|em|%)?      # unidade opcional (ausente = px, no sx/style)
        \s*['"]?""",
    re.VERBOSE,
)

path = sys.argv[1]
with open(path, encoding='utf-8', errors='replace') as fh:
    lines = fh.readlines()

bad = []
for n, raw in enumerate(lines, 1):
    # Linha de comentario nao dispara a regra -- assim a lesson e os templates
    # podem MOSTRAR o valor proibido sem serem reprovados por isso.
    if re.match(r'^\s*(//|\*|/\*|#)', raw):
        continue
    for m in VALUE.finditer(raw):
        unit = m.group('unit')
        if unit in ('em', '%'):
            continue  # relativo ao pai: nao da para decidir estaticamente
        px = float(m.group('num')) * (REM_PX if unit == 'rem' else 1.0)
        if px < MIN_PX:
            shown = m.group('num') + (unit or '')
            bad.append('  linha %d: %s  (= %.4gpx)' % (n, shown, px))

if bad:
    print('\n'.join(bad))
